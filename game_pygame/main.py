import pygame
import sys

pygame.init()



# Получаем размер экрана
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Создаем полноэкранное окно
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Полноэкранный режим")

# установка фона
background = pygame.image.load("pic/bg_2.jpg")  # Укажите путь к файлу
background = pygame.transform.scale(background, (screen_width + 2000, screen_height + 2000))

clock = pygame.time.Clock()


class Player:
    def __init__(self, x, y):
        # Мировые координаты (на карте)
        self.world_x = x
        self.world_y = y
        self.speed = 3
        self.moving = False

        # Загружаем картинку человечка
        self.image = pygame.image.load("pic/2.png")
        self.rect = self.image.get_rect()

    def move(self):
        """Движение к цели"""
        if self.moving:
            dx = self.target_x - self.world_x
            dy = self.target_y - self.world_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance < self.speed:
                self.world_x = self.target_x
                self.world_y = self.target_y
                self.moving = False
            else:
                self.world_x += (dx / distance) * self.speed
                self.world_y += (dy / distance) * self.speed

    def set_target(self, x, y):
        """Устанавливает цель для движения (мировые координаты)"""
        self.target_x = x - 35
        self.target_y = y - 30
        self.moving = True

    def draw(self, screen, camera_x, camera_y):
        """Рисует персонажа с учетом камеры"""
        screen_x = self.world_x + camera_x
        screen_y = self.world_y + camera_y
        self.rect.topleft = (screen_x, screen_y)
        screen.blit(self.image, self.rect)


class Grid:
    def __init__(self, step_x=3, step_y=3, screen_width=screen_width, screen_height=screen_height):
        self.house = []

        image1 = pygame.image.load("pic/house/castle.png")
        rect = image1.get_rect()
        rect.topleft = (450, -100)

        self.house.append(
            {
                'rect': rect,
                'visible': False,  # Невидимый прямоугольник (рисуется только при наведении)
                'image': image1
            }
        )

        image2 = pygame.image.load("pic/house/house_start.png")
        rect = image2.get_rect()
        rect.topleft = (950, -30)

        self.house.append(
            {
                'rect': rect,
                'visible': False,  # Невидимый прямоугольник (рисуется только при наведении)
                'image': image2
            }
        )

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.step_x = step_x
        self.step_y = step_y

        self.pos_x = -300
        self.pos_y = -300
        self.camera_x = -300  # меняем название с pos_x на camera_x
        self.camera_y = -300  # меняем название с pos_y на camera_y

    def get_camera_position(self):
        """Возвращает текущие координаты камеры"""
        return self.camera_x, self.camera_y

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # камера вправо
        if (mouse_pos[0] >= self.screen_width - 2 or keys[
            pygame.K_RIGHT]) and self.camera_x >= self.screen_width - 2250:
            self.camera_x -= self.step_x
            for build in self.house:
                rect = pygame.Rect(build['rect'].x - self.step_x, build['rect'].y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера вниз
        if (mouse_pos[1] >= self.screen_height - 2 or keys[pygame.K_DOWN]) and self.camera_y >= self.screen_height - 1400:
            self.camera_y -= self.step_y
            for build in self.house:
                rect = pygame.Rect(build['rect'].x, build['rect'].y - self.step_y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера влево
        if (mouse_pos[0] <= 2 or keys[pygame.K_LEFT]) and self.camera_x <= self.screen_width - 1650:
            self.camera_x += self.step_x
            for build in self.house:
                rect = pygame.Rect(build['rect'].x + self.step_x, build['rect'].y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера вверх
        if (mouse_pos[1] <= 2 or keys[pygame.K_UP]) and self.camera_y <= self.screen_height - 950:
            self.camera_y += self.step_y
            for build in self.house:
                rect = pygame.Rect(build['rect'].x, build['rect'].y + self.step_y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        screen.blit(background, (self.camera_x, self.camera_y))

    def draw(self):
        for info in self.house:
            screen.blit(info['image'], info['rect'])
            pygame.draw.rect(screen, (255, 255, 255), info['rect'], 2)


class Game:
    def __init__(self):
        self.grid = Grid(3, 3)
        self.running = True
        self.player = Player(400, 300)

    def run(self):
        while self.running:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        # Получаем мировые координаты (экранные + камера)
                        camera_x, camera_y = self.grid.get_camera_position()
                        world_x = mouse_pos[0] - camera_x
                        world_y = mouse_pos[1] - camera_y
                        self.player.set_target(world_x, world_y)
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.grid.step()

            # Рисуем сетку
            self.grid.draw()

            self.player.move()
            # Рисуем игрока с учетом камеры
            camera_x, camera_y = self.grid.get_camera_position()
            self.player.draw(screen, camera_x, camera_y)

            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
