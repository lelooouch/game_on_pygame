import pygame
import sys

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
        # Мировые координаты (на карте)
        self.world_x = x
        self.world_y = y
        self.speed = 3
        self.moving = False

        # Загружаем картинку человечка
        self.image = pygame.image.load("pic/2.png")
        self.rect = self.image.get_rect()

        self.camera = camera

        # Эффект клика
        self.click_frames = []
        for i in range(1, 9):
            frame = pygame.image.load(f"anim/click/{i}.png")
            self.click_frames.append(frame)

        self.click_effects = []  # Список активных эффектов

    def add_click_effect(self, x, y):
        """Добавляет эффект клика в указанных координатах"""
        self.click_effects.append({
            'x': x,
            'y': y,
            'current_frame': 0,
            'playing': True,
            'animation_timer': 0,
            'animation_speed': 0.06
        })

    def update_click_effects(self, dt):
        """Обновляет все эффекты клика"""
        for effect in self.click_effects[:]:
            effect['animation_timer'] += dt
            if effect['animation_timer'] >= effect['animation_speed']:
                effect['animation_timer'] = 0
                effect['current_frame'] += 1
                if effect['current_frame'] >= len(self.click_frames):
                    self.click_effects.remove(effect)

    def draw_click_effects(self, screen):
        """Рисует все эффекты клика"""
        for effect in self.click_effects:
            if effect['playing'] and effect['current_frame'] < len(self.click_frames):
                screen.blit(self.click_frames[effect['current_frame']], (effect['x'], effect['y']))

    def move(self, buildings, dt):
        self.update_click_effects(dt)

        """Движение к цели с проверкой столкновения со зданиями"""
        if not self.moving:
            return

        # Проверяем, не кликнули ли на здание
        for build in buildings:
            # Уменьшаем хитбокс прямо в проверке (на 40 пикселей)
            hitbox = build['rect'].inflate(-40, -40)
            if hitbox.collidepoint(self.target_x, self.target_y):
                self.moving = False
                return

        dx = self.target_x - self.world_x
        dy = self.target_y - self.world_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance < self.speed:
            self.world_x = self.target_x
            self.world_y = self.target_y
            self.moving = False
            return

        step_x = (dx / distance) * self.speed
        step_y = (dy / distance) * self.speed

        new_x = self.world_x + step_x
        new_y = self.world_y + step_y

        temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)

        # Проверяем столкновение с уменьшенным хитбоксом
        for build in buildings:
            hitbox = build['rect'].inflate(-40, -40)
            if temp_rect.colliderect(hitbox):
                self.moving = False
                return

        self.world_x = new_x
        self.world_y = new_y

    def set_target(self, x, y):
        """Устанавливает цель для движения (экранные координаты)"""
        camera_coord = self.camera.step()
        # Переводим экранные координаты в мировые
        world_x = x - camera_coord[0] - 35
        world_y = y - camera_coord[1] - 30

        self.target_x = world_x
        self.target_y = world_y
        self.moving = True

        self.add_click_effect(x - 16, y)


    def draw(self, screen):
        """Рисует персонажа с учетом камеры"""
        camera_coord = self.camera.step()

        screen_x = self.world_x + camera_coord[0]
        screen_y = self.world_y + camera_coord[1]

        self.draw_click_effects(screen)

        self.rect.topleft = (screen_x, screen_y)
        screen.blit(self.image, self.rect)


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
                'visible': False,  # Невидимый прямоугольник (рисуется только при наведении)
                'image': image1
            }
        )

        image2 = pygame.image.load("pic/house/house_start.png")
        rect = image2.get_rect()
        rect.topleft = (1250, 330)

        self.house.append(
            {
                'rect': rect,
                'visible': False,  # Невидимый прямоугольник (рисуется только при наведении)
                'image': image2
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

            screen.blit(build['image'], self.draw_rect)
            pygame.draw.rect(screen, (255, 255, 255), self.draw_rect, 2)


class Game:
    def __init__(self):
        self.camera = Camera(-300, -300, screen_width, screen_height)
        self.grid = Grid(self.camera)
        self.running = True
        self.player = Player(2050, 600, self.camera)
        self.last_time = pygame.time.get_ticks()


    def run(self):
        while self.running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0
            self.last_time = current_time

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        # Получаем мировые координаты (экранные)
                        self.player.set_target(mouse_pos[0], mouse_pos[1])
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False


            self.grid.draw()
            self.player.move(self.grid.house, dt)
            self.player.draw(screen)


            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
