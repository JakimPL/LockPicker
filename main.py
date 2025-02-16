import argparse
from pathlib import Path
from typing import Optional

import pygame

from lockpicker.agents.random import play_random_games
from lockpicker.constants.gui import HEIGHT, WIDTH
from lockpicker.game.editor import Editor
from lockpicker.game.game import Game
from lockpicker.level import MAX_HEIGHT, NUMBER_OF_PICKS
from lockpicker.lock import Level, Lock


def load_level(path: Path, number_of_picks: Optional[int], max_height: Optional[int]) -> Level:
    if path.exists() and path.is_file():
        return Level.load(path)
    else:
        if number_of_picks < 1:
            raise ValueError("number_of_picks must be at least 1")
        if max_height < 3:
            raise ValueError("max_height must be at least 3")

        return Level.create(number_of_picks, max_height)


def main():
    parser = argparse.ArgumentParser(description="Load a level from a file.")
    parser.add_argument("level_file", type=str, help="Path to the level file")
    parser.add_argument("--edit", action="store_true", help="Run the level editor")
    parser.add_argument("--random_moves", action="store_true", help="Plays random moves")
    parser.add_argument("--number_of_picks", type=int, default=NUMBER_OF_PICKS, help="Number of picks (at least 1)")
    parser.add_argument("--max_height", type=int, default=MAX_HEIGHT, help="Maximum height (at least 2)")
    parser.add_argument("--random_agent", action="store_true", help="Random simulation agent")
    args = parser.parse_args()

    path = Path(args.level_file)
    lock = Lock(load_level(path, number_of_picks=args.number_of_picks, max_height=args.max_height))

    if args.random_agent:
        print(play_random_games(lock))
        return

    def run_game():
        lock_copy = Lock(lock.level.copy())
        game = Game(screen, lock_copy, random_moves=args.random_moves)
        game.run()

    pygame.init()
    pygame.display.set_caption("LockPicker")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    if args.edit:
        editor = Editor(screen, lock, path, run_game)
        editor.run()
    else:
        run_game()

    pygame.quit()


if __name__ == "__main__":
    main()
