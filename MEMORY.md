# Project Memory

## Project

- Repository: `labyrint-games`
- Remote: `https://github.com/artimaedu/labyrint-games.git`
- Branch: `main`
- Game: `Arrow Path to Treasure`, a kid-friendly Python/Pygame maze path game.

## Run Commands

Windows:

```powershell
.\.venv\Scripts\python.exe main.py
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Main Files

- `main.py`: game loop, state, scaling/fullscreen, input handling, animations.
- `levels.py`: ordered linear level definitions.
- `maze.py`: path construction and validation.
- `ui.py`: buttons, arrows, answer strip drawing.
- `tools/process_assets.py`: removes edge backgrounds from source images and rebuilds transparent PNG assets.
- `assets/`: runtime PNG assets.

## Current Features

- Start menu with `NEW GAME`, `ADD NEW PLAYER`, `HIGH SCORE`, and `EXIT`.
- Player names are typed in-game and saved locally.
- High scores are stored in `high_scores.json`, one best completed-level score per player.
- If the same player gets a better score, the old score is replaced.
- Click-to-place and drag-to-place arrows.
- Answer strip with removable slots.
- Undo button removes the last arrow.
- Eraser button clears all input.
- `GO` checks the answer.
- Correct answer triggers character movement, `Great!` message, confetti, and a short win jingle.
- Finishing the last level shows a `You Win!` splash screen (stars, player score, looping confetti, `PLAY AGAIN` / `HIGH SCORE` / `MENU` buttons) and plays a longer victory fanfare.
- The in-game sound button mutes/unmutes the win sounds.
- Incorrect answer gives a gentle retry message.
- Window is resizable and attempts to maximize.
- `F11` toggles fullscreen; `Esc` exits fullscreen.
- Keyboard shortcuts during a level: arrow keys place directions, `Backspace`/`Delete` undoes the last arrow, `Esc` opens a pause menu (`NEW GAME` / `CANCEL` / `EXIT`).
- Each level's maze path is randomly generated on load (`maze.random_path`): `levels.py` now only supplies the band/grid/move-count "shape" per level, and the actual start cell + direction sequence are freshly randomized (self-avoiding, in-bounds) every time that level loads.
- Paths are guaranteed non-tangent: no two non-consecutive cells share an edge, so the corridor is always visually unambiguous. The treasure is never adjacent to the start cell, preventing shortcuts.
- Maze walls are rendered as solid brick-pattern blocks (no rounded corners), with thick dark borders facing corridor cells. The path corridor is a flat open floor between walls.
- Works on Windows and should run on Linux with Python 3 and Pygame.

## Asset Notes

- `assets/source/kid.jpg` and `assets/source/treasure.png` are the original downloaded sources.
- `assets/character.png` and `assets/treasure.png` are cleaned transparent runtime images.
- `assets/win_level.wav` and `assets/win_all.wav` are chiptune-style jingles generated procedurally by `main.py` on first run (delete them to regenerate).
- Rebuild cleaned images with:

```bash
python tools/process_assets.py
```

## Git Notes

- `.gitignore` excludes `.venv/`, `__pycache__/`, `*.pyc`, environment files, caches, and build outputs.
- `.gitignore` also excludes `high_scores.json` because it is local player data.
- Initial commit was `1d9e5de first commit`.
