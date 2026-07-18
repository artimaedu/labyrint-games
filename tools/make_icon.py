"""Build a square 256x256 app icon from the treasure asset.

Usage: python tools/make_icon.py [output.png]
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist/icon.png")
    source_path = Path(__file__).resolve().parent.parent / "assets" / "treasure.png"
    source = pygame.image.load(str(source_path))

    size = 256
    margin = 16
    icon = pygame.Surface((size, size), pygame.SRCALPHA)
    rect = source.get_rect()
    scale = min((size - margin) / rect.width, (size - margin) / rect.height)
    target = (max(1, int(rect.width * scale)), max(1, int(rect.height * scale)))
    scaled = pygame.transform.smoothscale(source, target)
    icon.blit(scaled, scaled.get_rect(center=(size // 2, size // 2)))

    out.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(icon, str(out))
    print(f"icon written to {out}")


if __name__ == "__main__":
    main()
