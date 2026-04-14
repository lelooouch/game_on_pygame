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
        self.x = x
        self.y = y
        self.speed = 5

        # Загружаем картинку человечка
        self.image = pygame.image.load("pic/2.png")  # путь к вашей картинке
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def move(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        if self.target_x != self.x and self.target_y != self.y:
            if self.x < self.target_x:
                self.x += self.speed
                if self.x > self.target_x:
                    self.x = self.target_x
            elif self.x > self.target_x:
                self.x -= self.speed
                if self.x < self.target_x:
                    self.x = self.target_x

            if self.y < self.target_y:
                self.y += self.speed
                if self.y > self.target_y:
                    self.y = self.target_y
            elif self.y > self.target_y:
                self.y -= self.speed
                if self.y < self.target_y:
                    self.y = self.target_y

            # Обновляем позицию rect
            self.rect.topleft = (self.x, self.y)


    def run(self):
        screen.blit(self.image, self.rect)


class Grid:
    # КЛАСС СОЗДАНИЯ ПОЛЯ

    def __init__(self, step_x = 3, step_y = 3, screen_width = screen_width, screen_height = screen_height):

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

    def draw(self):
        for info in self.house:
            screen.blit(info['image'], info['rect'])
            pygame.draw.rect(screen, (255, 255, 255), info['rect'], 2)

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # камера вправо
        if (mouse_pos[0] >= self.screen_width - 2 or keys[pygame.K_RIGHT]) and self.pos_x >= self.screen_width - 2250:
            self.pos_x -= self.step_x
            for build in self.house:
                rect = pygame.Rect(build['rect'].x - self.step_x, build['rect'].y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера вниз
        if (mouse_pos[1] >= self.screen_height - 2 or keys[pygame.K_DOWN]) and self.pos_y >= self.screen_height - 1400:
            self.pos_y -= self.step_y
            for build in self.house:
                rect = pygame.Rect(build['rect'].x, build['rect'].y - self.step_y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера влево
        if (mouse_pos[0] <= 2 or keys[pygame.K_LEFT]) and self.pos_x <= self.screen_width - 1650:
            self.pos_x += self.step_x
            for build in self.house:
                rect = pygame.Rect(build['rect'].x + self.step_x, build['rect'].y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        # камера вверх
        if (mouse_pos[1] <= 2 or keys[pygame.K_UP]) and self.pos_y <= self.screen_height - 950:
            self.pos_y += self.step_y
            for build in self.house:
                rect = pygame.Rect(build['rect'].x, build['rect'].y + self.step_y,
                                   build['rect'].width, build['rect'].height)
                build['rect'] = rect

        screen.blit(background, (self.pos_x, self.pos_y))


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
                    mouse_pos = pygame.mouse.get_pos()
                    print(mouse_pos)
                    self.player.move(mouse_pos[0], mouse_pos[1])
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            self.grid.step()

            # Рисуем сетку
            self.grid.draw()

            self.player.run()
            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
