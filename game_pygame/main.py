import pygame
import sys
import random
import math

from base import *

pygame.init()

# Получаем размер экрана
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Создаем полноэкранное окно
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

WORLD_WIDTH = screen_width + 2000
WORLD_HEIGHT = screen_height + 2000
pygame.display.set_caption("Shadow of the Blight")

clock = pygame.time.Clock()


class Location:
    """Хранит все данные одной локации: фон, здания, границы камеры, спавн игрока"""

    def __init__(self, name, background_path, house_data, camera_bounds, player_spawn, background_size=None):
        self.name = name
        self.background_path = background_path
        self.house_data = house_data  # список словарей {'rect': ..., 'image': ...}
        self.camera_bounds = camera_bounds  # (min_x, max_x, min_y, max_y)
        self.player_spawn = player_spawn  # (x, y) мировые координаты

        # Загружаем фон один раз при создании
        self.background = pygame.image.load(background_path)
        if background_size is None:
            background_size = (WORLD_WIDTH, WORLD_HEIGHT)
        self.background = pygame.transform.scale(self.background, background_size)

        # Создаём rect'ы для зданий
        self.house = []
        for data in house_data:
            self.house.append({
                'rect': data['rect'].copy(),  # копируем, чтобы не менять оригинал
                'image': data['image']
            })

class Camera:
    def __init__(self, camera_x, camera_y, screen_width, screen_height):
        self.camera_x = camera_x
        self.camera_y = camera_y
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.step_cord = 1

    def set_bounds(self, min_x, max_x, min_y, max_y):
        """Устанавливает новые границы для камеры"""
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # камера вправо
        if (mouse_pos[0] >= self.screen_width - 2 or keys[pygame.K_RIGHT]) and self.camera_x >= self.min_x:
            self.camera_x -= self.step_cord
        # камера влево
        if (mouse_pos[0] <= 2 or keys[pygame.K_LEFT]) and self.camera_x <= self.max_x:
            self.camera_x += self.step_cord
        # камера вниз
        if (mouse_pos[1] >= self.screen_height - 2 or keys[pygame.K_DOWN]) and self.camera_y >= self.min_y:
            self.camera_y -= self.step_cord
        # камера вверх
        if (mouse_pos[1] <= 2 or keys[pygame.K_UP]) and self.camera_y <= self.max_y:
            self.camera_y += self.step_cord

        return [self.camera_x, self.camera_y]

