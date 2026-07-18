import random

DIRECTION_VECTORS = {
    "U": (0, -1),
    "D": (0, 1),
    "L": (-1, 0),
    "R": (1, 0),
}

DIRECTIONS = list(DIRECTION_VECTORS)


def _neighbor_dirs(x, y):
    for dx, dy in DIRECTION_VECTORS.values():
        nx, ny = x + dx, y + dy
        yield nx, ny


def _has_tangent(cells):
    cell_set = set(cells)
    for i, (ax, ay) in enumerate(cells):
        for nx, ny in _neighbor_dirs(ax, ay):
            neighbor = (nx, ny)
            if neighbor in cell_set:
                j = cells.index(neighbor)
                if abs(i - j) != 1:
                    return True
    return False


def _treasure_is_clear(cells):
    treasure = cells[-1]
    start = cells[0]
    for nx, ny in _neighbor_dirs(start[0], start[1]):
        if (nx, ny) == treasure:
            return False
    return True


def random_path(grid, length, rng=random, attempts=5000):
    """Generate a random self-avoiding start cell + move sequence.

    The path is guaranteed to be non-tangent: no two non-consecutive cells
    share an edge.  The treasure cell is never adjacent to any cell except
    the one right before it, so the player cannot shortcut to the goal.
    """
    width, height = grid
    for _ in range(attempts):
        start = (rng.randrange(width), rng.randrange(height))
        cur = start
        visited = {start}
        path = []
        for _ in range(length):
            candidates = list(DIRECTIONS)
            rng.shuffle(candidates)
            for direction in candidates:
                dx, dy = DIRECTION_VECTORS[direction]
                nxt = (cur[0] + dx, cur[1] + dy)
                if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in visited:
                    path.append(direction)
                    visited.add(nxt)
                    cur = nxt
                    break
            else:
                break
        if len(path) != length:
            continue
        cells = _path_cells(start, path)
        if _has_tangent(cells):
            continue
        if not _treasure_is_clear(cells):
            continue
        return start, "".join(path)
    raise RuntimeError("could not generate a random path for this grid/length")


def _path_cells(start, path):
    cells = [start]
    x, y = start
    for direction in path:
        dx, dy = DIRECTION_VECTORS[direction]
        x += dx
        y += dy
        cells.append((x, y))
    return cells


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
