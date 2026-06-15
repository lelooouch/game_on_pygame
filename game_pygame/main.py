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

    def __init__(self, name, background_path, house_data, camera_bounds, player_spawn):
        self.name = name
        self.background_path = background_path
        self.house_data = house_data  # список словарей {'rect': ..., 'image': ...}
        self.camera_bounds = camera_bounds  # (min_x, max_x, min_y, max_y)
        self.player_spawn = player_spawn  # (x, y) мировые координаты

        # Загружаем фон один раз при создании
        self.background = pygame.image.load(background_path)
        self.background = pygame.transform.scale(self.background, (WORLD_WIDTH, WORLD_HEIGHT))

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
        self.step_cord = 2

        # 🆕 Границы движения камеры (по умолчанию — широкие)
        self.min_x = -3000
        self.max_x = 3000
        self.min_y = -3000
        self.max_y = 3000

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

        self.menu = menu

        self.hp = 100
        self.camera = camera
        self.hp_bar = hp_bar

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
        if self.hp >= 0:
            img = pygame.image.load(hp_bar[self.hp])
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

        if self.is_invulnerable:
            # Мигаем с частотой ~10 раз в секунду
            if pygame.time.get_ticks() % 200 < 100:
                return  # в этот кадр не рисуем — эффект "прозрачности"

        # 🛡️ Безопасное получение текущего спрайта
        if (self.direction in self.sprites and
                self.sprites[self.direction] and
                0 <= self.current_frame < len(self.sprites[self.direction])):

            current_sprite = self.sprites[self.direction][self.current_frame]
            screen.blit(current_sprite, (screen_x, screen_y))
        # else:
        #     # 🔴 Фолбэк: красный квадрат, если спрайт не найден
        #     # Поможет сразу увидеть проблему при отладке
        #     pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y, 32, 32))
        #     # Для продакшена можно заменить на заглушку:
        #     # if self.sprites and 'down' in self.sprites and self.sprites['down']:
        #     #     screen.blit(self.sprites['down'][0], (screen_x, screen_y))

class Menu:
    def __init__(self):
        self.status = True
        self.bliding = True

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

        img_easter_egg = pygame.image.load('pic/menu/pash.jpg')
        img_easter_egg = pygame.transform.scale(img_easter_egg, (screen_width, screen_height))

        screen.blit(img_gameover, (0, 0))
        pygame.display.flip()
        pygame.time.delay(3000)

        screen.blit(img_easter_egg, (0, 0))
        pygame.display.flip()
        pygame.time.delay(200)

        screen.blit(img_gameover, (0, 0))

    def pause(self):
        pass

class Enemy:
    def __init__(self, camera, enemy_base):
        self.camera = camera
        self.enemy_base = enemy_base

        self.x = 0
        self.y = 0

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

        #Данные второй локации
        location2_house = [
            {'rect': pygame.Rect(500, 400, 100, 160), 'image': pygame.image.load("pic/house/statue.png")},
            {'rect': pygame.Rect(0, 0, screen_width + 2000, 170), 'image': None},  # верхняя граница
            {'rect': pygame.Rect(0, screen_height + 300, screen_width + 1000, 150), 'image': None}, # нижняя граница
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

        self.camera = Camera(-700, -200, screen_width, screen_height)
        self.menu = Menu()
        self.current_location = self.location1
        self.grid = Grid(self.camera, self.current_location)
        self.grid.update_camera_bounds()  # применяем границы

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

        # 👇создаём врага и один раз задаём ему случайную позицию
        self.enemy_1 = Enemy(self.camera, enemy_1)
        self.enemy_2 = Enemy(self.camera, enemy_1)

        self.enemies = [self.enemy_1, self.enemy_2]

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

        print(f"🔄 Переход в локацию: {new_location.name}")

    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time

            events = pygame.event.get()
            mouse_pos = pygame.mouse.get_pos()

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.player.set_target(mouse_pos[0], mouse_pos[1])
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    # 🆕 Открытие замка по E
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    if self.current_location == self.location1 and self.tips.near_build_flag:
                        self._switch_location(self.location2)

            if self.menu.status:
                # 🗣️ Обновляем диалог (только если есть активный NPC)
                if self.current_location == self.location1:
                    self.npc.update_dialog(events)

                if self.current_location == self.location1 and self.npc.is_interactive:
                    # 🎭 Диалоговый режим
                    self.npc.draw_dialog(screen)
                else:
                    self.grid.draw()
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
                        self.tips_for_statue.near_build(player_screen_x, player_screen_y, -85, 40)
                        self.tips_for_statue.draw_E_build(screen)

                    self.player.move(self.grid.house, dt)
                    self.player.update_invulnerability()
                    self.player.draw(screen)
                    self.player.health()
                    
                pygame.display.flip()
                clock.tick(60)
            else:
                self.menu.game_over()
                pygame.display.flip()
                clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
