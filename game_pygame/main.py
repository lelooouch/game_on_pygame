import pygame
import sys

from base import *

pygame.init()

# Получаем размер экрана
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Создаем полноэкранное окно
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Game")

clock = pygame.time.Clock()


class Camera:
    def __init__(self, camera_x, camera_y, screen_width, screen_height):
        self.camera_x = camera_x
        self.camera_y = camera_y

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.step_cord = 2

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # камера вправо
        if (mouse_pos[0] >= self.screen_width - 2 or keys[
            pygame.K_RIGHT]) and self.camera_x >= self.screen_width - 2250:
            self.camera_x -= self.step_cord

        # камера вниз
        if (mouse_pos[1] >= self.screen_height - 2 or keys[
            pygame.K_DOWN]) and self.camera_y >= self.screen_height - 1330:
            self.camera_y -= self.step_cord

        # камера влево
        if (mouse_pos[0] <= 2 or keys[pygame.K_LEFT]) and self.camera_x <= self.screen_width - 1650:
            self.camera_x += self.step_cord

        # камера вверх
        if (mouse_pos[1] <= 2 or keys[pygame.K_UP]) and self.camera_y <= self.screen_height - 950:
            self.camera_y += self.step_cord

        return [self.camera_x, self.camera_y]


class Player:
    def __init__(self, x, y, camera):
        # Мировые координаты
        self.world_x = x
        self.world_y = y
        self.speed = 3
        self.moving = False

        self.camera = camera

        # 🎭 Загрузка спрайтов для 4 направлений
        # Формат: "anim/player/{direction}/{frame}.png"
        # direction: 'up', 'down', 'left', 'right'
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

        # Хитбокс (возьмём размер из первого загруженного спрайта)
        if self.sprites:
            first_sprite = next(iter(self.sprites.values()))[0]
            self.rect = first_sprite.get_rect()
        else:
            self.rect = pygame.Rect(0, 0, 32, 32)  # фолбэк

        # Эффект клика (ваш существующий код)
        self.click_frames = []
        for i in range(1, 9):
            try:
                frame = pygame.image.load(f"anim/click/{i}.png")
                self.click_frames.append(frame)
            except FileNotFoundError:
                break

        self.click_effects = []

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

        # === Логика движения (ваша, без изменений) ===
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

        # 🎯 Определяем направление ДО перемещения
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

        # 🎬 Обновляем анимацию только если движемся
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

        # 🛡️ Безопасное получение текущего спрайта
        if (self.direction in self.sprites and
                self.sprites[self.direction] and
                0 <= self.current_frame < len(self.sprites[self.direction])):

            current_sprite = self.sprites[self.direction][self.current_frame]
            screen.blit(current_sprite, (screen_x, screen_y))
        else:
            # 🔴 Фолбэк: красный квадрат, если спрайт не найден
            # Поможет сразу увидеть проблему при отладке
            pygame.draw.rect(screen, (255, 0, 0), (screen_x, screen_y, 32, 32))
            # Для продакшена можно заменить на заглушку:
            # if self.sprites and 'down' in self.sprites and self.sprites['down']:
            #     screen.blit(self.sprites['down'][0], (screen_x, screen_y))

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
    def __init__(self, camera, npc):
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


class Grid:
    def __init__(self, camera, screen_width=screen_width, screen_height=screen_height):
        self.house = []

        # установка фона
        self.background = pygame.image.load("pic/bg_2.jpg")
        self.background = pygame.transform.scale(self.background, (screen_width + 2000, screen_height + 2000))

        image1 = pygame.image.load("pic/house/castle.png")
        rect = image1.get_rect()
        rect.topleft = (750, 100)

        self.house.append(
            {
                'rect': rect,
                'image': image1
            }
        )

        image2 = pygame.image.load("pic/house/house_start.png")
        rect = image2.get_rect()
        rect.topleft = (1250, 330)

        self.house.append(
            {
                'rect': rect,
                'image': image2
            }
        )

        rect = pygame.Rect(0, 0, screen_width + 1000, 150)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(0, screen_height + 400, screen_width + 1000, 150)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(0, 0, 240, screen_height + 1000)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(1865, 316, 130, 213) # правые руины
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(1615, 460, 178, 60)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(720, 805, 220, 165)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(2020, 930, 90, 103)
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        rect = pygame.Rect(1100, 430, 90, 90) #npc
        self.house.append(
            {
                'rect': rect,
                'image': None
            }
        )

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.camera = camera

    def draw(self):
        camera_coord = self.camera.step()
        screen.blit(self.background, (camera_coord[0], camera_coord[1]))

        for build in self.house:
            # Создаем временный rect для отрисовки, НЕ меняем оригинал
            self.draw_rect = pygame.Rect(
                build['rect'].x + camera_coord[0],
                build['rect'].y + camera_coord[1],
                build['rect'].width,
                build['rect'].height
            )

            if build['image']:
                screen.blit(build['image'], self.draw_rect)

            # pygame.draw.rect(screen, (255, 255, 255), self.draw_rect, 2) # показать хитбоксы


class Game:
    def __init__(self):
        self.camera = Camera(-700, -200, screen_width, screen_height)
        self.grid = Grid(self.camera)
        self.running = True
        self.player = Player(2050, 600, self.camera)
        self.last_time = pygame.time.get_ticks()

        self.npc = NPC("Торговец", npc_frames, first_npc, self.camera)
        self.npc.set_position(1100, 430)

        self.tips = Tips(self.camera, self.npc)
        # ... остальной код init ...

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

            # 🆕 Обновляем логику диалога КАЖДЫЙ кадр
            self.npc.update_dialog(events)

            if not self.npc.is_interactive:
                self.grid.draw()
                self.npc.update_animation(dt)
                self.npc.anim_draw(screen)
                self.player.move(self.grid.house, dt)
                self.player.draw(screen)

                player_screen_x = self.player.world_x + self.camera.step()[0]
                player_screen_y = self.player.world_y + self.camera.step()[1]
                near_npc = self.npc.near(player_screen_x, player_screen_y)
                self.npc.interaction()
                self.tips.draw_E(screen, near_npc)
            else:
                self.npc.draw_dialog(screen)

            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
