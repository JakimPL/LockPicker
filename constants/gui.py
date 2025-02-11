from constants.game import LOCK

WIDTH, HEIGHT = 1000, 800
X_OFFSET = 150
BAR_WIDTH = 80
BAR_OFFSET = 5
SCALE = HEIGHT / LOCK.max_height

PICK_SIZE = 20
PICK_OFFSET = 20
PICK_WIDTH = 6
PICK_IDLE_OFFSET = 80
PICK_DISCREPANCY = 40

HIGHLIGHT_COLOR = (0xFF, 0xFF, 0xFF)
BACKGROUND_COLOR = (0x20, 0x20, 0x20)
TUMBLERS_COLORS = [
    (0x80, 0x80, 0x80),
    (0xC0, 0xC0, 0x40),
    (0xC0, 0x40, 0x40)
]

PICK_COLORS = [
    (0xC0, 0xD0, 0xC0),
    (0xD0, 0xC0, 0xC0)
]

ANIMATION_SPEED = 0.05
