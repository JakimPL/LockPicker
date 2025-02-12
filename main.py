import argparse

from game import Game
from lock import Lock, Level


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
