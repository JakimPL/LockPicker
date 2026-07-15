# Lock Picker

Lock Picker is a small logic-puzzle game built with PyGame. A lock is a set of
**tumblers** arranged in columns; each column has an upper and a lower tumbler
that share a height budget. You manipulate the tumblers with a set of **picks**,
pushing and releasing them in the right order until every tumbler is free. Some
tumblers are **bound** to others (pushing one moves another), some are
**masters** that jam their whole group, and some spring to a different height
once released. The goal is to get every tumbler into its free position at the
same time.

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Install

```bash
uv sync
```

## Running

The entry point takes a path to a level file. If the file does not exist, a new
empty level is created with the given dimensions (useful together with `--edit`).

```bash
# Play a level
uv run python main.py levels/level_01_01.lvl

# Equivalent invocations
uv run python -m lockpicker levels/level_01_01.lvl
uv run lockpicker levels/level_01_01.lvl

# Open a level in the editor
uv run python main.py levels/level_01_01.lvl --edit

# Watch / run random moves alongside your own input
uv run python main.py levels/level_01_01.lvl --random_moves

# Headless random-agent simulation (no window; CI-safe)
SDL_VIDEODRIVER=dummy uv run python main.py levels/level_01_01.lvl --random_agent
```

CLI options:

| Option              | Effect                                                            |
| ------------------- | ----------------------------------------------------------------- |
| `--edit`            | Open the level editor instead of playing.                         |
| `--random_moves`    | The game also plays random moves each frame.                      |
| `--random_agent`    | Run a headless simulation of random games; prints whether it won. |
| `--number_of_picks` | Picks for a freshly created level (used when the file is absent). |
| `--max_height`      | Maximum tumbler height for a freshly created level.               |

## Controls

### Game

| Input               | Action                                             |
| ------------------- | -------------------------------------------------- |
| Left-click tumbler  | Push the tumbler with the current pick.            |
| Left-click empty    | Release the current pick.                          |
| Right-click         | Switch to the next pick.                           |
| `Ctrl` + `Z` / `Y`  | Undo / redo.                                        |
| `Ctrl` + `R`        | Restart the level.                                  |
| `Esc`               | Quit.                                               |

### Editor

| Input                | Action                                                     |
| -------------------- | ---------------------------------------------------------- |
| Left-drag tumbler    | Set the tumbler's base height.                             |
| Right-drag tumbler   | Set the tumbler's post-release height.                     |
| `Insert`             | Add a tumbler at the cursor.                               |
| `Delete`             | Remove the highlighted tumbler.                            |
| `1` / `2` / `3`      | Select the active group (and reassign the highlighted one).|
| `M`                  | Toggle the highlighted tumbler as its group's master.      |
| `B`                  | Bind tumblers: press on the source, then the target.       |
| Right-click          | Cancel an in-progress binding.                             |
| `Ctrl` + `S`         | Save the level to its file.                                |
| `Ctrl` + `P`         | Play-test the current level.                               |
| `Ctrl` + `Z` / `Y`   | Undo / redo.                                                |
| `Esc`                | Quit.                                                       |

## Configuration

All presentation and gameplay tuning lives in [`config.yaml`](config.yaml)
(screen size, layout, colors, pick shapes, animation speed, simulation limits).
It is loaded once into a validated Pydantic settings singleton
(`lockpicker.constants.config.settings`); there are no hardcoded defaults in
code. Binary level files (`levels/*.lvl`) are a separate, gzip-compressed wire
format owned by the serialization codec.

## Architecture

The domain core is framework-free (no PyGame); everything PyGame lives under
`game/`.

```
src/lockpicker/
├── lock.py            # Lock: the rules engine (push/release, bindings,
│                      #   masters, win check, state save/load, board snapshots)
├── pick.py            # PickSet: pick-slot bookkeeping
├── level/
│   ├── level.py       # Level: tumblers + bindings, (de)serialization, save/load
│   ├── data.py        # LevelData: the on-disk block layout
│   └── validation.py  # Pydantic load-boundary validation
├── tumbler/
│   ├── definition.py  # TumblerDefinition: frozen authored data + wire codec
│   ├── state.py       # TumblerState: mutable runtime state
│   ├── tumbler.py     # Tumbler: aggregate (definition + state + counter wiring)
│   └── location.py    # Location: (position, upper) coordinate
├── state/state.py     # State: value-equal snapshot used for undo/redo
├── game/
│   ├── base.py        # BaseGame: shared rendering + input
│   ├── game.py        # Game: play loop
│   ├── editor.py      # Editor: level authoring + snapshot-based undo
│   ├── layout.py      # Layout: pure geometry (height ↔ pixel transforms)
│   └── animation.py   # Board-snapshot deltas → animation steps
├── agents/random.py   # RandomAgent + headless simulation
├── constants/config.py# Pydantic settings loaded from config.yaml
└── paths.py           # Path resolution
```

Three tumbler types are kept deliberately, separated by lifecycle and consumer:
`TumblerDefinition` is the frozen, authored, serialized unit; `TumblerState` is
the mutable per-move runtime payload; `Tumbler` is the runtime aggregate that
owns behavior, the injected `max_height`, and the counter wiring. The engine
records an ordered list of board snapshots; the UI drains them and computes the
per-tumbler height animation, keeping animation concerns out of the core.

## Development

```bash
uv run pytest          # tests (characterization goldens + unit tests)
uv run mypy            # strict type checking
uv run pre-commit run --all-files
```
