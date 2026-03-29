import pygame
import sys

pygame.init()

# Получаем размер экрана
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Создаем полноэкранное окно
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Камера跟随 курсору")



clock = pygame.time.Clock()


class Grid:
    def __init__(self, row_i=7, col_j=9):
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

    def draw(self, camera_x, camera_y):
        """Рисует сетку с учетом камеры"""
        mouse_pos = pygame.mouse.get_pos()

        # Координаты мыши с учетом камеры
        world_mouse_pos = (mouse_pos[0] + camera_x, mouse_pos[1] + camera_y)

        # Проверяем, на каком прямоугольнике курсор
        current_hover = None
        for rect_info in self.rectangles:
            # Создаем прямоугольник с учетом камеры для проверки
            screen_rect = pygame.Rect(
                rect_info['x'] - camera_x,
                rect_info['y'] - camera_y,
                self.width,
                self.height
            )
            if screen_rect.collidepoint(mouse_pos):
                current_hover = rect_info
                break

        self.hovered_rect = current_hover

        # Рисуем все прямоугольники
        for rect_info in self.rectangles:
            # Координаты на экране с учетом камеры
            screen_x = rect_info['x'] - camera_x
            screen_y = rect_info['y'] - camera_y

            # Пропускаем прямоугольники за пределами экрана (оптимизация)
            if (screen_x + self.width < 0 or screen_x > screen_width or
                    screen_y + self.height < 0 or screen_y > screen_height):
                continue

            if self.hovered_rect and self.hovered_rect['rect'] == rect_info['rect']:
                # Подсвеченный прямоугольник
                pygame.draw.rect(screen, (255, 255, 100), (screen_x, screen_y, self.width, self.height))
                pygame.draw.polygon(screen, (255, 255, 255), [
                    (screen_x, screen_y),
                    (screen_x + self.width, screen_y),
                    (screen_x + self.width, screen_y + self.height),
                    (screen_x, screen_y + self.height)
                ], 3)
            else:
                # Обычный прямоугольник
                pygame.draw.polygon(screen, (85, 90, 47), [
                    (screen_x, screen_y),
                    (screen_x + self.width, screen_y),
                    (screen_x + self.width, screen_y + self.height),
                    (screen_x, screen_y + self.height)
                ], 3)


class Game:
    def __init__(self):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = clock
        self.running = True

        # Параметры камеры
        self.camera_x = 0
        self.camera_y = 0

        # Максимальные координаты камеры (зависит от размера карты)
        self.grid = Grid(row_i=7, col_j=9)

        # Вычисляем максимальные границы камеры
        max_grid_x = self.grid.x_0_coord + (self.grid.col_j - 1) * self.grid.width + self.grid.width
        max_grid_y = self.grid.y_0_coord + (self.grid.row_i - 1) * self.grid.height + self.grid.height

        self.max_camera_x = max(0, max_grid_x - self.screen_width)
        self.max_camera_y = max(0, max_grid_y - self.screen_height)

        # Настройки движения камеры
        self.camera_speed = 15
        self.edge_distance = 50  # Расстояние от края для активации движения

        self.font = pygame.font.Font(None, 36)

    def step(self):
        """Движение камеры за курсором"""
        mouse_pos = pygame.mouse.get_pos()

        # Движение вправо
        if mouse_pos[0] >= self.screen_width - self.edge_distance:
            self.camera_x += self.camera_speed
        # Движение влево
        elif mouse_pos[0] <= self.edge_distance:
            self.camera_x -= self.camera_speed

        # Движение вниз
        if mouse_pos[1] >= self.screen_height - self.edge_distance:
            self.camera_y += self.camera_speed
        # Движение вверх
        elif mouse_pos[1] <= self.edge_distance:
            self.camera_y -= self.camera_speed

        # Ограничиваем движение камеры
        self.camera_x = max(0, min(self.camera_x, self.max_camera_x))
        self.camera_y = max(0, min(self.camera_y, self.max_camera_y))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:  # Сброс камеры по пробелу
                    self.camera_x = 0
                    self.camera_y = 0

    def draw_info(self):
        """Отображает информацию"""
        info_text = f"Camera: ({self.camera_x}, {self.camera_y}) | Speed: {self.camera_speed}"
        text_surface = self.font.render(info_text, True, (255, 255, 255))
        text_bg = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10))
        text_bg.set_alpha(128)
        text_bg.fill((0, 0, 0))
        self.screen.blit(text_bg, (15, 15))
        self.screen.blit(text_surface, (20, 20))

        # Подсказка по управлению
        hint_text = "SPACE - reset camera | ESC - exit"
        hint_surface = self.font.render(hint_text, True, (200, 200, 200))
        self.screen.blit(hint_surface, (20, self.screen_height - 40))

    def run(self):
        while self.running:
            # Двигаем камеру
            self.step()

            # Обрабатываем события
            self.handle_events()

            # Отрисовка
            if background:
                # Рисуем фон с учетом камеры (если нужно)
                self.screen.blit(background, (0, 0))
            else:
                self.screen.fill((85, 107, 47))

            # Рисуем сетку с учетом камеры
            self.grid.draw(self.camera_x, self.camera_y)

            # Отображаем информацию
            self.draw_info()

            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()