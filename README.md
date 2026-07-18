# Arrow Path to Treasure

A small Pygame labyrinth game for kids. Each level shows one visible path from a character to a treasure. The player recreates the path by placing arrows into the answer strip.

## Run on Windows

1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/.
2. Open PowerShell in this folder.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again.

4. Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

5. Start the game:

```powershell
py main.py
```

The first run creates simple placeholder PNG files in `assets/` if they are missing.

## Run on Linux

1. Install Python and venv support. On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

2. Open a terminal in this folder.
3. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

5. Start the game:

```bash
python main.py
```

The window is resizable on Linux too. Press `F11` for fullscreen presentation mode and `Esc` to leave fullscreen.

To rebuild the cleaned character and treasure PNGs from files in `assets/source/`, run:

```powershell
.\.venv\Scripts\python.exe tools\process_assets.py
```

On Linux, run:

```bash
python tools/process_assets.py
```

## Controls

- The game starts on a menu with `NEW GAME`, `ADD NEW PLAYER`, `HIGH SCORE`, and `EXIT`.
- `ADD NEW PLAYER` lets you type a player name and starts a fresh game.
- `HIGH SCORE` shows the best completed-level score for each player.
- If the same player earns a better score, the old score is replaced.
- Click an arrow in the tray to place it in the next empty answer slot.
- Drag an arrow from the tray to the answer strip to place it.
- Click a filled answer slot to remove that arrow.
- Use the left arrow button to undo the last arrow.
- Use the eraser button to clear all input.
- Press `GO` to check, or fill all slots to check automatically.
- Resize or maximize the window for a larger display.
- Press `F11` to toggle fullscreen. Press `Esc` to leave fullscreen.

### Keyboard Shortcuts (during a level)

- `Up` / `Down` / `Left` / `Right` arrow keys: place that direction in the next empty answer slot, same as clicking the tray button.
- `Backspace` or `Delete`: remove the last placed arrow (same as the undo button).
- `Esc`: open the pause menu with `NEW GAME`, `CANCEL`, and `EXIT`. Press `Esc` again to `CANCEL` and resume. If the window is in fullscreen, the first `Esc` press leaves fullscreen instead.

Scores are saved locally in `high_scores.json`. This file is ignored by Git because it is player data.

## Add Or Reorder Levels

Levels are defined in `levels.py`. Each entry is a template, not a fixed maze:

- `band`: `Beginner`, `Intermediate`, or `Hard`
- `grid`: grid size as `(columns, rows)`
- `start`: only used to determine the template's move count; the actual start
  cell is randomized at load time (see below)
- `path`: only its length matters; the actual directions are randomized at
  load time

Example:

```python
{"band": "Beginner", "grid": (4, 4), "start": (0, 1), "path": "RRD"}
```

This template means: a Beginner-band, 4x4 level with a 3-move path. Every time
this level loads, `maze.random_path()` picks a fresh random start cell and a
fresh random self-avoiding sequence of 3 moves that stays inside the grid, so
the maze is different each time you play.

Maze walls are rendered as solid brick-pattern blocks (no rounded corners), with
thick dark borders on every wall edge that faces the corridor. The path between
walls is drawn as a flat open floor.

To reorder levels or change difficulty, edit the `grid` size and the length of
`path` in `levels.py`. The game uses simple linear progression through the
`LEVELS` list.
