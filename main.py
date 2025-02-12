import argparse
from pathlib import Path

import pygame

from lockpicker.constants.gui import HEIGHT, WIDTH
from lockpicker.game.editor import Editor
from lockpicker.game.game import Game
from lockpicker.lock import Level, Lock


def load_level(path: Path) -> Level:
    if path.exists() and path.is_file():
        return Level.load(path)
    else:
        return Level.default()


def main():
    parser = argparse.ArgumentParser(description="Load a level from a file.")
    parser.add_argument("level_file", type=str, help="Path to the level file")
    parser.add_argument("--edit", action="store_true", help="Run the level editor")
    args = parser.parse_args()
    path = Path(args.level_file)
    lock = Lock(load_level(path))

    def run_game():
        lock_copy = Lock(lock.level.copy())
        game = Game(screen, lock_copy)
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
