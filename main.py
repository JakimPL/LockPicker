import argparse

from lockpicker.game.game import Game
from lockpicker.lock import Level, Lock


def main():
    parser = argparse.ArgumentParser(description="Load a level from a file.")
    parser.add_argument("level_file", type=str, help="Path to the level file")
    args = parser.parse_args()

    level = Level.load(args.level_file)
    lock = Lock(level)
    game = Game(lock)
    game.run()


if __name__ == "__main__":
    main()
