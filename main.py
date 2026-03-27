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

# установка фона - пока не юзаем
background = pygame.image.load("setka.jpg")  # Укажите путь к файлу
background = pygame.transform.scale(background, (screen_width, screen_height))

clock = pygame.time.Clock()

class Grid:
    # КЛАСС СОЗДАНИЯ ПОЛЯ

    def __init__(self, row_i = 7, col_j = 10):
        self.row_i = row_i
        self.col_j = col_j

        self.width = 100
        self.height = 70

        self.x_0_coord = 300
        self.y_0_coord = 220

        self.rectangles = []

        self.hovered_rect = None

        for j in range(self.col_j):
            for i in range(self.row_i):
                # Координаты прямоугольника (x, y, width, height)
                rect_x = self.x_0_coord + j * self.width
                rect_y = self.y_0_coord + i * self.height
                rect = pygame.Rect(rect_x, rect_y, self.width, self.height)
                self.rectangles.append({
                    'rect': rect,
                    'row': i,
                    'col': j,
                    'x': rect_x,
                    'y': rect_y
                })

    def draw(self):

        mouse_pos = pygame.mouse.get_pos()

        # Проверяем, на каком прямоугольнике курсор
        current_hover = None
        for rect_info in self.rectangles:
            if rect_info['rect'].collidepoint(mouse_pos):
                current_hover = rect_info
                break

        # Обновляем подсвеченный прямоугольник
        self.hovered_rect = current_hover

        # Рисуем все прямоугольники
        for rect_info in self.rectangles:
            # Если это подсвеченный прямоугольник, используем другой цвет
            if self.hovered_rect and self.hovered_rect['rect'] == rect_info['rect']:
                # Рисуем залитый прямоугольник для подсветки
                pygame.draw.rect(screen, (85, 90, 47), rect_info['rect'])
            else:
                # Обычный цвет контура
                pygame.draw.polygon(screen, (90, 90, 47), [
                    (rect_info['x'], rect_info['y']),
                    (rect_info['x'] + self.width, rect_info['y']),
                    (rect_info['x'] + self.width, rect_info['y'] + self.height),
                    (rect_info['x'], rect_info['y'] + self.height)
                ], 3)


class Game:
    def __init__(self):
        self.grid = Grid(7, 9)
        self.running = True

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            screen.fill((85, 107, 47))

            # Рисуем сетку
            self.grid.draw()

            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
