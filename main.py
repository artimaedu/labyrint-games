from __future__ import annotations

import json
import math
import os
import random
import struct
import sys
import wave
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
from maze import build_path, random_path, solution
from ui import ARROW_COLORS, Button, answer_slot_rects, draw_arrow, draw_round_rect


SCREEN_SIZE = (1024, 768)
FPS = 60
SAMPLE_RATE = 44100


def resource_dir():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def data_dir():
    if not getattr(sys, "frozen", False):
        return Path(__file__).parent
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / "arrow-path-to-treasure"
    path.mkdir(parents=True, exist_ok=True)
    return path


ASSET_DIR = resource_dir() / "assets"
SCORE_FILE = data_dir() / "high_scores.json"

DIRECTION_KEYS = {
    pygame.K_UP: "U",
    pygame.K_DOWN: "D",
    pygame.K_LEFT: "L",
    pygame.K_RIGHT: "R",
}

BG = (167, 224, 255)
PANEL = (255, 247, 212)
CORRIDOR = (255, 236, 128)
WALL = (100, 175, 140)
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


def make_sound_files():
    ASSET_DIR.mkdir(exist_ok=True)
    needed = {
        "win_level.wav": level_win_samples,
        "win_all.wav": all_win_samples,
    }
    for filename, sampler in needed.items():
        path = ASSET_DIR / filename
        if path.exists():
            continue
        write_wav(path, sampler())


def tone(freq, seconds, volume=0.4):
    count = int(SAMPLE_RATE * seconds)
    samples = []
    for i in range(count):
        t = i / SAMPLE_RATE
        attack = min(1.0, t / 0.008)
        release = min(1.0, (seconds - t) / 0.03)
        envelope = attack * release * math.exp(-3.5 * t)
        value = math.sin(2 * math.pi * freq * t) + 0.35 * math.sin(4 * math.pi * freq * t)
        samples.append(value * envelope * volume)
    return samples


def chord(freqs, seconds):
    notes = [tone(freq, seconds, 0.16) for freq in freqs]
    return [sum(values) for values in zip(*notes)]


def level_win_samples():
    samples = []
    for freq in (523.25, 659.25, 783.99, 1046.50):
        samples += tone(freq, 0.15)
    return samples


def all_win_samples():
    samples = []
    for freq, seconds in (
        (392.00, 0.16),
        (523.25, 0.16),
        (659.25, 0.16),
        (783.99, 0.30),
        (659.25, 0.16),
        (783.99, 0.16),
    ):
        samples += tone(freq, seconds)
    samples += chord((523.25, 659.25, 783.99, 1046.50), 1.0)
    return samples


def write_wav(path, samples):
    frames = b"".join(
        struct.pack("<h", max(-32767, min(32767, int(sample * 32767)))) for sample in samples
    )
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(frames)


