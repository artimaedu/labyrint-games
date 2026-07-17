from __future__ import annotations

import math
import random
import sys
from pathlib import Path

try:
    import pygame
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Pygame is required. Install it with:\n"
        "  python -m pip install -r requirements.txt\n"
        "or on Linux:\n"
        "  python3 -m pip install -r requirements.txt\n"
        "Then start with:\n"
        "  python main.py"
    ) from exc

from levels import LEVELS
from maze import build_path, solution
from ui import ARROW_COLORS, Button, answer_slot_rects, draw_arrow, draw_round_rect


SCREEN_SIZE = (1024, 768)
FPS = 60
ASSET_DIR = Path(__file__).parent / "assets"

BG = (167, 224, 255)
PANEL = (255, 247, 212)
CORRIDOR = (255, 236, 128)
WALL = (116, 198, 157)
GRID_LINE = (80, 171, 132)
PURPLE = (92, 69, 142)
WHITE = (255, 255, 255)


def make_asset_files():
    ASSET_DIR.mkdir(exist_ok=True)
    needed = {
        "character.png": draw_character_asset,
        "treasure.png": draw_treasure_asset,
        "background_tile.png": draw_background_asset,
        "arrow_up.png": lambda s: draw_asset_arrow(s, "U"),
        "arrow_down.png": lambda s: draw_asset_arrow(s, "D"),
        "arrow_left.png": lambda s: draw_asset_arrow(s, "L"),
        "arrow_right.png": lambda s: draw_asset_arrow(s, "R"),
    }
    for filename, drawer in needed.items():
        path = ASSET_DIR / filename
        if path.exists():
            continue
        surface = pygame.Surface((128, 128), pygame.SRCALPHA)
        drawer(surface)
        pygame.image.save(surface, path)


def draw_character_asset(surface):
    pygame.draw.circle(surface, (255, 202, 120), (64, 48), 30)
    pygame.draw.circle(surface, (61, 45, 85), (52, 43), 5)
    pygame.draw.circle(surface, (61, 45, 85), (76, 43), 5)
    pygame.draw.arc(surface, (61, 45, 85), (48, 43, 32, 26), 0.2, 2.9, 3)
    pygame.draw.circle(surface, (255, 111, 145), (64, 94), 32)
    pygame.draw.rect(surface, (91, 141, 239), (39, 74, 50, 40), border_radius=18)


def draw_treasure_asset(surface):
    pygame.draw.rect(surface, (255, 185, 64), (24, 50, 80, 50), border_radius=12)
    pygame.draw.rect(surface, (170, 105, 57), (24, 68, 80, 34), border_radius=8)
    pygame.draw.rect(surface, (255, 236, 128), (58, 62, 12, 24), border_radius=4)
    pygame.draw.arc(surface, (255, 185, 64), (24, 24, 80, 60), math.pi, 0, 12)


def draw_background_asset(surface):
    surface.fill((167, 224, 255, 0))
    for _ in range(10):
        x = random.randint(0, 127)
        y = random.randint(0, 127)
        pygame.draw.circle(surface, (255, 255, 255, 110), (x, y), random.randint(4, 10))