class Player:
    def __init__(self, x, y, camera, menu):
        # Мировые координаты
        self.world_x = x
        self.world_y = y
        self.speed = 3
        self.moving = False

        self.inventory = []

        self.menu = menu

        self.hp = 100
        self.attack = 60
        self.crit_attack = 0

        self.camera = camera
        self.hp_bar = hp_bar

        self.is_picking_up = False
        self.is_fishing = False

        self.sprites = {}
        for direction in ['up', 'down', 'left', 'right']:
            frames = []
            frame_id = 1
            while True:
                try:
                    frame = pygame.image.load(f"anim/character/{direction}/{frame_id}.png")
                    new_width = int(frame.get_width() * 0.75)
                    new_height = int(frame.get_height() * 0.75)
                    frame = pygame.transform.scale(frame, (new_width, new_height))
                    frames.append(frame)
                    frame_id += 1
                except FileNotFoundError:
                    break
            if frames:
                self.sprites[direction] = frames
        # Текущее состояние анимации
        self.direction = 'down'  # направление по умолчанию
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.08  # секунд на кадр (меньше = быстрее)

        # Хитбокс
        if self.sprites:
            first_sprite = next(iter(self.sprites.values()))[0]
            self.rect = first_sprite.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 32, 32)  # фолбэк

        # Эффект клика
        self.click_frames = []
        for i in range(1, 9):
            try:
                frame = pygame.image.load(f"anim/click/{i}.png")
                self.click_frames.append(frame)
            except FileNotFoundError:
                break

        self.click_effects = []

        self.last_damage_time = 0  # время последнего полученного урона
        self.damage_cooldown = 1000  # кулдаун в миллисекундах (1000 = 1 секунда)
        self.is_invulnerable = False  # флаг неуязвимости (для эффекта мигания)

    def add_to_inventory(self, object):
        self.inventory.append(object)

    def take_damage(self, amount):
        """Получить урон с учётом кулдауна. Возвращает True, если урон применён."""
        now = pygame.time.get_ticks()
        if now - self.last_damage_time < self.damage_cooldown:
            return False  # ещё неуязвим

        self.hp -= amount
        self.last_damage_time = now
        self.is_invulnerable = True
        return True

    def update_invulnerability(self):
        """Обновляет состояние неуязвимости (вызывать каждый кадр)"""
        now = pygame.time.get_ticks()
        if self.is_invulnerable and now - self.last_damage_time >= self.damage_cooldown:
            self.is_invulnerable = False

    def health(self):
        if self.hp > 0:
            rounded_hp = max(0, (self.hp // 20) * 20)
            img = pygame.image.load(hp_bar[rounded_hp])
            img = pygame.transform.scale(img, (int(img.get_width() * 0.75), int(img.get_height() * 0.75)))
            screen.blit(img, (1340, 40))
        else:
            self.menu.status = False

    def add_click_effect(self, x, y):
        self.click_effects.append({
            'x': x, 'y': y, 'current_frame': 0,
            'playing': True, 'animation_timer': 0, 'animation_speed': 0.06
        })

    def update_click_effects(self, dt):
        for effect in self.click_effects[:]:
            effect['animation_timer'] += dt
            if effect['animation_timer'] >= effect['animation_speed']:
                effect['animation_timer'] = 0
                effect['current_frame'] += 1
                if effect['current_frame'] >= len(self.click_frames):
                    self.click_effects.remove(effect)

    def draw_click_effects(self, screen):
        for effect in self.click_effects:
            if effect['playing'] and effect['current_frame'] < len(self.click_frames):
                screen.blit(self.click_frames[effect['current_frame']], (effect['x'], effect['y']))

    def _get_direction(self, dx, dy):
        """Определяет направление движения по вектору"""
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'down' if dy > 0 else 'up'

    def _update_animation(self, dt, is_moving):
        """Обновляет кадр анимации с защитой от выхода за границы"""
        if is_moving and self.direction in self.sprites and self.sprites[self.direction]:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                frames_count = len(self.sprites[self.direction])
                self.current_frame = (self.current_frame + 1) % frames_count
        elif not is_moving:
            # При остановке сбрасываем на первый кадр, но только если спрайты есть
            if self.direction in self.sprites and self.sprites[self.direction]:
                self.current_frame = 0

    def move(self, buildings, dt):
        self.update_click_effects(dt)

        if not self.moving:
            self._update_animation(dt, is_moving=False)
            return

        clicked_on_building = False
        for build in buildings:
            hitbox = build['rect'].inflate(-60, -60)
            if hitbox.collidepoint(self.target_x, self.target_y):
                clicked_on_building = True
                break

        if clicked_on_building:
            closest_building = None
            min_distance = float('inf')
            for build in buildings:
                hitbox = build['rect'].inflate(-60, -60)
                if hitbox.collidepoint(self.target_x, self.target_y):
                    building_center_x = hitbox.centerx
                    building_center_y = hitbox.centery
                    dist = ((building_center_x - self.world_x) ** 2 + (building_center_y - self.world_y) ** 2) ** 0.5
                    if dist < min_distance:
                        min_distance = dist
                        closest_building = hitbox

            if closest_building:
                dx_to_building = closest_building.centerx - self.world_x
                dy_to_building = closest_building.centery - self.world_y
                distance_to_building = (dx_to_building ** 2 + dy_to_building ** 2) ** 0.5
                if distance_to_building > 0:
                    self.target_x = self.world_x + (dx_to_building / distance_to_building) * (distance_to_building - 50)
                    self.target_y = self.world_y + (dy_to_building / distance_to_building) * (distance_to_building - 50)
            clicked_on_building = False

        dx = self.target_x - self.world_x
        dy = self.target_y - self.world_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance < self.speed:
            self.world_x = self.target_x
            self.world_y = self.target_y
            self.moving = False
            self._update_animation(dt, is_moving=False)
            return

        step_x = (dx / distance) * self.speed
        step_y = (dy / distance) * self.speed


        self.direction = self._get_direction(dx, dy)

        new_x = self.world_x + step_x
        new_y = self.world_y + step_y
        temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)

        for build in buildings:
            hitbox = build['rect'].inflate(-40, -40)
            if temp_rect.colliderect(hitbox):
                self.moving = False
                self._update_animation(dt, is_moving=False)
                return

        self.world_x = new_x
        self.world_y = new_y

        self._update_animation(dt, is_moving=True)

    def set_target(self, x, y):
        camera_coord = self.camera.step()
        world_x = x - camera_coord[0] - 35
        world_y = y - camera_coord[1] - 30

        self.target_x = world_x
        self.target_y = world_y
        self.moving = True
        self.add_click_effect(x - 16, y)

    def draw(self, screen):
        """Рисует персонажа с учетом камеры и защитой от ошибок"""
        camera_coord = self.camera.step()
        screen_x = self.world_x + camera_coord[0]
        screen_y = self.world_y + camera_coord[1]

        self.draw_click_effects(screen)

        if self.is_fishing or self.is_picking_up:
            return

        if self.is_invulnerable:
            # Мигаем с частотой ~10 раз в секунду
            if pygame.time.get_ticks() % 200 < 100:
                return  # в этот кадр не рисуем — эффект "прозрачности"

        # 🛡Безопасное получение текущего спрайта
        if (self.direction in self.sprites and
                self.sprites[self.direction] and
                0 <= self.current_frame < len(self.sprites[self.direction])):

            current_sprite = self.sprites[self.direction][self.current_frame]
            screen.blit(current_sprite, (screen_x, screen_y))

class Menu:
    def __init__(self):
        self.status = True
        self.bliding = True

        self.start_bg = pygame.image.load('pic/menu/start_bg.jpg')
        self.start_bg = pygame.transform.scale(self.start_bg, (screen_width, screen_height))

        # Загруем кнопки (замени пути на свои)
        self.start_btn = pygame.image.load('pic/button/button_play_1.png')
        self.start_btn_pressed = pygame.image.load('pic/button/button_play_2.png')

        self.exit_btn = pygame.image.load('pic/button/button_exit_1.png')
        self.exit_btn_pressed = pygame.image.load('pic/button/button_exit_2.png')

        # Позиции кнопок
        self.start_btn_x = screen_width // 2 - self.start_btn.get_width() // 2
        self.start_btn_y = screen_height // 2 - 100

        self.exit_btn_x = screen_width // 2 - self.exit_btn.get_width() // 2
        self.exit_btn_y = screen_height // 2 + 50

        self.pause_bg = pygame.image.load('pic/menu/pause_screen.png')
        new_w = int(self.pause_bg.get_width() * 0.75)
        new_h = int(self.pause_bg.get_height() * 0.75)
        self.pause_bg = pygame.transform.scale(self.pause_bg, (new_w, new_h))
        self.pause_bg_x = screen_width // 2 - self.pause_bg.get_width() // 2
        self.pause_bg_y = screen_height // 2 - self.pause_bg.get_height() // 2

        self.saved_screen = None

        self.font = pygame.font.Font("fonts/menu_font.ttf", 42)

    def game_over(self):
        if self.bliding:
            for alpha in range(0, 256, 5):  # шаг 5 — скорость затемнения
                overlay = pygame.Surface((screen_width, screen_height))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(alpha)
                screen.blit(overlay, (0, 0))
                pygame.display.flip()
                pygame.time.delay(15)  # задержка между кадрами (мс)

        self.bliding = False

        img_gameover = pygame.image.load('pic/menu/gameover.jpg')
        img_gameover = pygame.transform.scale(img_gameover, (screen_width, screen_height))

        screen.blit(img_gameover, (0, 0))
        pygame.display.flip()

    def start_screen(self):
        """Начальный экран с кнопками Start и Exit"""
        while True:
            # Рисуем фон
            screen.blit(self.start_bg, (0, 0))

            # Получаем позицию мыши
            mouse_pos = pygame.mouse.get_pos()
            mouse_x, mouse_y = mouse_pos

            # Определяем, над какой кнопкой находится курсор
            start_hovered = (self.start_btn_x <= mouse_x <= self.start_btn_x + self.start_btn.get_width() and
                             self.start_btn_y <= mouse_y <= self.start_btn_y + self.start_btn.get_height())

            exit_hovered = (self.exit_btn_x <= mouse_x <= self.exit_btn_x + self.exit_btn.get_width() and
                            self.exit_btn_y <= mouse_y <= self.exit_btn_y + self.exit_btn.get_height())

            # Рисуем кнопки (нажатые при наведении)
            if start_hovered:
                screen.blit(self.start_btn_pressed, (self.start_btn_x, self.start_btn_y + 10))
            else:
                screen.blit(self.start_btn, (self.start_btn_x, self.start_btn_y))

            if exit_hovered:
                screen.blit(self.exit_btn_pressed, (self.exit_btn_x, self.exit_btn_y + 10))
            else:
                screen.blit(self.exit_btn, (self.exit_btn_x, self.exit_btn_y))

            pygame.display.flip()

            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_hovered:
                        return  # Выходим из start_screen, игра начинается
                    elif exit_hovered:
                        pygame.quit()
                        sys.exit()

            clock.tick(60)

    def pause(self, current_screen, inventory):
        self.saved_screen = current_screen.copy()

        while True:
            mouse_pos = pygame.mouse.get_pos()
            mouse_x, mouse_y = mouse_pos

            screen.blit(self.saved_screen, (0, 0))

            blur_surface = pygame.Surface((screen_width, screen_height))
            blur_surface.fill((0, 0, 0))
            blur_surface.set_alpha(150)
            screen.blit(blur_surface, (0, 0))

            screen.blit(self.pause_bg, (self.pause_bg_x, self.pause_bg_y))

            text_1 = self.font.render('continue', True, (155, 45, 48))
            screen.blit(text_1, (480, 330))

            text_2 = self.font.render('exit', True, (155, 45, 48))
            screen.blit(text_2, (480, 400))

            text_3 = self.font.render('inventory', True, (155, 45, 48))
            screen.blit(text_3, (480, 470))

            continue_hovered = (480 <= mouse_x <= 480 + text_1.get_width() and
                             330 <= mouse_y <= 330 + text_1.get_height())

            exit_hovered = (480 <= mouse_x <= 480 + text_2.get_width() and
                            400 <= mouse_y <= 400 + text_2.get_height())

            inventory_hovered = (480 <= mouse_x <= 480 + text_3.get_width() and
                            470 <= mouse_y <= 470 + text_3.get_height())

            # Рисуем кнопки (нажатые при наведении)
            if continue_hovered:
                text_1 = self.font.render('continue', True, (115, 30, 32))
                screen.blit(text_1, (480, 330))
            else:
                text_1 = self.font.render('continue', True, (155, 45, 48))
                screen.blit(text_1, (480, 330))

            if exit_hovered:
                text_2 = self.font.render('exit', True, (115, 30, 32))
                screen.blit(text_2, (480, 400))
            else:
                text_2 = self.font.render('exit', True, (155, 45, 48))
                screen.blit(text_2, (480, 400))

            if inventory_hovered:
                text_3 = self.font.render('inventory', True, (115, 30, 32))
                screen.blit(text_3, (480, 470))
            else:
                text_3 = self.font.render('inventory', True, (155, 45, 48))
                screen.blit(text_3, (480, 470))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if exit_hovered:
                        pygame.quit()
                        sys.exit()
                    elif continue_hovered:
                        return
                    elif inventory_hovered:
                        self.show_inventory(inventory)
            clock.tick(60)

    def show_inventory(self, inventory):
        while True:
            # Рисуем фон
            screen.blit(self.saved_screen, (0, 0))

            blur_surface = pygame.Surface((screen_width, screen_height))
            blur_surface.fill((0, 0, 0))
            blur_surface.set_alpha(150)
            screen.blit(blur_surface, (0, 0))

            # Заголовок
            title = self.font.render('Inventory', True, (255, 255, 255))
            screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))

            # Список предметов
            if not inventory:
                text = self.font.render('No items', True, (200, 200, 200))
                screen.blit(text, (screen_width // 2 - text.get_width() // 2, 200))
            else:
                item_size = 100  # размер ячейки
                padding = 20  # отступ между предметами
                start_x = screen_width // 2 - 200  # начальная позиция
                start_y = 200  # начальная Y

                col = 0
                row = 0
                max_cols = 4  # максимум 4 предмета в ряд

                for item in inventory:
                    # Вычисляем позицию
                    x = start_x + col * (item_size + padding)
                    y = start_y + row * (item_size + padding + 50)  # +50 для названия

                    # Загружаем и масштабируем картинку
                    if 'pic' in item and item['pic']:
                        item_img = pygame.image.load(item['pic'])
                        item_img = pygame.transform.scale(item_img, (item_size, item_size))
                        screen.blit(item_img, (x, y))

                    # Следующая колонка/строка
                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return  # Возвращаемся в меню паузы

            clock.tick(60)


class Enemy:
    def __init__(self, camera, enemy_base):
        self.camera = camera
        self.enemy_base = enemy_base

        self.x = 0
        self.y = 0

        self.hp = enemy_base['hp']  # здоровье врага
        self.attack = enemy_base['damage']  # атака врага

        # кадры анимации
        self.anim = []
        frame_id = 1
        while True:
            try:
                frame = pygame.image.load(f"pic/enemy/{self.enemy_base['type']}/{frame_id}.png")
                # new_w = int(frame.get_width() * 0.75)
                # new_h = int(frame.get_height() * 0.75)
                # frame = pygame.transform.scale(frame, (new_w, new_h))
                self.anim.append(frame)
                frame_id += 1
            except FileNotFoundError:
                break

        # ⚙️ Состояние анимации
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15  # секунд на кадр

        self.step = 5

        self.detection_radius = 300  # радиус обнаружения игрока
        self.speed = 2  # скорость движения к игроку
        self.is_chasing = False  # флаг: преследует ли враг игрока

    def chase_player(self, player):
        """Преследует игрока, если он в зоне видимости"""
        # Вычисляем расстояние между врагом и игроком
        dx = player.world_x - self.x
        dy = player.world_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Проверяем, находится ли игрок в зоне обнаружения
        if distance < self.detection_radius:
            self.is_chasing = True

            # Если расстояние больше 0, двигаемся к игроку
            if distance > 0:
                # Нормализуем вектор и умножаем на скорость
                step_x = (dx / distance) * self.speed
                step_y = (dy / distance) * self.speed

                self.x += step_x
                self.y += step_y
                if distance <= 30:
                    player.take_damage(20)

        else:
            self.is_chasing = False

    def random_location(self, min_x, max_x, min_y, max_y):
        self.x = random.randint(min_x, max_x)
        self.y = random.randint(min_y, max_y)

    def update_animation(self, dt):
        """Обновляет кадр анимации. Вызывать каждый кадр."""
        if not self.anim:
            return
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.anim)

    def draw(self, screen):
        if not self.anim:
            return
        camera_coord = self.camera.step()
        screen_x = self.x + camera_coord[0]
        screen_y = self.y + camera_coord[1]
        screen.blit(self.anim[self.current_frame], (screen_x, screen_y))

    def random_location(self, min_x, max_x, min_y, max_y):
        self.x = random.randint(min_x, max_x)
        self.y = random.randint(min_y, max_y)

    def move(self):
        self.x += math.sin(0.1 * self.step) * 5
        self.step += 1

class NPC:
    def __init__(self, name: str, anim: list, dialog_data: dict, camera):
        self.name = name
        self.anim = anim
        self.dialog_data = dialog_data

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.3
        self.x = 0
        self.y = 0
        self.camera = camera
        self.near_player = False
        self.is_interactive = False

        # ⚙️ Состояние диалога
        self.dialog_active = False
        self.line_idx = 0
        self.char_idx = 0
        self.last_tick = 0
        self.pause_start = None
        self.char_delay = 60       # мс на одну букву
        self.pause_delay = 3000    # мс паузы после конца строки

        self.font = pygame.font.Font("fonts/diolog.ttf", 20)


    def set_position(self, x, y):
        """Устанавливает позицию NPC"""
        self.x = x
        self.y = y

    def update_animation(self, dt):
        """Обновляет анимацию (вызывать каждый кадр)"""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.anim)

    def anim_draw(self, screen):
        """Рисует анимацию NPC"""
        camera_coord = self.camera.step()

        if self.anim:
            screen_x = self.x + camera_coord[0]
            screen_y = self.y + camera_coord[1]

            frame = self.anim[self.current_frame]
            frame_width = frame.get_width()
            frame_height = frame.get_height()

            screen.blit(frame, (screen_x, screen_y))

            # Квадрат вокруг NPC
            square_size = 100
            self.npc_square = pygame.Rect(
                screen_x + (frame_width // 2) - (square_size // 2),
                screen_y + (frame_height // 2) - (square_size // 2),
                square_size,
                square_size
            )
            #pygame.draw.rect(screen, (255, 255, 255), self.npc_square, 2)

    def start_dialog(self):
        # Загружаем и масштабируем фон
        self.dialog_image = pygame.image.load(self.dialog_data['picture'])
        self.dialog_image = pygame.transform.scale(self.dialog_image, (screen_width, screen_height))

        self.dialog_active = True
        self.is_interactive = True
        self.line_idx = 0
        self.char_idx = 0
        self.last_tick = pygame.time.get_ticks()
        self.pause_start = None

    def update_dialog(self, events):
        if not self.dialog_active:
            return

        now = pygame.time.get_ticks()
        lines = self.dialog_data['voiceline']

        # 🛡️ Сначала проверяем: закончились ли строки?
        if self.line_idx >= len(lines):
            self.close_dialog()
            return

        # 🎮 Пропуск анимации или закрытие диалога по Space
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Дорисовываем текущую строку мгновенно
                self.char_idx = len(lines[self.line_idx])
                self.pause_start = 0  # Мгновенно переходим к паузе
                return

        # 🔤 Фаза печати
        if self.char_idx < len(lines[self.line_idx]):
            if now - self.last_tick >= self.char_delay:
                self.char_idx += 1
                self.last_tick = now
        # ⏸ Фаза паузы после окончания строки
        else:
            if self.pause_start is None:
                self.pause_start = now
            elif now - self.pause_start >= self.pause_delay:
                self.line_idx += 1
                self.char_idx = 0
                self.last_tick = now
                self.pause_start = None

    def close_dialog(self):
        self.dialog_active = False
        self.is_interactive = False

    def interaction(self):
        if self.near_player and pygame.key.get_pressed()[pygame.K_e]:
            self.start_dialog()

    def draw_dialog(self, screen):
        if not self.dialog_active:
            return

        screen.blit(self.dialog_image, (0, 0))

        lines = self.dialog_data['voiceline']
        if self.line_idx >= len(lines):
            return

        # Берём только напечатанную часть текущей строки
        visible_text = lines[self.line_idx][:self.char_idx]
        if not visible_text:
            return

        # ⚙️ Фиксированная максимальная ширина в пикселях
        max_width = 900

        # 📝 Встроенный алгоритм переноса по словам
        words = visible_text.split()
        wrapped_lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                # Если одно слово длиннее max_width, разбиваем его по символам
                if self.font.size(word)[0] > max_width:
                    char_line = ""
                    for char in word:
                        test_char = char_line + char
                        if self.font.size(test_char)[0] <= max_width:
                            char_line = test_char
                        else:
                            if char_line:
                                wrapped_lines.append(char_line)
                            char_line = char
                    current_line = char_line
                else:
                    current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        # 📐 Вычисляем позицию для вертикального центрирования
        line_height = self.font.get_height()
        start_y = 670 - (len(wrapped_lines) * line_height) // 2

        # 🖼️ Отрисовка каждой строки
        for i, line in enumerate(wrapped_lines):
            text_surface = self.font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(800, start_y + i * line_height))
            screen.blit(text_surface, text_rect)

    def near(self, x, y):
        if self.npc_square and self.npc_square.collidepoint(x, y):
            self.near_player = True
            return True
        self.near_player = False
        return False

class Tips:
    def __init__(self, camera, npc=None, build=None):
        self.camera = camera
        # Загружаем два кадра для анимации
        self.image_E_1 = pygame.image.load('pic/button/button_E_1.png')
        self.image_E_1 = pygame.transform.scale(self.image_E_1, (30, 30))
        self.image_E_2 = pygame.image.load('pic/button/button_E_2.png')
        self.image_E_2 = pygame.transform.scale(self.image_E_2, (30, 30))

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.3  # скорость анимации
        self.npc = npc
        self.build = build  # 🆕 зона замка

        self.build_rect = self.build['rect']
        self.build_trigger = pygame.Rect(
            self.build_rect.centerx,
            self.build_rect.centery,
            150,
            70
        )
        self.near_build_flag = False

    def near_build(self, player_world_x, player_world_y, ofcet_x = 0, ofcet_y = 0):
        camera_coord = self.camera.step()
        player_point = pygame.Rect(player_world_x, player_world_y, 1, 1)

        self.build_trigger.x = self.build_rect.centerx + ofcet_x + camera_coord[0]
        self.build_trigger.y = self.build_rect.centery + ofcet_y + camera_coord[1]

        pygame.draw.rect(screen, (0, 255, 0), self.build_trigger, 2)

        if player_point.colliderect(self.build_trigger):
            self.near_build_flag = True
            return True
        self.near_build_flag = False
        return False

    def update_animation(self):
        """Обновляет анимацию кнопки"""
        self.animation_timer += 0.02
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % 2

    def draw_E(self, screen, near):
        if near:
            self.update_animation()

            camera_coord = self.camera.step()
            screen_x = self.npc.x + camera_coord[0] + 33
            screen_y = self.npc.y + camera_coord[1] - 23

            # Рисуем текущий кадр
            if self.current_frame == 0:
                screen.blit(self.image_E_1, (screen_x, screen_y))
            else:
                screen.blit(self.image_E_2, (screen_x, screen_y))

    def draw_E_build(self, screen):
        if self.near_build_flag and self.build_trigger:
            self.update_animation()
            screen_x = self.build_trigger.centerx
            screen_y = self.build_trigger.top - 140
            img = self.image_E_1 if self.current_frame == 0 else self.image_E_2
            screen.blit(img, (screen_x, screen_y))

class Grid:
    def __init__(self, camera, location: Location):
        self.camera = camera
        self.location = location
        self.house = location.house  # ссылка на здания из локации

    def draw(self):
        camera_coord = self.camera.step()
        screen.blit(self.location.background, (camera_coord[0], camera_coord[1]))

        for build in self.house:
            draw_rect = pygame.Rect(
                build['rect'].x + camera_coord[0],
                build['rect'].y + camera_coord[1],
                build['rect'].width,
                build['rect'].height
            )
            if build['image']:
                screen.blit(build['image'], draw_rect)
            pygame.draw.rect(screen, (255, 255, 255), draw_rect, 2)  # отладка хитбоксов

    def update_camera_bounds(self):
        """Передаёт границы камеры из текущей локации"""
        min_x, max_x, min_y, max_y = self.location.camera_bounds
        self.camera.set_bounds(min_x, max_x, min_y, max_y)

class Fishing:
    def __init__(self, camera, player):
        self.camera = camera
        self.player = player
        self.fishing_trigger = pygame.Rect(740, 1130, 150, 70)
        self.near_fishing_flag = False

        self.objects = ['рыба', 'рыба', 'старый сапог', 'ржавый ключ']

        # Состояния: 'idle', 'waiting', 'bite_window', 'result'
        self.state = 'idle'
        self.timer = 0
        self.bite_duration = 0  # сколько секунд окно активно
        self.catch_result = ""

        # Загружаем спрайт с удочкой (один кадр для всех направлений или свой набор)
        self.fishing_sprite = pygame.image.load("anim/character/is_fishing/fishing.png")
        self.fishing_sprite = pygame.transform.scale(
            self.fishing_sprite,
            (int(self.fishing_sprite.get_width() * 0.1),
             int(self.fishing_sprite.get_height() * 0.1))
        )
        # Шрифт для подсказок
        self.font = pygame.font.Font("fonts/diolog.ttf", 36)
        self.small_font = pygame.font.Font("fonts/diolog.ttf", 24)

    def player_is_near(self, player_world_x, player_world_y):
        """Проверяет, находится ли игрок в зоне рыбалки"""
        player_point = pygame.Rect(player_world_x, player_world_y, 1, 1)

        # Отладочная отрисовка зоны
        camera_coord = self.camera.step()
        draw_rect = pygame.Rect(
            self.fishing_trigger.x + camera_coord[0],
            self.fishing_trigger.y + camera_coord[1],
            self.fishing_trigger.width,
            self.fishing_trigger.height
        )
        pygame.draw.rect(screen, (0, 255, 0), draw_rect, 2)  # раскомментируй для отладки

        if player_point.colliderect(draw_rect):
            self.near_fishing_flag = True
            return True
        self.near_fishing_flag = False
        return False

    def start_fishing(self):
        """Запускает процесс рыбалки (вызывается при нажатии E)"""
        if self.state != 'idle':
            return

        self.state = 'waiting'
        self.timer = 0
        self.bite_duration = random.uniform(1.0, 5.0)  # Ждём от 2 до 5 секунд
        self.player.is_fishing = True  # Меняем спрайт игрока

    def update(self, dt, events, object, item_pickup):
        """Обновляет состояние рыбалки. Возвращает True, если рыбалка активна."""
        if self.state == 'idle':
            return False

        # --- СОСТОЯНИЕ: ОЖИДАНИЕ ПОКЛЁВКИ ---
        if self.state == 'waiting':
            self.timer += dt
            # Рисуем подсказку "Ждём..."
            text = self.font.render("ждём поклёвку...", True, (255, 255, 255))
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, 100))

            # Если время вышло — переходим в окно подсечки
            if self.timer >= self.bite_duration:
                self.state = 'bite_window'
                self.timer = 0
                self.bite_duration = random.uniform(1.0, 2.0)  # Окно от 1 до 2 секунд
            return True

        # --- СОСТОЯНИЕ: ОКНО ПОДСЕЧКИ ---
        elif self.state == 'bite_window':
            self.timer += dt
            # Рисуем подсказку "!!! КЛЮЁТ! ЖМИ ПРОБЕЛ !!!"
            text = self.font.render("!!! КЛЮЁТ! ЖМИ [ПРОБЕЛ] !!!", True, (255, 255, 0))
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, 100))

            # Проверяем нажатие пробела
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # Успел! Поймали рыбу
                    self.state = 'result'
                    self.timer = 0
                    obj = random.choice(self.objects)
                    self.catch_result = f"поймано: {obj}!"
                    if obj == 'ржавый ключ':
                        self.player.inventory.append(object)
                        item_pickup.start_pickup(object)
                    return True

            # Если время окна вышло — рыба сорвалась
            if self.timer >= self.bite_duration:
                self.state = 'result'
                self.timer = 0
                self.catch_result = "сорвалось... слишком поздно!"
            return True

        elif self.state == 'result':
            self.timer += dt
            # Рисуем результат
            color = (0, 255, 0) if "поймано" in self.catch_result else (255, 100, 100)
            text = self.font.render(self.catch_result, True, color)
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, 100))

            # Через 3 секунды возвращаемся в idle
            if self.timer >= 3.0:
                self.state = 'idle'
                self.player.is_fishing = False  # Возвращаем обычный спрайт
            return True

        return False

    def draw_fishing_sprite(self, screen):
        """Рисует персонажа с удочкой вместо обычного спрайта"""
        if self.fishing_sprite and self.player.is_fishing:
            camera_coord = self.camera.step()
            screen_x = self.player.world_x + camera_coord[0]
            screen_y = self.player.world_y + camera_coord[1]
            screen.blit(self.fishing_sprite, (screen_x, screen_y))

