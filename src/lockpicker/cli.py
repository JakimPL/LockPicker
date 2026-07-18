import argparse
from pathlib import Path
from typing import Optional, Tuple

import pygame

from lockpicker.agents.random import play_random_games
from lockpicker.constants.config import RendererMode, settings
from lockpicker.engine.lock import Lock
from lockpicker.game.editor.editor import Editor
from lockpicker.game.game import Game
from lockpicker.level.level import Level


def load_level(
    path: Path,
    number_of_picks: int,
    max_height: int,
) -> Level:
    if path.exists() and path.is_file():
        return Level.load(path)

    if number_of_picks < settings.rules.min_number_of_picks:
        raise ValueError(f"number_of_picks must be at least {settings.rules.min_number_of_picks}")

    if max_height < settings.rules.min_max_height:
        raise ValueError(f"max_height must be at least {settings.rules.min_max_height}")

    return Level.create(number_of_picks, max_height)


def parse_resolution(value: str) -> Tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x")
        return int(width_text), int(height_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid resolution {value!r}, expected WIDTHxHEIGHT") from error


def create_window(
    resolution: Optional[Tuple[int, int]],
    *,
    fullscreen: bool,
) -> pygame.surface.Surface:
    if fullscreen or (settings.display.fullscreen and resolution is None):
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    width, height = resolution if resolution is not None else (settings.display.width, settings.display.height)
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load a level from a file.",
    )
    parser.add_argument(
        "level_file",
        type=str,
        help="Path to the level file",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="Run the level editor",
    )
    parser.add_argument(
        "--random_moves",
        action="store_true",
        help="Plays random moves",
    )
    parser.add_argument(
        "--number_of_picks",
        type=int,
        default=settings.rules.default_number_of_picks,
        help="Number of picks (at least 1)",
    )
    parser.add_argument(
        "--max_height",
        type=int,
        default=settings.rules.default_max_height,
        help="Maximum height (at least 2)",
    )
    parser.add_argument(
        "--random_agent",
        action="store_true",
        help="Random simulation agent",
    )
    parser.add_argument(
        "--renderer",
        type=RendererMode,
        choices=list(RendererMode),
        default=None,
        help="Renderer mode (defaults to theme.mode from config)",
    )
    parser.add_argument(
        "--resolution",
        type=parse_resolution,
        default=None,
        help="Window size as WIDTHxHEIGHT (defaults to display config)",
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        help="Fullscreen at desktop resolution",
    )
    args = parser.parse_args()

    path = Path(args.level_file)
    lock = Lock(
        load_level(
            path,
            number_of_picks=args.number_of_picks,
            max_height=args.max_height,
        )
    )

    if args.random_agent:
        print(play_random_games(lock))
        return

    def run_game() -> None:
        lock_copy = Lock(lock.level.copy())
        window = pygame.display.get_surface() or screen
        game = Game(
            window,
            lock_copy,
            random_moves=args.random_moves,
            renderer_mode=args.renderer,
        )
        game.run()

    pygame.init()
    pygame.display.set_caption("LockPicker")
    screen = create_window(args.resolution, fullscreen=args.fullscreen)

    if args.edit:
        editor = Editor(
            screen,
            lock,
            path,
            run_game,
            renderer_mode=args.renderer,
        )
        editor.run()
    else:
        try:
            run_game()
        except KeyboardInterrupt:
            print("Bye!")

    pygame.quit()
