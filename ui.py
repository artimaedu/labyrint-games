import pygame


ARROW_COLORS = {
    "U": (91, 141, 239),
    "D": (82, 196, 126),
    "L": (255, 185, 64),
    "R": (255, 111, 145),
}


def draw_round_rect(surface, rect, color, radius=20, border=0, border_color=(255, 255, 255)):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)


def draw_arrow(surface, rect, direction, color=None):
    color = color or ARROW_COLORS[direction]
    cx, cy = rect.center
    size = min(rect.width, rect.height)
    shaft = max(8, size // 7)
    head = size // 3
    length = size // 2

    if direction == "U":
        pygame.draw.rect(surface, color, (cx - shaft // 2, cy - length // 5, shaft, length // 2), border_radius=5)
        points = [(cx, cy - length // 2), (cx - head, cy - 3), (cx + head, cy - 3)]
    elif direction == "D":
        pygame.draw.rect(surface, color, (cx - shaft // 2, cy - length // 3, shaft, length // 2), border_radius=5)
        points = [(cx, cy + length // 2), (cx - head, cy + 3), (cx + head, cy + 3)]
    elif direction == "L":
        pygame.draw.rect(surface, color, (cx - length // 5, cy - shaft // 2, length // 2, shaft), border_radius=5)
        points = [(cx - length // 2, cy), (cx - 3, cy - head), (cx - 3, cy + head)]
    else:
        pygame.draw.rect(surface, color, (cx - length // 3, cy - shaft // 2, length // 2, shaft), border_radius=5)
        points = [(cx + length // 2, cy), (cx + 3, cy - head), (cx + 3, cy + head)]

    pygame.draw.polygon(surface, color, points)


class Button:
    def __init__(self, rect, kind, color):
        self.rect = pygame.Rect(rect)
        self.kind = kind
        self.color = color

    def draw(self, surface, font):
        draw_round_rect(surface, self.rect, self.color, radius=22, border=4, border_color=(255, 255, 255))
        if self.kind in ("U", "D", "L", "R"):
            draw_arrow(surface, self.rect.inflate(-18, -18), self.kind)
        elif self.kind == "refresh":
            x, y, w, h = self.rect.inflate(-24, -24)
            eraser = pygame.Rect(x + 4, y + 15, w - 8, h - 8)
            pygame.draw.rect(surface, (255, 143, 171), eraser, border_radius=8)
            pygame.draw.polygon(
                surface,
                (255, 255, 255),
                [(eraser.left + 12, eraser.top), (eraser.right, eraser.top), (eraser.right - 12, eraser.bottom), (eraser.left, eraser.bottom)],
            )
            pygame.draw.line(surface, (92, 69, 142), (eraser.left + 14, eraser.bottom), (eraser.right - 14, eraser.bottom), 4)
            pygame.draw.circle(surface, (92, 69, 142), (x + 9, y + 7), 3)
            pygame.draw.line(surface, (92, 69, 142), (x + 9, y + 1), (x + 9, y + 13), 2)
            pygame.draw.line(surface, (92, 69, 142), (x + 3, y + 7), (x + 15, y + 7), 2)
            pygame.draw.circle(surface, (255, 255, 255), (x + w - 2, y + 9), 4)
        elif self.kind == "undo":
            center = self.rect.center
            pygame.draw.line(surface, (92, 69, 142), (center[0] + 22, center[1]), (center[0] - 18, center[1]), 9)
            pygame.draw.polygon(surface, (92, 69, 142), [(center[0] - 28, center[1]), (center[0] - 4, center[1] - 21), (center[0] - 4, center[1] + 21)])
        elif self.kind == "clear":
            x, y, w, h = self.rect.inflate(-34, -34)
            pygame.draw.rect(surface, (92, 69, 142), (x + 12, y + 18, w - 24, h - 14), border_radius=7)
            pygame.draw.rect(surface, (255, 236, 128), (x + 16, y + 8, w - 32, 14), border_radius=4)
            pygame.draw.line(surface, (255, 255, 255), (x + 24, y + 26), (x + 24, y + h - 5), 4)
            pygame.draw.line(surface, (255, 255, 255), (x + w - 24, y + 26), (x + w - 24, y + h - 5), 4)
        elif self.kind == "sound":
            x, y, w, h = self.rect.inflate(-34, -34)
            pygame.draw.polygon(surface, (92, 69, 142), [(x, y + h // 2 - 12), (x + 18, y + h // 2 - 12), (x + 36, y), (x + 36, y + h)])
            pygame.draw.arc(surface, (92, 69, 142), (x + 30, y + 8, 30, h - 16), -0.7, 0.7, 5)
        elif self.kind == "go":
            label = font.render("GO", True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=self.rect.center))


def answer_slot_rects(count, screen_width, y):
    gap = 8
    max_total = screen_width - 96
    slot = min(58, (max_total - (count - 1) * gap) // count)
    slot = max(42, slot)
    total = count * slot + (count - 1) * gap
    start_x = (screen_width - total) // 2
    return [pygame.Rect(start_x + i * (slot + gap), y, slot, slot) for i in range(count)]