class ItemPickup:
    def __init__(self, camera, player):
        self.camera = camera
        self.player = player

        # Состояние анимации
        self.is_active = False
        self.timer = 0
        self.duration = 2.5  # длительность анимации в секундах

        # Спрайт персонажа при получении предмета
        self.pickup_sprite = pygame.image.load("anim/character/player_is_add.png")
        self.pickup_sprite = pygame.transform.scale(
            self.pickup_sprite,
            (int(self.pickup_sprite.get_width() * 0.1),
                int(self.pickup_sprite.get_height() * 0.1))
        )

        # Картинка предмета (ключ)
        self.item_image = ''
        self.item_start_y = 0  # начальная позиция Y
        self.item_current_y = 0  # текущая позиция Y
        self.item_rise_speed = 30  # скорость подъёма ключика (пикселей в секунду)

        # Шрифт для названия предмета
        self.font = pygame.font.Font("fonts/diolog.ttf", 28)
        self.item_name = ''

    def start_pickup(self, item_data):
        """Запускает анимацию получения предмета"""
        if self.is_active:
            return

        self.is_active = True
        self.timer = 0
        self.player.is_picking_up = True  # Блокируем движение

        # Загружаем картинку предмета
        if item_data and 'pic' in item_data and item_data['pic']:
            self.item_image = pygame.image.load(item_data['pic'])
            self.item_image = pygame.transform.scale(
                self.item_image,
                (int(self.item_image.get_width() * 0.5),
                 int(self.item_image.get_height() * 0.5))
            )

        # Название предмета
        self.item_name = item_data.get('name', 'Предмет') if item_data else 'Предмет'

        # Начальная позиция ключика (над головой игрока)
        self.item_start_y = self.player.world_y - 50
        self.item_current_y = self.item_start_y

    def update(self, dt, screen):
        """Обновляет анимацию. Возвращает True, если анимация активна."""
        if not self.is_active:
            return False

        self.timer += dt

        # Поднимаем ключик вверх
        self.item_current_y -= self.item_rise_speed * dt

        # Рисуем спрайт персонажа с анимацией получения
        camera_coord = self.camera.step()
        screen_x = self.player.world_x + camera_coord[0]
        screen_y = self.player.world_y + camera_coord[1]

        if self.pickup_sprite:
            screen.blit(self.pickup_sprite, (screen_x, screen_y))

        # Рисуем поднимающийся ключик
        if self.item_image:
            item_screen_x = screen_x + 20  # смещение по X от персонажа
            item_screen_y = self.item_current_y + camera_coord[1]
            screen.blit(self.item_image, (item_screen_x, item_screen_y))

            # Рисуем название предмета над ключиком
            text = self.font.render(self.item_name, True, (255, 255, 255))
            text_x = item_screen_x - text.get_width() // 2 + self.item_image.get_width() // 2
            text_y = item_screen_y - 30
            screen.blit(text, (text_x, text_y))

        # Завершаем анимацию через duration секунд
        if self.timer >= self.duration:
            self.is_active = False
            self.player.is_picking_up = False
            self.item_image = None

        return True

