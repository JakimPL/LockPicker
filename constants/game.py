from lock import Lock
from tumbler import Tumbler

TUMBLERS = [
    Tumbler(0, True, 0, 5),
    Tumbler(1, True, 0, 6),
    Tumbler(2, True, 0, 4, master=True),
    Tumbler(3, True, 1, 4),
    Tumbler(4, True, 1, 5),
    Tumbler(5, True, 1, 6, master=True),
    Tumbler(6, True, 2, 6),
    Tumbler(7, True, 2, 5),
    Tumbler(8, True, 2, 6, master=True),

    Tumbler(0, False, 0, 5),
    Tumbler(1, False, 0, 2),
    Tumbler(3, False, 1, 4),
    Tumbler(4, False, 1, 5),
    Tumbler(6, False, 2, 3),
    Tumbler(7, False, 2, 2)
]

RULES = {
    (0, True): [(0, False, 1)],
    (0, False): [(0, True, 3)],
    (1, True): [(0, False, 2)],
    (1, False): [(0, True, 2)],
    (3, True): [(7, False, 4)],
    (3, False): [(3, True, 3)],
    (4, True): [(4, False, -2)],
    (4, False): [(6, True, 2)],
    (6, True): [(6, False, 1)],
    (6, False): [(3, False, -1)],
    (7, True): [(8, True, 1)],
    (7, False): [(7, True, 3)]
}

LOCK = Lock(TUMBLERS, RULES)
