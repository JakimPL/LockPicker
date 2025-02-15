from tqdm import tqdm

from lockpicker.lock import Lock

GAMES = 1000
MAX_MOVES = 100


def play_random_games(lock: Lock, games: int = GAMES, max_moves: int = MAX_MOVES) -> bool:
    for _ in tqdm(range(games)):
        lock.reset()
        for _ in range(max_moves):
            lock.play_random_move()
            if lock.check_win():
                return True

    return False