class Note(ItemPickup):
    def __init__(self, camera, player, text):
        super().__init__(camera, player)

        self.text = text
        self.font = pygame.font.Font("fonts/kom-post.ttf", 32)
        self.small_font = pygame.font.Font("fonts/diolog.ttf", 24)

        # Картинка-фон для текста
        self.image = pygame.image.load('pic/side/note_for_text.png')

        # Позиция картинки
        self.image_x = (screen_width - self.image.get_width()) // 2
        self.image_y = (screen_height - self.image.get_height()) // 2

        # Отступы для текста внутри картинки
        self.text_offset_x = 50
        self.text_offset_y = 50
        self.text_max_width = self.image.get_width() - 100

        # Цвет текста
        self.text_color = (255, 255, 255)

        # Размытие фона
        self.blur_alpha = 150

    def start_pickup(self, item_data=None):
        """Запускает показ записки"""
        if self.is_active:
            return

        self.is_active = True
        self.timer = 0
        self.player.is_picking_up = True  # Блокируем движение

    def update(self, dt, screen, events):
        """Обновляет показ записки. Возвращает True, если записка активна."""
        if not self.is_active:
            return False

        self.timer += dt

        # 1. Рисуем размытый фон (затемнение)
        blur_surface = pygame.Surface((screen_width, screen_height))
        blur_surface.fill((0, 0, 0))
        blur_surface.set_alpha(self.blur_alpha)
        screen.blit(blur_surface, (0, 0))

        # 2. Рисуем картинку-фон
        screen.blit(self.image, (self.image_x, self.image_y))

        # 3. Рисуем текст записки с переносом слов
        text_x = self.image_x + self.text_offset_x
        text_y = self.image_y + self.text_offset_y

        # Разбиваем текст на строки
        words = self.text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.font.size(test_line)[0] <= self.text_max_width - 250:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Рисуем каждую строку
        line_height = self.font.get_height() + 10
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, self.text_color)
            screen.blit(text_surface, (text_x + 100, text_y + i * line_height + 20))

        # 4. Подсказка "Нажмите пробел"
        hint_text = self.small_font.render("[ПРОБЕЛ] Закрыть", True, (200, 200, 200))
        hint_x = (screen_width - hint_text.get_width()) // 2
        hint_y = screen_height - 80
        screen.blit(hint_text, (hint_x, hint_y))

        # 5. Обрабатываем нажатие пробела
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.is_active = False
                self.player.is_picking_up = False
                return False

        return True

