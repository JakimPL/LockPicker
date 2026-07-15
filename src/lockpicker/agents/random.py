import random

from tqdm import tqdm

from lockpicker.constants.config import settings
from lockpicker.lock import Lock


class RandomAgent:
    def __init__(self, lock: Lock) -> None:
        self._lock = lock

    def play_move(self) -> None:
        moves = self._lock.get_possible_moves()
        if moves:
            move = random.choice(moves)
            pick = random.choice(range(self._lock.level.number_of_picks))
            self._lock.select_pick(pick)
            self._lock.push(move)


def play_random_games(
    lock: Lock,
    *,
    games: int = settings.simulation.games,
    max_moves: int = settings.simulation.max_moves,
) -> bool:
    agent = RandomAgent(lock)
    for _ in tqdm(range(games)):
        lock.reset()
        for _ in range(max_moves):
            agent.play_move()
            if lock.check_win():
                return True

    return False
