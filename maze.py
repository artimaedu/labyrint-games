DIRECTION_VECTORS = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}


def build_path(level):
    cells = [level["start"]]
    x, y = level["start"]
    width, height = level["grid"]

    for direction in level["path"]:
        dx, dy = DIRECTION_VECTORS[direction]
        x += dx
        y += dy
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"Level path leaves the grid at {(x, y)}")
        if (x, y) in cells:
            raise ValueError(f"Level path loops back through {(x, y)}")
        cells.append((x, y))

    return cells


def solution(level):
    return list(level["path"])
