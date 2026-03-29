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
background = pygame.image.load("pic/bg.jpg")  # Укажите путь к файлу
background = pygame.transform.scale(background, (screen_width + 5000, screen_height + 5000))

clock = pygame.time.Clock()

class Grid:
    # КЛАСС СОЗДАНИЯ ПОЛЯ

    def __init__(self, row_i = 7, col_j = 10,
                 step_x = 3, step_y = 3, screen_width = screen_width, screen_height = screen_height):
        self.row_i = row_i
        self.col_j = col_j

        self.width = 130
        self.height = 100

        self.x_0_coord = 300
        self.y_0_coord = 220

        self.rectangles = []

        self.hovered_rect = None

        for j in range(self.col_j):
            for i in range(self.row_i):
                # Координаты прямоугольника (x, y, width, height)
                self.rect_x = self.x_0_coord + j * self.width
                self.rect_y = self.y_0_coord + i * self.height
                rect = pygame.Rect(self.rect_x, self.rect_y, self.width, self.height)
                self.rectangles.append({
                    'rect': rect,
                    'row': i,
                    'col': j,
                    'x': self.rect_x,
                    'y': self.rect_y
                })

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.step_x = step_x
        self.step_y = step_y

        self.pos_x = -500
        self.pos_y = -500

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
                pygame.draw.rect(screen, (85, 90, 47), rect_info['rect'], 3)
            else:
                # Обычный цвет контура
                pygame.draw.polygon(screen, (90, 90, 47), [
                    (rect_info['x'], rect_info['y']),
                    (rect_info['x'] + self.width, rect_info['y']),
                    (rect_info['x'] + self.width, rect_info['y'] + self.height),
                    (rect_info['x'], rect_info['y'] + self.height)
                ], 3)

    def step(self):
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] >= self.screen_width - 2:
            self.pos_x -= self.step_x
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'] - self.step_x, rect_info['y'], self.width, self.height)
                rect_info['rect'] = rect
                rect_info['x'] -= self.step_x

        if mouse_pos[1] >= self.screen_height - 2:
            self.pos_y -= self.step_y
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'], rect_info['y'] - self.step_y, self.width, self.height)
                rect_info['rect'] = rect
                rect_info['y'] -= self.step_y

        if mouse_pos[0] <= 2:
            self.pos_x += self.step_x
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'] + self.step_x, rect_info['y'], self.width, self.height)
                rect_info['rect'] = rect
                rect_info['x'] += self.step_x

        if mouse_pos[1] <= 2:
            self.pos_y += self.step_y
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'], rect_info['y'] + self.step_y, self.width, self.height)
                rect_info['rect'] = rect
                rect_info['y'] += self.step_y

        screen.blit(background, (self.pos_x, self.pos_y))


class Game:
    def __init__(self):
        self.grid = Grid(5, 7)
        self.running = True

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            #screen.fill((85, 107, 47))

            self.grid.step()

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
