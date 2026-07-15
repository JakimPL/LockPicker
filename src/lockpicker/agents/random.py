from tqdm import tqdm

from lockpicker.constants.config import settings
from lockpicker.lock import Lock


def play_random_games(
    lock: Lock,
    games: int = settings.simulation.games,
    max_moves: int = settings.simulation.max_moves,
) -> bool:
    for _ in tqdm(range(games)):
        lock.reset()
        for _ in range(max_moves):
            lock.play_random_move()
            if lock.check_win():
                return True

    return False
