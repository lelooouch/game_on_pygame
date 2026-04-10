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
pygame.display.set_caption("Полноэкранный режим")

# установка фона
background = pygame.image.load("pic/bg.jpg")  # Укажите путь к файлу
background = pygame.transform.scale(background, (screen_width + 5000, screen_height + 5000))

clock = pygame.time.Clock()

class Player:
    def __init__(self, gold, woods, iron, stone):
        self.gold = gold
        self.woods = woods
        self.iron = iron
        self.stone = stone



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

        self.pos_x = -1000
        self.pos_y = -1000

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
        keys = pygame.key.get_pressed()

        # камера вправо
        if (mouse_pos[0] >= self.screen_width - 2 or keys[pygame.K_RIGHT]) and self.pos_x >= self.screen_width - 6500:
            self.pos_x -= self.step_x
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'] - self.step_x, rect_info['y'], self.width, self.height)
                rect_info['rect'] = rect
                rect_info['x'] -= self.step_x

        # камера вниз
        if (mouse_pos[1] >= self.screen_height - 2 or keys[pygame.K_DOWN]) and self.pos_y >= self.screen_height - 5800:
            self.pos_y -= self.step_y
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'], rect_info['y'] - self.step_y, self.width, self.height)
                rect_info['rect'] = rect
                rect_info['y'] -= self.step_y

        # камера влево
        if (mouse_pos[0] <= 2 or keys[pygame.K_LEFT]) and self.pos_x <= self.screen_width - 1800:
            self.pos_x += self.step_x
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'] + self.step_x, rect_info['y'], self.width, self.height)
                rect_info['rect'] = rect
                rect_info['x'] += self.step_x

        # камера вверх
        if (mouse_pos[1] <= 2 or keys[pygame.K_UP]) and self.pos_y <= self.screen_height - 1000:
            self.pos_y += self.step_y
            for rect_info in self.rectangles:
                rect = pygame.Rect(rect_info['x'], rect_info['y'] + self.step_y, self.width, self.height)
                rect_info['rect'] = rect
                rect_info['y'] += self.step_y

        screen.blit(background, (self.pos_x, self.pos_y))


class DownTab():
    # КЛАСС НИЖНЕЙ ПАНЕЛИ
    def __init__(self, width = screen_width, height = screen_height):
        self.width = width
        self.screen_height = screen_height
        self.height = height - (height // 3.5)

        self.is_open = False

        self.image_down = pygame.transform.scale(
            pygame.image.load("pic/down.png"), (50, 50))
        self.image_up = pygame.transform.scale(
            pygame.image.load("pic/up.png"), (50, 50))

        # self.h1 = pygame.transform.scale(
        #     pygame.image.load("pic/house/h1.jpg"), (180, 180))

        self.current_image = self.image_down
        self._update_image_rect()

        self.buildings = buildings

    def _update_image_rect(self):
        """Вспомогательный метод для обновления позиции картинки"""
        y_pos = self.screen_height - 50 if self.is_open else self.height + 30
        self.image_rect = self.current_image.get_rect(center=(60, y_pos))

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.image_rect.collidepoint(event.pos):
                self.is_open = not self.is_open  # Переключаем
                self.current_image = self.image_up if self.is_open else self.image_down
                self._update_image_rect()
                return True  # Событие обработано
        return False

    def draw(self):
        if self.is_open:
            panel_y = self.screen_height - 70 # панель вниз
        else:
            panel_y = self.height

        pygame.draw.rect(
            screen, (92, 90, 90),
            (0, panel_y, self.width, panel_y),  # ✅ Высота панели фиксирована
            border_radius=15
        )
        # Рисуем картинку
        screen.blit(self.current_image, self.image_rect)
        if not self.is_open:
            i = 0
            for obj in self.buildings.keys():
                h1 = pygame.transform.scale(pygame.image.load(f"pic/house/{obj}"), (180, 190))
                screen.blit(h1, (100 + i, self.height + 60)) # картика дома
                h1_rect = h1.get_rect()
                h1_rect.topleft = (100 + i, self.height + 60)
                self.buildings[obj]['position'] = h1_rect
                i += 200

    def house_check(self):
        mouse_pos = pygame.mouse.get_pos()

        # Проверяем, на какой картинке курсор и открыто ли окно с домами
        if not self.is_open:
            for info in self.buildings.keys():
                is_hovering = self.buildings[info]['position'].collidepoint(mouse_pos)
                if is_hovering:
                    text = ''
                    for par, value in self.buildings[info].items():
                        if par in ['price', 'woods', 'iron', 'stone'] and value:
                            text += f'{par.capitalize()}: {value} '

                    font = pygame.font.Font('fonts/DreiFraktur.ttf', 20)
                    text_surface = font.render(text, True, (255, 255, 255))
                    text_rect = text_surface.get_rect()

                    # Прямоугольник рядом с курсором (смещение 20 пикселей)
                    tooltip_rect = pygame.Rect(mouse_pos[0] + 20, mouse_pos[1] + 10,
                                               text_rect.width + 15, text_rect.height + 8)

                    # Рисуем фон прямоугольника
                    pygame.draw.rect(screen, (64, 64, 64), tooltip_rect, border_radius=6)

                    # Рисуем текст
                    screen.blit(text_surface, (mouse_pos[0] + 25, mouse_pos[1] + 15))




class Game:
    def __init__(self):
        self.grid = Grid(5, 7)
        self.running = True
        self.tab = DownTab()

    def run(self):
        while self.running:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                else:
                    self.tab.handle_events(event)

            self.grid.step()

            # Рисуем сетку
            self.grid.draw()

            self.tab.draw()
            self.tab.house_check()

            pygame.display.flip()
            clock.tick(60)


# Запуск игры
if __name__ == "__main__":
    game = Game()
    game.run()

    pygame.quit()
    sys.exit()