class Game:
    def __init__(self):
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Arrow Path to Treasure")
        self.window = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
        self.screen = pygame.Surface(SCREEN_SIZE).convert()
        self.render_rect = pygame.Rect(0, 0, *SCREEN_SIZE)
        self.render_scale = 1
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("arialrounded", 58, bold=True) or pygame.font.Font(None, 58)
        self.font = pygame.font.SysFont("arialrounded", 32, bold=True) or pygame.font.Font(None, 32)
        self.small_font = pygame.font.SysFont("arialrounded", 24, bold=True) or pygame.font.Font(None, 24)

        make_asset_files()
        self.character = pygame.image.load(ASSET_DIR / "character.png").convert_alpha()
        self.treasure = pygame.image.load(ASSET_DIR / "treasure.png").convert_alpha()
        self.sounds = self.load_sounds()

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
        self.state = "menu"
        self.current_player = "Player"
        self.name_input = ""
        self.completed_this_run = 0
        self.high_scores = load_high_scores()
        self.load_level(0)
        self.maximize_window()

    def load_sounds(self):
        if not pygame.mixer.get_init():
            return {}
        try:
            make_sound_files()
            return {
                "win_level": pygame.mixer.Sound(str(ASSET_DIR / "win_level.wav")),
                "win_all": pygame.mixer.Sound(str(ASSET_DIR / "win_all.wav")),
            }
        except (pygame.error, OSError):
            return {}

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound and self.sound_on:
            sound.play()

    def load_level(self, index):
        self.level_index = index % len(LEVELS)
        template = LEVELS[self.level_index]
        start, path = random_path(template["grid"], len(template["path"]))
        self.level = {**template, "start": start, "path": path}
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
        if self.state == "menu":
            self.handle_menu_event(event)
            return
        if self.state == "name":
            self.handle_name_event(event)
            return
        if self.state == "scores":
            self.handle_scores_event(event)
            return
        if self.state == "pause":
            self.handle_pause_event(event)
            return
        if self.state == "winner":
            self.handle_winner_event(event)
            return

        if self.celebrating:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "pause"
                return
            if event.key in DIRECTION_KEYS:
                self.place_arrow(DIRECTION_KEYS[event.key])
                return
            if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                if self.answer:
                    self.answer.pop()
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

    def handle_menu_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        buttons = self.menu_buttons()
        if buttons["new_game"].collidepoint(pos):
            self.start_new_game()
        elif buttons["add_player"].collidepoint(pos):
            self.name_input = "" if self.current_player == "Player" else self.current_player
            self.state = "name"
        elif buttons["high_score"].collidepoint(pos):
            self.state = "scores"
        elif buttons["exit"].collidepoint(pos):
            pygame.quit()
            sys.exit()

    def handle_name_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "menu"
                return
            if event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
                return
            if event.key == pygame.K_RETURN:
                self.save_player_name()
                return
            typed = getattr(event, "unicode", "")
            if typed and len(self.name_input) < 14:
                if typed.isalnum() or typed in " -_":
                    self.name_input += typed
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            buttons = self.name_buttons()
            if buttons["start"].collidepoint(pos):
                self.save_player_name()
            elif buttons["back"].collidepoint(pos):
                self.state = "menu"

    def handle_scores_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "menu"
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_button().collidepoint(event.pos):
                self.state = "menu"

    def handle_pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "game"
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            buttons = self.pause_buttons()
            if buttons["new_game"].collidepoint(pos):
                self.start_new_game()
            elif buttons["cancel"].collidepoint(pos):
                self.state = "game"
            elif buttons["exit"].collidepoint(pos):
                pygame.quit()
                sys.exit()

    def handle_winner_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = "menu"
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            buttons = self.winner_buttons()
            if buttons["play_again"].collidepoint(pos):
                self.start_new_game()
            elif buttons["high_score"].collidepoint(pos):
                self.state = "scores"
            elif buttons["menu"].collidepoint(pos):
                self.state = "menu"

    def save_player_name(self):
        name = self.name_input.strip() or "Player"
        self.current_player = name[:14]
        if self.current_player not in self.high_scores:
            self.high_scores[self.current_player] = 0
            save_high_scores(self.high_scores)
        self.start_new_game()

    def start_new_game(self):
        self.completed_this_run = 0
        self.load_level(0)
        self.state = "game"

    def record_score(self, score):
        name = self.current_player.strip() or "Player"
        if score > self.high_scores.get(name, 0):
            self.high_scores[name] = score
            save_high_scores(self.high_scores)

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
        self.completed_this_run = max(self.completed_this_run, self.level_index + 1)
        self.record_score(self.completed_this_run)
        self.confetti = self.make_confetti()
        self.play_sound("win_level")
        self.flash_message("Great!", 2.0)

    def make_confetti(self):
        return [
            [random.randint(40, SCREEN_SIZE[0] - 40), random.randint(-260, -20), random.choice(list(ARROW_COLORS.values())), random.uniform(110, 220)]
            for _ in range(130)
        ]

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.message and now > self.message_until:
            self.message = ""
        if self.celebrating:
            for bit in self.confetti:
                bit[1] += bit[3] * dt
            if now - self.celebration_start > 2400:
                if self.level_index + 1 >= len(LEVELS):
                    self.celebrating = False
                    self.state = "winner"
                    self.message = ""
                    self.confetti = self.make_confetti()
                    self.play_sound("win_all")
                else:
                    self.load_level(self.level_index + 1)
        elif self.state == "winner":
            for bit in self.confetti:
                bit[1] += bit[3] * dt
                if bit[1] > SCREEN_SIZE[1] + 20:
                    bit[0] = random.randint(40, SCREEN_SIZE[0] - 40)
                    bit[1] = random.randint(-160, -20)

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

    def menu_buttons(self):
        return {
            "new_game": pygame.Rect(332, 248, 360, 72),
            "add_player": pygame.Rect(332, 340, 360, 72),
            "high_score": pygame.Rect(332, 432, 360, 72),
            "exit": pygame.Rect(332, 524, 360, 72),
        }

    def pause_buttons(self):
        return {
            "new_game": pygame.Rect(332, 300, 360, 72),
            "cancel": pygame.Rect(332, 392, 360, 72),
            "exit": pygame.Rect(332, 484, 360, 72),
        }

    def winner_buttons(self):
        return {
            "play_again": pygame.Rect(332, 476, 360, 72),
            "high_score": pygame.Rect(332, 566, 360, 72),
            "menu": pygame.Rect(332, 656, 360, 72),
        }

    def name_buttons(self):
        return {
            "start": pygame.Rect(344, 478, 336, 74),
            "back": pygame.Rect(392, 574, 240, 62),
        }

    def back_button(self):
        return pygame.Rect(392, 634, 240, 62)

    def draw(self):
        self.screen.fill(BG)
        self.draw_clouds()
        if self.state in ("game", "pause"):
            self.draw_progress()
            self.draw_maze()
            self.draw_side_panel()
            self.draw_answer_strip()
            self.draw_tray()
            self.draw_confetti()
            self.draw_message()
            self.draw_dragging()
            if self.state == "pause":
                self.draw_pause_overlay()
        elif self.state == "name":
            self.draw_name_screen()
        elif self.state == "scores":
            self.draw_high_scores()
        elif self.state == "winner":
            self.draw_winner_screen()
        else:
            self.draw_menu()
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

    def draw_menu(self):
        title = self.title_font.render("Arrow Path", True, PURPLE)
        subtitle = self.font.render("to Treasure", True, (255, 111, 145))
        self.screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0] // 2, 130)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_SIZE[0] // 2, 184)))

        player = self.small_font.render(f"Player: {self.current_player}", True, PURPLE)
        self.screen.blit(player, player.get_rect(center=(SCREEN_SIZE[0] // 2, 222)))

        labels = {
            "new_game": "NEW GAME",
            "add_player": "ADD NEW PLAYER",
            "high_score": "HIGH SCORE",
            "exit": "EXIT",
        }
        colors = {
            "new_game": (82, 196, 126),
            "add_player": (255, 185, 64),
            "high_score": (91, 141, 239),
            "exit": (255, 111, 145),
        }
        for key, rect in self.menu_buttons().items():
            draw_menu_button(self.screen, self.font, rect, labels[key], colors[key])

        kid_rect = pygame.Rect(128, 300, 150, 230)
        treasure_rect = pygame.Rect(748, 318, 168, 140)
        blit_fit(self.screen, self.character, kid_rect)
        blit_fit(self.screen, self.treasure, treasure_rect)

    def draw_name_screen(self):
        title = self.title_font.render("New Player", True, PURPLE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0] // 2, 150)))
        hint = self.small_font.render("Type a name, then press Enter or Start", True, PURPLE)
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_SIZE[0] // 2, 214)))

        input_rect = pygame.Rect(284, 288, 456, 82)
        draw_round_rect(self.screen, input_rect, WHITE, radius=24, border=6, border_color=(255, 236, 128))
        shown_name = self.name_input or "Player name"
        color = PURPLE if self.name_input else (145, 132, 170)
        text = self.font.render(shown_name, True, color)
        self.screen.blit(text, text.get_rect(center=input_rect.center))

        buttons = self.name_buttons()
        draw_menu_button(self.screen, self.font, buttons["start"], "START GAME", (82, 196, 126))
        draw_menu_button(self.screen, self.small_font, buttons["back"], "BACK", (255, 185, 64))

    def draw_high_scores(self):
        title = self.title_font.render("High Score", True, PURPLE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0] // 2, 118)))
        panel = pygame.Rect(252, 174, 520, 430)
        draw_round_rect(self.screen, panel, PANEL, radius=34, border=6, border_color=WHITE)

        scores = sorted(self.high_scores.items(), key=lambda item: (-item[1], item[0].lower()))[:8]
        if not scores:
            empty = self.font.render("No scores yet", True, PURPLE)
            self.screen.blit(empty, empty.get_rect(center=panel.center))
        for index, (name, score) in enumerate(scores):
            y = panel.y + 54 + index * 44
            rank = self.small_font.render(f"{index + 1}.", True, PURPLE)
            player = self.small_font.render(name, True, PURPLE)
            points = self.small_font.render(f"{score}/{len(LEVELS)}", True, (82, 196, 126))
            self.screen.blit(rank, rank.get_rect(midleft=(panel.x + 42, y)))
            self.screen.blit(player, player.get_rect(midleft=(panel.x + 96, y)))
            self.screen.blit(points, points.get_rect(midright=(panel.right - 44, y)))

        draw_menu_button(self.screen, self.small_font, self.back_button(), "BACK", (255, 185, 64))

    def draw_winner_screen(self):
        title = self.title_font.render("You Win!", True, PURPLE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0] // 2, 138)))
        subtitle = self.font.render("All levels complete!", True, (255, 111, 145))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_SIZE[0] // 2, 200)))

        star_count = len(LEVELS)
        gap = 44
        start_x = SCREEN_SIZE[0] // 2 - (star_count - 1) * gap // 2
        for index in range(star_count):
            draw_star(self.screen, (start_x + index * gap, 262), 17, (255, 185, 64))

        score = self.small_font.render(
            f"{self.current_player}: {len(LEVELS)}/{len(LEVELS)} levels", True, PURPLE
        )
        self.screen.blit(score, score.get_rect(center=(SCREEN_SIZE[0] // 2, 322)))

        kid_rect = pygame.Rect(112, 380, 160, 250)
        treasure_rect = pygame.Rect(742, 410, 180, 150)
        blit_fit(self.screen, self.character, kid_rect)
        blit_fit(self.screen, self.treasure, treasure_rect)

        labels = {"play_again": "PLAY AGAIN", "high_score": "HIGH SCORE", "menu": "MENU"}
        colors = {"play_again": (82, 196, 126), "high_score": (91, 141, 239), "menu": (255, 185, 64)}
        for key, rect in self.winner_buttons().items():
            draw_menu_button(self.screen, self.font, rect, labels[key], colors[key])

        self.draw_confetti()

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
        if not self.celebrating and self.state != "winner":
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

    def draw_pause_overlay(self):
        overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        overlay.fill((40, 30, 60, 175))
        self.screen.blit(overlay, (0, 0))

        title = self.title_font.render("Paused", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_SIZE[0] // 2, 220)))

        labels = {"new_game": "NEW GAME", "cancel": "CANCEL", "exit": "EXIT"}
        colors = {"new_game": (82, 196, 126), "cancel": (255, 185, 64), "exit": (255, 111, 145)}
        for key, rect in self.pause_buttons().items():
            draw_menu_button(self.screen, self.font, rect, labels[key], colors[key])

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


def draw_menu_button(surface, font, rect, label, color):
    draw_round_rect(surface, rect, color, radius=28, border=6, border_color=WHITE)
    text = font.render(label, True, WHITE)
    surface.blit(text, text.get_rect(center=rect.center))


def load_high_scores():
    if not SCORE_FILE.exists():
        return {}
    try:
        with SCORE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(name)[:14]: int(score) for name, score in data.items() if isinstance(score, int) and score >= 0}


def save_high_scores(scores):
    ordered = dict(sorted(scores.items(), key=lambda item: (-item[1], item[0].lower())))
    with SCORE_FILE.open("w", encoding="utf-8") as file:
        json.dump(ordered, file, indent=2)


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