def draw_asset_arrow(surface, direction):
    draw_round_rect(surface, surface.get_rect().inflate(-12, -12), (255, 255, 255, 220), radius=24)
    draw_arrow(surface, surface.get_rect().inflate(-28, -28), direction)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Arrow Path to Treasure")
        self.window = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
        self.screen = pygame.Surface(SCREEN_SIZE).convert()
        self.render_rect = pygame.Rect(0, 0, *SCREEN_SIZE)
        self.render_scale = 1
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arialrounded", 32, bold=True) or pygame.font.Font(None, 32)
        self.small_font = pygame.font.SysFont("arialrounded", 24, bold=True) or pygame.font.Font(None, 24)

        make_asset_files()
        self.character = pygame.image.load(ASSET_DIR / "character.png").convert_alpha()
        self.treasure = pygame.image.load(ASSET_DIR / "treasure.png").convert_alpha()

        self.level_index = 0
        self.answer = []
        self.message = ""
        self.message_until = 0
        self.celebrating = False
        self.celebration_start = 0
        self.walk_cells = []
        self.dragging = None
        self.drag_start = None
        self.sound_on = True
        self.confetti = []
        self.load_level(0)
        self.maximize_window()

    def load_level(self, index):
        self.level_index = index % len(LEVELS)
        self.level = LEVELS[self.level_index]
        self.path_cells = build_path(self.level)
        self.correct_answer = solution(self.level)
        self.answer = []
        self.message = ""
        self.celebrating = False
        self.confetti = []

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                        continue
                    if event.key == pygame.K_ESCAPE and self.fullscreen:
                        self.toggle_fullscreen()
                        continue
                if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    continue
                self.handle_event(self.scaled_event(event))
            self.update(dt)
            self.draw()

    def maximize_window(self):
        try:
            from pygame._sdl2.video import Window

            Window.from_display_module().maximize()
        except Exception:
            pass

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
            self.maximize_window()

    def scaled_event(self, event):
        if not hasattr(event, "pos"):
            return event
        data = event.__dict__.copy()
        data["pos"] = self.to_game_pos(event.pos)
        return pygame.event.Event(event.type, data)

    def to_game_pos(self, pos):
        x = (pos[0] - self.render_rect.x) / self.render_scale
        y = (pos[1] - self.render_rect.y) / self.render_scale
        return int(x), int(y)

    def handle_event(self, event):
        if self.celebrating:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for direction, rect in self.arrow_buttons().items():
                if rect.collidepoint(pos):
                    self.dragging = direction
                    self.drag_start = pos
                    return
            if self.undo_button().rect.collidepoint(pos):
                if self.answer:
                    self.answer.pop()
                return
            if self.refresh_button().rect.collidepoint(pos):
                self.answer.clear()
                return
            if self.sound_button().rect.collidepoint(pos):
                self.sound_on = not self.sound_on
                return
            if self.go_button().rect.collidepoint(pos):
                self.check_answer()
                return
            for index, rect in enumerate(self.slot_rects()):
                if rect.collidepoint(pos) and index < len(self.answer):
                    self.answer.pop(index)
                    return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            moved = self.drag_start and distance(self.drag_start, event.pos) > 8
            if moved:
                for rect in self.slot_rects():
                    if rect.collidepoint(event.pos):
                        self.place_arrow(self.dragging)
                        break
            else:
                self.place_arrow(self.dragging)
            self.dragging = None
            self.drag_start = None

    def place_arrow(self, direction):
        if len(self.answer) >= len(self.correct_answer):
            return
        self.answer.append(direction)
        if len(self.answer) == len(self.correct_answer):
            self.check_answer()

    def check_answer(self):
        if len(self.answer) != len(self.correct_answer):
            self.flash_message("Fill the path!", 1.2)
            return
        if self.answer == self.correct_answer:
            self.start_celebration()
        else:
            self.flash_message("Try again!", 1.5)

    def flash_message(self, text, seconds):
        self.message = text
        self.message_until = pygame.time.get_ticks() + int(seconds * 1000)

    def start_celebration(self):
        self.celebrating = True
        self.celebration_start = pygame.time.get_ticks()
        self.walk_cells = list(self.path_cells)
        self.confetti = [
            [random.randint(40, SCREEN_SIZE[0] - 40), random.randint(-260, -20), random.choice(list(ARROW_COLORS.values())), random.uniform(110, 220)]
            for _ in range(130)
        ]
        self.flash_message("Great!", 2.0)

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.message and now > self.message_until:
            self.message = ""
        if self.celebrating:
            for bit in self.confetti:
                bit[1] += bit[3] * dt
            if now - self.celebration_start > 2400:
                self.load_level(self.level_index + 1)

    def maze_rect(self):
        return pygame.Rect(84, 92, 560, 430)

    def cell_size(self):
        width, height = self.level["grid"]
        rect = self.maze_rect()
        return min(rect.width // width, rect.height // height)

    def grid_origin(self):
        width, height = self.level["grid"]
        size = self.cell_size()
        rect = self.maze_rect()
        return rect.x + (rect.width - width * size) // 2, rect.y + (rect.height - height * size) // 2

    def cell_rect(self, cell):
        size = self.cell_size()
        ox, oy = self.grid_origin()
        return pygame.Rect(ox + cell[0] * size, oy + cell[1] * size, size, size)

    def cell_center(self, cell):
        return self.cell_rect(cell).center

    def slot_rects(self):
        return answer_slot_rects(len(self.correct_answer), SCREEN_SIZE[0], 564)

    def arrow_buttons(self):
        y = 658
        x = 230
        gap = 16
        size = 68
        return {
            direction: pygame.Rect(x + index * (size + gap), y, size, size)
            for index, direction in enumerate(["U", "D", "L", "R"])
        }

    def undo_button(self):
        return Button((584, 658, 68, 68), "undo", (255, 236, 128))

    def refresh_button(self):
        return Button((668, 658, 68, 68), "refresh", (255, 236, 128))

    def sound_button(self):
        return Button((894, 28, 76, 76), "sound", (255, 236, 128) if self.sound_on else (210, 210, 210))

    def go_button(self):
        return Button((756, 654, 110, 76), "go", (82, 196, 126))

    def draw(self):
        self.screen.fill(BG)
        self.draw_clouds()
        self.draw_progress()
        self.draw_maze()
        self.draw_side_panel()
        self.draw_answer_strip()
        self.draw_tray()
        self.draw_confetti()
        self.draw_message()
        self.draw_dragging()
        self.present()

    def present(self):
        window = pygame.display.get_surface()
        window_width, window_height = window.get_size()
        scale = min(window_width / SCREEN_SIZE[0], window_height / SCREEN_SIZE[1])
        scaled_size = (max(1, int(SCREEN_SIZE[0] * scale)), max(1, int(SCREEN_SIZE[1] * scale)))
        self.render_scale = scale
        self.render_rect = pygame.Rect(0, 0, *scaled_size)
        self.render_rect.center = (window_width // 2, window_height // 2)

        window.fill(BG)
        if scaled_size == SCREEN_SIZE:
            window.blit(self.screen, self.render_rect)
        else:
            window.blit(pygame.transform.smoothscale(self.screen, scaled_size), self.render_rect)
        pygame.display.flip()

    def draw_clouds(self):
        for x, y, scale in [(90, 48, 1.0), (520, 44, 0.8), (790, 132, 1.1)]:
            color = (255, 255, 255)
            pygame.draw.circle(self.screen, color, (x, y), int(28 * scale))
            pygame.draw.circle(self.screen, color, (x + int(30 * scale), y - int(8 * scale)), int(34 * scale))
            pygame.draw.circle(self.screen, color, (x + int(64 * scale), y), int(26 * scale))
            pygame.draw.rect(self.screen, color, (x, y, int(64 * scale), int(24 * scale)), border_radius=12)

    def draw_progress(self):
        for index in range(len(LEVELS)):
            x = 260 + index * 38
            y = 42
            color = (255, 185, 64) if index <= self.level_index else (255, 255, 255)
            draw_star(self.screen, (x, y), 15, color)

    def draw_maze(self):
        rect = self.maze_rect()
        draw_round_rect(self.screen, rect, PANEL, radius=32, border=6, border_color=WHITE)
        width, height = self.level["grid"]
        path_set = set(self.path_cells)

        for y in range(height):
            for x in range(width):
                cell = (x, y)
                cell_rect = self.cell_rect(cell).inflate(-4, -4)
                color = CORRIDOR if cell in path_set else WALL
                draw_round_rect(self.screen, cell_rect, color, radius=14)
                pygame.draw.rect(self.screen, GRID_LINE, cell_rect, width=2, border_radius=14)

        treasure_rect = self.cell_rect(self.path_cells[-1]).inflate(-10, -10)
        blit_fit(self.screen, self.treasure, treasure_rect)

        char_pos = self.animated_character_position()
        char_rect = pygame.Rect(0, 0, self.cell_size() - 10, self.cell_size() - 10)
        char_rect.center = char_pos
        blit_fit(self.screen, self.character, char_rect)

    def animated_character_position(self):
        if not self.celebrating:
            return self.cell_center(self.path_cells[0])
        elapsed = (pygame.time.get_ticks() - self.celebration_start) / 1000
        segment_time = 1.55 / max(1, len(self.walk_cells) - 1)
        segment = min(int(elapsed / segment_time), len(self.walk_cells) - 2)
        local = min(1, (elapsed - segment * segment_time) / segment_time)
        eased = 1 - pow(1 - local, 3)
        ax, ay = self.cell_center(self.walk_cells[segment])
        bx, by = self.cell_center(self.walk_cells[segment + 1])
        bounce = math.sin(local * math.pi) * 12
        return ax + (bx - ax) * eased, ay + (by - ay) * eased - bounce

    def draw_side_panel(self):
        panel = pygame.Rect(682, 134, 266, 360)
        draw_round_rect(self.screen, panel, (255, 247, 212), radius=32, border=6, border_color=WHITE)
        band = self.small_font.render(self.level["band"], True, PURPLE)
        self.screen.blit(band, band.get_rect(center=(panel.centerx, panel.y + 48)))

        path_label = self.small_font.render("Look at the path", True, PURPLE)
        self.screen.blit(path_label, path_label.get_rect(center=(panel.centerx, panel.y + 94)))
        for index in range(len(self.correct_answer)):
            x = panel.x + 42 + (index % 5) * 42
            y = panel.y + 132 + (index // 5) * 42
            draw_star(self.screen, (x, y), 12, (255, 185, 64))

        self.sound_button().draw(self.screen, self.font)

    def draw_answer_strip(self):
        label = self.small_font.render("Build your arrows", True, PURPLE)
        self.screen.blit(label, label.get_rect(center=(SCREEN_SIZE[0] // 2, 540)))
        for index, rect in enumerate(self.slot_rects()):
            draw_round_rect(self.screen, rect, WHITE, radius=18, border=4, border_color=(255, 236, 128))
            if index < len(self.answer):
                draw_arrow(self.screen, rect.inflate(-10, -10), self.answer[index])

    def draw_tray(self):
        for direction, rect in self.arrow_buttons().items():
            Button(rect, direction, WHITE).draw(self.screen, self.font)
        self.undo_button().draw(self.screen, self.font)
        self.refresh_button().draw(self.screen, self.font)
        self.go_button().draw(self.screen, self.font)

    def draw_confetti(self):
        if not self.celebrating:
            return
        for x, y, color, _speed in self.confetti:
            pygame.draw.rect(self.screen, color, (x, y, 9, 13), border_radius=3)

    def draw_message(self):
        if not self.message:
            return
        rect = pygame.Rect(344, 104, 336, 64) if self.celebrating else pygame.Rect(354, 514, 316, 58)
        draw_round_rect(self.screen, rect, (255, 111, 145), radius=24, border=4, border_color=WHITE)
        text = self.font.render(self.message, True, WHITE)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_dragging(self):
        if not self.dragging:
            return
        mx, my = self.to_game_pos(pygame.mouse.get_pos())
        rect = pygame.Rect(0, 0, 82, 82)
        rect.center = (mx, my)
        draw_round_rect(self.screen, rect, WHITE, radius=20, border=4, border_color=(255, 236, 128))
        draw_arrow(self.screen, rect.inflate(-14, -14), self.dragging)


def draw_star(surface, center, radius, color):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.48
        points.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (255, 255, 255), points, width=2)


def blit_fit(surface, image, rect):
    image_rect = image.get_rect()
    scale = min(rect.width / image_rect.width, rect.height / image_rect.height)
    width = max(1, int(image_rect.width * scale))
    height = max(1, int(image_rect.height * scale))
    target = pygame.Rect(0, 0, width, height)
    target.center = rect.center
    surface.blit(pygame.transform.smoothscale(image, target.size), target)


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


if __name__ == "__main__":
    Game().run()
