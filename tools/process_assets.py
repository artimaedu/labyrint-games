from collections import deque
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def is_edge_background(color):
    r, g, b, a = color
    return a == 0 or (r > 205 and g > 205 and b > 205 and abs(r - g) < 22 and abs(g - b) < 22 and abs(r - b) < 22)


def remove_edge_background(source, output, max_size=512):
    surface = pygame.image.load(str(source)).convert_alpha()
    width, height = surface.get_size()
    seen = bytearray(width * height)
    queue = deque()

    def push(x, y):
        index = y * width + x
        if not seen[index] and is_edge_background(surface.get_at((x, y))):
            seen[index] = 1
            queue.append((x, y))

    for x in range(width):
        push(x, 0)
        push(x, height - 1)
    for y in range(height):
        push(0, y)
        push(width - 1, y)

    while queue:
        x, y = queue.popleft()
        r, g, b, _a = surface.get_at((x, y))
        surface.set_at((x, y), (r, g, b, 0))

        if x > 0:
            push(x - 1, y)
        if x < width - 1:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y < height - 1:
            push(x, y + 1)

    min_x, min_y = width, height
    max_x, max_y = -1, -1
    for y in range(height):
        for x in range(width):
            if surface.get_at((x, y)).a:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < min_x or max_y < min_y:
        raise ValueError(f"No visible pixels left after background removal: {source}")

    cropped = surface.subsurface(pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)).copy()
    scale = min(max_size / cropped.get_width(), max_size / cropped.get_height(), 1)
    if scale < 1:
        size = (int(cropped.get_width() * scale), int(cropped.get_height() * scale))
        cropped = pygame.transform.smoothscale(cropped, size)

    pygame.image.save(cropped, str(output))


def main():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    remove_edge_background(ASSETS / "source" / "kid.jpg", ASSETS / "character.png")
    remove_edge_background(ASSETS / "source" / "treasure.png", ASSETS / "treasure.png")
    print("Processed transparent character.png and treasure.png")


if __name__ == "__main__":
    main()
