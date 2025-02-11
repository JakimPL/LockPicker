import pygame

from constants.game import LOCK
from constants.gui import WIDTH, HEIGHT, BACKGROUND_COLOR
from gui import draw_tumbler, draw_pick

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LockPicker")

running = True
mouse_was_pressed = (False, False, False)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND_COLOR)

    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()

    position_highlighted = None
    for position, items in LOCK.positions.items():
        for upper, item in items.items():
            if item is not None:
                highlighted = draw_tumbler(item, position, screen, mouse_pos)
                if highlighted:
                    position_highlighted = position, upper

    if mouse_pressed[0] and not mouse_was_pressed[0]:
        if position_highlighted is not None:
            LOCK.release()
            LOCK.push(*position_highlighted)
        else:
            LOCK.release()

    if mouse_pressed[2] and not mouse_was_pressed[2]:
        LOCK.current_pick = 1 - LOCK.current_pick

    for pick in LOCK.picks:
        draw_pick(LOCK, pick, screen)

    mouse_was_pressed = mouse_pressed

    pygame.display.flip()

pygame.quit()