class Battle:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy

        self.background = pygame.image.load("pic/battle/location_castle.jpg")
        self.background = pygame.transform.scale(self.background, (screen_width, screen_height))

        # Состояния: 'player_turn', 'enemy_turn', 'animating', 'victory', 'defeat'
        self.state = 'player_turn'
        self.timer = 0
        self.animation_duration = 1.5

        # Статы игрока (берём из player)
        self.player_hp = player.hp
        self.player_max_hp = 100
        self.player_attack_power = player.attack
        self.player_crit_damage = player.crit_attack

        # Статы врага (берём из enemy)
        self.enemy_hp = enemy.hp
        self.enemy_max_hp = enemy.hp
        self.enemy_attack_power = enemy.attack

        self.message_attack = 'Сила атаки: ' + str(self.player_attack_power)
        self.message_crit = 'Крит урон: ' + str(self.player_crit_damage)

        # Визуализация
        self.dice_value = 0
        self.message = "Твой ход! Нажми [ПРОБЕЛ] для атаки"
        self.message_color = (255, 255, 255)

        self.player_battle_sprites = []
        for i in range(1, 5):
            frame = pygame.image.load(f"anim/character/attack/{i}.png")
            new_width = int(frame.get_width() * 0.75)
            new_height = int(frame.get_height() * 0.75)
            frame = pygame.transform.scale(frame, (new_width, new_height))
            self.player_battle_sprites.append(frame)

        self.enemy_scale = 4

        # Анимация игрока
        self.player_frame = 0
        self.player_anim_timer = 0
        self.player_anim_speed = 0.15

        # Анимация врага
        self.enemy_frame = 0
        self.enemy_anim_timer = 0
        self.enemy_anim_speed = 0.15

        self.font = pygame.font.Font("fonts/diolog.ttf", 32)
        self.small_font = pygame.font.Font("fonts/diolog.ttf", 24)

    def roll_dice(self):
        """Бросок кубика 1-10"""
        return random.randint(1, 10)

    def calculate_damage(self, attack, dice_value, crit_damage=0):
        """Расчёт урона: выпало 1-10, от этого зависит сила (10% - 100%)"""
        if dice_value == 10:
            # Критический удар
            crit_multiplier = 2.0 + (crit_damage / 100)
            return int(attack * crit_multiplier), True
        else:
            # Обычный удар (10% - 90% от атаки)
            return int(attack * (dice_value / 10)), False

    def player_attack(self):
        """Игрок атакует врага"""
        self.dice_value = self.roll_dice()
        damage, is_crit = self.calculate_damage(
            self.player_attack_power,
            self.dice_value,
            self.player_crit_damage
        )

        self.enemy_hp -= damage

        if is_crit:
            self.message = f"КРИТ! Выпало {self.dice_value}. Урон: {damage}"
            self.message_color = (255, 215, 0)
        else:
            self.message = f"Выпало {self.dice_value}. Урон: {damage}"
            self.message_color = (255, 255, 255)

        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            self.state = 'victory'
            self.message = "Победа! Враг повержен!"
            self.message_color = (0, 255, 0)
        else:
            self.state = 'animating'
            self.timer = 0

    def enemy_attack(self):
        """Враг атакует игрока"""
        self.dice_value = self.roll_dice()
        damage, is_crit = self.calculate_damage(self.enemy_attack_power, self.dice_value)

        self.player_hp -= damage

        if self.player_hp < 0:
            self.player_hp = 0

        self.player.hp = self.player_hp  # обновляем реальное HP

        if is_crit:
            self.message = f"Враг выбросил {self.dice_value}! КРИТ! Урон: {damage}"
            self.message_color = (255, 100, 100)
        else:
            self.message = f"Враг выбросил {self.dice_value}. Урон: {damage}"
            self.message_color = (255, 255, 255)

        if self.player_hp <= 0:
            self.state = 'defeat'
            self.message = "Поражение... Вы погибли"
            self.message_color = (255, 0, 0)
            self.timer = 0

        else:
            self.state = 'animating'
            self.timer = 0

    def update(self, events, dt):
        """Обновляет состояние боя"""
        # Обновляем анимации
        self.player_anim_timer += dt
        if self.player_anim_timer >= self.player_anim_speed:
            self.player_anim_timer = 0
            if self.player_battle_sprites:
                self.player_frame = (self.player_frame + 1) % len(self.player_battle_sprites)
                self.player_frame = min(self.player_frame, len(self.player_battle_sprites) - 1)

        self.enemy_anim_timer += dt
        if self.enemy_anim_timer >= self.enemy_anim_speed:
            self.enemy_anim_timer = 0
            if self.enemy.anim:
                self.enemy_frame = (self.enemy_frame + 1) % len(self.enemy.anim)

        if self.state in ['victory', 'defeat']:
            self.timer += dt
            if self.timer >= 3.0:
                return True
            return False

        # Обработка ввода
        if self.player.hp > 0:
            if self.state == 'player_turn':
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.player_attack()

            elif self.state == 'animating':
                self.timer += dt
                if self.timer >= self.animation_duration:
                    if self.message.startswith("Враг"):
                        self.state = 'player_turn'
                        self.message = "Твой ход! Нажми [ПРОБЕЛ] для атаки"
                        self.message_color = (255, 255, 255)
                    else:
                        self.state = 'enemy_turn'
                        self.enemy_attack()

            elif self.state == 'enemy_turn':
                self.enemy_attack()

        return False

    def draw(self, screen):
        """Отрисовывает арену боя"""
        # Фон из локации
        screen.blit(self.background, (0, 0))

        # Позиции персонажей
        player_x = screen_width // 4 - 50
        player_y = screen_height // 2 - 100
        enemy_x = screen_width * 3 // 4 - 50
        enemy_y = screen_height // 2 - 100

        if self.player_battle_sprites and 0 <= self.player_frame < len(self.player_battle_sprites):
            sprite = self.player_battle_sprites[self.player_frame]
            screen.blit(sprite, (player_x, player_y))

        if self.enemy.anim and 0 <= self.enemy_frame < len(self.enemy.anim):
            enemy_sprite = self.enemy.anim[self.enemy_frame]
            # Масштабируем врага
            new_width = int(enemy_sprite.get_width() * self.enemy_scale)
            new_height = int(enemy_sprite.get_height() * self.enemy_scale)
            scaled_sprite = pygame.transform.scale(enemy_sprite, (new_width, new_height))
            # Центрируем увеличенного врага
            offset_x = (new_width - enemy_sprite.get_width()) // 2
            offset_y = (new_height - enemy_sprite.get_height()) // 2
            screen.blit(scaled_sprite, (enemy_x - offset_x, enemy_y - offset_y + 100))

        # Полоски HP
        self._draw_hp_bar(screen, 100, 100, self.player_hp, self.player_max_hp, "Игрок")
        self._draw_hp_bar(screen, screen_width - 350, 100, self.enemy_hp, self.enemy_max_hp, "Враг")

        #статы
        text_1 = self.font.render(self.message_attack, True, self.message_color)
        screen.blit(text_1, (100, 160))

        text_2 = self.font.render(self.message_crit, True, self.message_color)
        screen.blit(text_2, (100, 200))

        # Сообщение
        text = self.font.render(self.message, True, self.message_color)
        screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height - 150))

        # Кубик
        if self.dice_value > 0:
            dice_text = self.small_font.render(f"{self.dice_value}", True, (255, 255, 0))
            screen.blit(dice_text, (screen_width // 2 - dice_text.get_width() // 2, screen_height - 100))

    def _draw_hp_bar(self, screen, x, y, current_hp, max_hp, name):
        """Отрисовка полоски HP"""
        bar_width = 250
        bar_height = 30

        pygame.draw.rect(screen, (50, 50, 50), (x, y, bar_width, bar_height))

        fill_width = int((current_hp / max_hp) * bar_width)
        color = (0, 255, 0) if current_hp > max_hp * 0.5 else (255, 255, 0) if current_hp > max_hp * 0.25 else (255, 0,
                                                                                                                0)
        pygame.draw.rect(screen, color, (x, y, fill_width, bar_height))

        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)

        hp_text = self.small_font.render(f"{name}: {current_hp}/{max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (x, y - 30))

class Game:
    def __init__(self):
        #Данные первой локации
        location1_house = [
            {'rect': pygame.Rect(750, 100, 300, 400), 'image': pygame.image.load("pic/house/castle.png")},
            {'rect': pygame.Rect(1250, 330, 200, 200), 'image': pygame.image.load("pic/house/house_start.png")},

            {'rect': pygame.Rect(0, 0, screen_width + 1000, 150), 'image': None},
            {'rect': pygame.Rect(0, screen_height + 400, screen_width + 1000, 150), 'image': None},
            {'rect': pygame.Rect(0, 0, 240, screen_height + 1000), 'image': None},
            {'rect': pygame.Rect(1865, 316, 130, 213), 'image': None},
            {'rect': pygame.Rect(1615, 460, 178, 60), 'image': None},
            {'rect': pygame.Rect(720, 805, 220, 165), 'image': None},
            {'rect': pygame.Rect(2020, 930, 90, 103), 'image': None},
            {'rect': pygame.Rect(1100, 430, 90, 90), 'image': None},  # зона NPC
        ]

        self.location1 = Location(
            name="village",
            background_path="pic/bg_2.jpg",
            house_data=location1_house,
            camera_bounds=(-710, -5, -420, -5),
            player_spawn=(2050, 600)
        )

        #Данные подземелья
        location2_house = [
            {'rect': pygame.Rect(500, 400, 100, 160), 'image': pygame.image.load("pic/house/statue.png")},
            {'rect': pygame.Rect(0, 0, screen_width + 2000, 170), 'image': None},  # верхняя граница
            {'rect': pygame.Rect(0, screen_height + 300, 740, 150), 'image': None}, # нижняя граница
            {'rect': pygame.Rect(840, screen_height + 300, screen_width + 520, 150), 'image': None},  # нижняя граница
            {'rect': pygame.Rect(740, screen_height + 350, 100, 150), 'image': None},  # нижняя граница
            {'rect': pygame.Rect(0, 0, 240, screen_height + 1000), 'image': None}, # левая
            {'rect': pygame.Rect(screen_width + 530, 0, 240, screen_height + 1000), 'image': None}, # правая
        ]

        self.location2 = Location(
            name="castle",
            background_path="pic/bg_21.jpg",  # новый фон
            house_data=location2_house,
            camera_bounds=(-710, -5, -420, -5),
            player_spawn=(800, 400)  # где появится игрок в замке
        )

        location3_house = [
            {'rect': pygame.Rect(0, 440, screen_width + 2000, 170), 'image': None},  # верхняя граница
            {'rect': pygame.Rect(0, 848, 1010, 150), 'image': None},  # нижняя граница
            {'rect': pygame.Rect(1080, 848, screen_width + 520, 150), 'image': None},  # нижняя граница
            {'rect': pygame.Rect(390, 0, 240, screen_height + 1000), 'image': None},  # левая
            {'rect': pygame.Rect(1250, 0, 240, screen_height + 1000), 'image': None},  # правая
            {'rect': pygame.Rect(1010, 920, 70, 30), 'image': None}, #выход
            {'rect': pygame.Rect(905, 550, 130, 60), 'image': None},  # камин
            {'rect': pygame.Rect(1130, 695, 120, 65), 'image': None}, # перегородка рядом с кроватью
            {'rect': pygame.Rect(1185, 760, 70, 85), 'image': None} #кровать
        ]

        self.location3 = Location(
            name="house",
            background_path="pic/bg_3.jpg",
            house_data=location3_house,
            camera_bounds=(-100, -1005, -100, -1005),
            player_spawn=(1030, 840),
            background_size=(screen_width + 900, screen_height + 1000)  # размер фона под дом
        )

        self.camera = Camera(-700, -200, screen_width, screen_height)
        self.menu = Menu()
        self.current_location = self.location1
        self.grid = Grid(self.camera, self.current_location)
        self.grid.update_camera_bounds()  # применяем границы

        #предметы
        self.key_from_river = {'name': 'Ржавый ключ из канализации',
                               'pic': 'pic/objects/key_from_river.png'}
        self.key_from_fireplace = {'name': 'Грязный ключ из камина',
                               'pic': 'pic/objects/key_from_fireplace.png'}
        self.note_from_bed = {'name': 'Странная записка',
                              'pic': 'pic/objects/note.png'}

        pygame.mixer.music.load('music/INEKT_-_KYRR_first.mp3')
        pygame.mixer.music.set_volume(0.3)  # громкость от 0.0 до 1.0
        pygame.mixer.music.play(-1)

        self.running = True
        self.player = Player(self.current_location.player_spawn[0],
                             self.current_location.player_spawn[1],
                             self.camera, self.menu)
        self.last_time = pygame.time.get_ticks()

        # NPC только для первой локации
        self.npc = NPC("Торговец", npc_frames, first_npc, self.camera)
        self.npc.set_position(1100, 430)

        self.tips = Tips(self.camera, self.npc, location1_house[0])
        self.tips_for_statue = Tips(self.camera, self.npc, location2_house[0])
        self.tips_for_river = Tips(self.camera, self.npc, location2_house[2])
        self.tips_for_house = Tips(self.camera, self.npc, location1_house[1])
        self.tips_for_from_house = Tips(self.camera, self.npc, location3_house[5])
        self.tips_for_fireplace = Tips(self.camera, self.npc, location3_house[6])
        self.tips_for_bed = Tips(self.camera, self.npc, location3_house[8])

        self.fishing = Fishing(self.camera, self.player)
        self.item_pickup = ItemPickup(self.camera, self.player)

        self.note = Note(self.camera, self.player,text_for_note)
        self.pending_note = None

        #создаём врага и один раз задаём ему случайную позицию
        self.enemy_1 = Enemy(self.camera, enemy_1)
        self.enemy_2 = Enemy(self.camera, enemy_1)

        self.enemies = [self.enemy_1, self.enemy_2]

        self.battle = None

        # Границы для спавна
        self.enemy_1.random_location(
            min_x=300, max_x=screen_width + 430,
            min_y=200, max_y=screen_height + 200
        )

        self.enemy_2.random_location(
            min_x=300, max_x=screen_width + 430,
            min_y=200, max_y=screen_height + 200
        )

    def _switch_location(self, new_location: Location):
        """Переключает локацию и переносит игрока"""
        self.current_location = new_location
        self.grid = Grid(self.camera, self.current_location)
        self.grid.update_camera_bounds()

        # Телепортируем игрока в точку спавна новой локации
        self.player.world_x, self.player.world_y = new_location.player_spawn
        self.player.moving = False
        if self.current_location == self.location3:
            self.camera.camera_x = self.camera.screen_width // 2 - self.player.world_x + 100
            self.camera.camera_y = self.camera.screen_height // 2 - self.player.world_y + 120

    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time

            events = pygame.event.get()
            mouse_pos = pygame.mouse.get_pos()

            # 👇 ПРОВЕРКА СТОЛКНОВЕНИЯ С ВРАГАМИ (только если не в бою)
            if not self.battle and self.current_location == self.location2:
                for enemy in self.enemies:
                    dist = math.hypot(self.player.world_x - enemy.x, self.player.world_y - enemy.y)
                    if dist < 50:  # расстояние столкновения
                        self.battle = Battle(self.player, enemy)
                        break

            # 👇 ЕСЛИ ИДЁТ БОЙ
            if self.battle:
                battle_over = self.battle.update(events, dt)
                self.battle.draw(screen)

                if battle_over:
                    if self.battle.state == 'victory':
                        if self.battle.enemy in self.enemies:
                            self.enemies.remove(self.battle.enemy)
                            print("Враг побеждён!")
                    elif self.battle.state == 'defeat':
                        self.player.hp = 0
                        self.menu.status = False
                        self.battle = None
                        self.menu.game_over()
                        self.running = False  # 👈 Завершаем игру
                        return  # 👈 Выходим из run()

                    self.battle = None  # завершаем бой
                pygame.display.flip()
                clock.tick(60)
                continue  # пропускаем остальную логику

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.player.set_target(mouse_pos[0], mouse_pos[1])
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.battle is None:
                        self.menu.pause(screen.copy(), self.player.inventory)

                    #Открытие замка по E
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:

                    if self.current_location == self.location1:
                        if self.tips.near_build_flag:
                            self._switch_location(self.location2)
                        elif self.tips_for_house.near_build_flag:
                            self._switch_location(self.location3)

                    elif self.current_location == self.location2:
                        if self.tips_for_statue.near_build_flag:
                            self.player.hp = 100
                        elif self.fishing.near_fishing_flag and self.fishing.state == 'idle' and self.key_from_river not in self.player.inventory:
                            self.fishing.start_fishing()

                    elif self.current_location == self.location3:
                        if self.tips_for_from_house.near_build_flag:
                            self._switch_location(self.location1)
                            self.player.world_x, self.player.world_y = (1340, 520)
                        elif self.tips_for_fireplace.near_build_flag and self.key_from_fireplace not in self.player.inventory:
                            self.player.add_to_inventory(self.key_from_fireplace)
                            self.item_pickup.start_pickup(self.key_from_fireplace)
                        elif self.tips_for_bed.near_build_flag and self.note_from_bed not in self.player.inventory:
                            self.player.add_to_inventory(self.note_from_bed)
                            self.item_pickup.start_pickup(self.note_from_bed)
                            self.pending_note = self.note

            if self.menu.status:
                #Обновляем диалог (только если есть активный NPC)
                if self.current_location == self.location1:
                    self.npc.update_dialog(events)

                if self.current_location == self.location1 and self.npc.is_interactive:
                    #Диалоговый режим
                    self.npc.draw_dialog(screen)
                else:
                    self.grid.draw()

                    block_player = False

                    #Логика для первой локации
                    if self.current_location == self.location1:
                        self.npc.update_animation(dt)
                        self.npc.anim_draw(screen)

                        #Проверка близости к NPC
                        player_screen_x = self.player.world_x + self.camera.step()[0]
                        player_screen_y = self.player.world_y + self.camera.step()[1]

                        near_npc = self.npc.near(player_screen_x, player_screen_y)
                        self.npc.interaction()
                        self.tips.draw_E(screen, near_npc)

                        #Проверка близости к замку
                        self.tips.near_build(player_screen_x, player_screen_y, -110, 200)
                        self.tips.draw_E_build(screen)
                        # Проверка близости к дому
                        self.tips_for_house.near_build(player_screen_x, player_screen_y, -80, 50)
                        self.tips_for_house.draw_E_build(screen)

                    elif self.current_location == self.location2:

                        for enemy in self.enemies:
                            enemy.update_animation(dt)
                            enemy.chase_player(self.player)

                        # Если не преследует
                            if not enemy.is_chasing:
                                enemy.move()

                            enemy.draw(screen)

                        player_screen_x = self.player.world_x + self.camera.step()[0]
                        player_screen_y = self.player.world_y + self.camera.step()[1]

                        if self.key_from_river not in self.player.inventory:
                            self.tips_for_river.near_build(player_screen_x, player_screen_y, 310, -130)
                            self.tips_for_river.draw_E_build(screen)

                        self.tips_for_statue.near_build(player_screen_x, player_screen_y, -85, 40)
                        self.fishing.player_is_near(player_screen_x, player_screen_y)
                        self.tips_for_statue.draw_E_build(screen)


                        is_fishing_active = self.fishing.update(dt, events, self.key_from_river, self.item_pickup)
                        if is_fishing_active:
                            self.fishing.draw_fishing_sprite(screen)
                            block_player = True

                        is_picking_up = self.item_pickup.update(dt, screen)
                        if is_picking_up:
                            block_player = True

                    elif self.current_location == self.location3:

                        player_screen_x = self.player.world_x + self.camera.step()[0]
                        player_screen_y = self.player.world_y + self.camera.step()[1]

                        self.tips_for_from_house.near_build(player_screen_x, player_screen_y, -60, -110)
                        self.tips_for_from_house.draw_E_build(screen)

                        if self.key_from_fireplace not in self.player.inventory:
                            self.tips_for_fireplace.near_build(player_screen_x, player_screen_y, -70, 0)
                            self.tips_for_fireplace.draw_E_build(screen)
                        is_picking_up = self.item_pickup.update(dt, screen)
                        if is_picking_up:
                            block_player = True

                        if self.note_from_bed not in self.player.inventory:
                            self.tips_for_bed.near_build(player_screen_x, player_screen_y, -100, -30)
                            self.tips_for_bed.draw_E_build(screen)
                        is_picking_up_note = self.item_pickup.update(dt, screen)
                        if is_picking_up_note:
                            block_player = True

                        if not is_picking_up and self.pending_note is not None:
                            self.pending_note.start_pickup()
                            self.pending_note = None

                            # 👇 Обновление записки
                        is_note_active = self.note.update(dt, screen, events)
                        if is_note_active:
                            block_player = True

                    if not block_player:
                        self.player.move(self.grid.house, dt)
                        self.player.update_invulnerability()
                        self.player.draw(screen)
                        self.player.health()

            else:
                self.menu.game_over()

            pygame.display.flip()
            clock.tick(60)

# Запуск игры
if __name__ == "__main__":
    menu = Menu()
    menu.start_screen()
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
