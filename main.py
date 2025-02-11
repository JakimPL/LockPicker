from constants.levels import LEVEL
from game import Game
from lock import Lock

lock = Lock(LEVEL)
game = Game(lock)
game.run()
