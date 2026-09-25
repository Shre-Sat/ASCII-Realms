# ASCII-Realms
# ASCII Realms — A Battle RPG

A tiny, fully self-contained turn-based battle RPG rendered entirely in
text-mode "ASCII graphics," built with **pygame-ce**. Every sound effect
and background track is **synthesized on the fly with numpy** — there
are no image or audio asset files anywhere in this repo.

```
   _   ____   ____ ___ ___    ____  _____    _    _     __  __ ____
  / \ / ___| / ___|_ _|_ _|  |  _ \| ____|  / \  | |   |  \/  / ___|
 / _ \\___ \| |    | | | |   | |_) |  _|   / _ \ | |   | |\/| \___ \
/ ___ \___) | |___ | | | |   |  _ <| |___ / ___ \| |___| |  | |___) |
/_/   \_\____/ \____|___|___|  |_| \_\_____/_/   \_\_____|_|  |_|____/
```

## Features

- **Pure text-mode graphics** — every sprite, health bar, and menu is
  drawn with a monospace font and box-drawing characters. No sprite
  sheets, no image files.
- **Procedural audio** — a `SoundEngine` class generates every sound
  effect (attacks, hits, healing, magic, victory/defeat jingles) and
  background chiptune loop at runtime from raw sine/square/saw/noise
  waveforms.
- **2 full levels** — *Whispering Woods* (Goblin Grunt) and *Dragon's
  Lair* (Ember Drake), each with its own intro sequence, enemy, and
  music.
- **Turn-based combat** — Attack / Defend / Magic / Item, with HP & MP
  bars, a scrolling battle log, and hit-flash/screen-shake feedback.
- **Clean OOP architecture** — the whole game is organized into small,
  single-responsibility classes (see [Architecture](#architecture)
  below) rather than one big script.

## Requirements

- Python 3.9+
- [`pygame-ce`](https://pyga.me/)
- `numpy`

## Installation

```bash
git clone https://github.com/<your-username>/ascii-realms.git
cd ascii-realms
pip install pygame-ce numpy
```

## Running the game

```bash
python main.py
```

## Controls

| Context     | Keys                                  | Action                    |
|-------------|----------------------------------------|----------------------------|
| Menus       | `↑`/`↓` or `W`/`S`                     | Move selection             |
| Menus       | `Enter` / `Space`                      | Confirm                    |
| Battle      | `1`                                    | Attack                     |
| Battle      | `2`                                    | Defend                     |
| Battle      | `3`                                    | Cast Magic (6 MP)          |
| Battle      | `4`                                    | Use Item (Potion)          |
| Anywhere    | `Esc`                                  | Quit                       |

## Project Structure

```
ascii_realms/
├── main.py                  # Entry point — creates and runs the Game
└── ascii_realms/
    ├── __init__.py
    ├── config.py             # Window size & color palette constants
    ├── ascii_art.py          # All ASCII art strings (title, fighters)
    ├── audio.py               # SoundEngine — procedural SFX/BGM synthesis
    ├── entities.py            # Fighter (base) → Player, Enemy (subclasses)
    ├── levels.py               # Level class + the level data table
    ├── ui.py                   # Renderer — text/box/HP-bar drawing helpers
    ├── states.py                # GameState (ABC) + all concrete screens
    └── game.py                   # Game — state machine & main loop
```

## Architecture

The project follows a few classic object-oriented patterns to keep
logic, rendering, and audio cleanly separated:

- **`Fighter` (abstract base class) → `Player` / `Enemy`**
  `Fighter` holds shared battle state (HP, guarding, hit-animation
  timers) and damage handling. `Player` adds MP, magic, and a potion
  inventory; `Enemy` adds a named special attack. Both can be treated
  polymorphically by anything that just needs "a fighter with HP and
  art."

- **`GameState` (abstract base class) + the State pattern**
  Every screen — `TitleState`, `IntroState`, `BattleState`,
  `LevelWinState`, `GameOverState`, `WinGameState` — implements the
  same `handle_event / update / draw` interface. `Game.run()` calls
  `self.state.<method>()` without knowing which screen is active, and
  `Game.change_state()` swaps screens cleanly.

- **`SoundEngine`**
  Encapsulates all numpy waveform synthesis and pygame mixer setup
  behind a simple `play_sfx(key)` / `play_bgm(key)` API, including
  runtime detection of mono vs. stereo mixer output.

- **`Renderer`**
  Wraps the pygame screen and fonts, exposing reusable drawing
  primitives (`draw_text`, `draw_ascii_block`, `draw_box`,
  `draw_hp_bar`) so no other module touches raw pygame draw calls.

- **`Game`**
  The composition root: owns the window, clock, `SoundEngine`,
  `Renderer`, session data (player, current enemy, level index, battle
  log), and the battle rules (`player_action`, `enemy_turn`,
  `check_battle_end`) that `BattleState` calls into.

## Extending the game

- **Add a level**: append a new `Level(...)` entry to `LEVELS` in
  `levels.py` with its own title, intro text, background-music key,
  and an `Enemy` factory.
- **Add a new player ability**: add a method to `Player` in
  `entities.py`, then wire it into `BattleState.MENU` and
  `Game.player_action()`.
- **Add a new screen**: subclass `GameState` in `states.py` and
  transition to it with `game.change_state(YourState)`.

## License

MIT — do whatever you'd like with it.

