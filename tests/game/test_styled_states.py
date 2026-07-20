from __future__ import annotations

import pygame
import pytest

from lockpicker.constants.config import RendererMode, settings
from lockpicker.engine.lock import Lock
from lockpicker.game.assets.library import AssetLibrary
from lockpicker.game.assets.sprites import ThemeSprites
from lockpicker.game.game import Game
from lockpicker.game.layout import Layout


@pytest.fixture
def sprites(screen: pygame.surface.Surface) -> ThemeSprites:
    library = AssetLibrary.load()
    return ThemeSprites(library, Layout(settings.rules.default_max_height))


def average_brightness(surface: pygame.surface.Surface) -> int:
    color = pygame.transform.average_color(surface)
    return color[0] + color[1] + color[2]


def render_bytes(game: Game) -> bytes:
    game.draw()
    return pygame.image.tobytes(game.screen, "RGB")


def test_tumbler_state_variants_shift_brightness(sprites: ThemeSprites) -> None:
    for upper in (True, False):
        for group in range(len(settings.color.tumblers)):
            base = sprites.tumbler(group, upper=upper, highlighted=False, jammed=False)
            hover = sprites.tumbler(group, upper=upper, highlighted=True, jammed=False)
            jammed = sprites.tumbler(group, upper=upper, highlighted=False, jammed=True)
            assert average_brightness(hover.surface) > average_brightness(base.surface)
            assert average_brightness(jammed.surface) < average_brightness(base.surface)
            assert base.anchor == hover.anchor == jammed.anchor


def test_faded_tumbler_variant_is_cached(sprites: ThemeSprites) -> None:
    faded = sprites.tumbler(0, upper=True, highlighted=False, jammed=False, alpha=settings.alpha.faint)
    again = sprites.tumbler(0, upper=True, highlighted=False, jammed=False, alpha=settings.alpha.faint)
    base = sprites.tumbler(0, upper=True, highlighted=False, jammed=False)
    assert faded is again
    assert faded.surface.get_alpha() == settings.alpha.faint
    assert faded.surface is not base.surface
    assert faded.anchor == base.anchor


def test_shadow_and_badge_prescaled(sprites: ThemeSprites) -> None:
    for upper in (True, False):
        shadow = sprites.shadow(upper=upper)
        assert shadow.surface.get_alpha() == settings.theme.shadow_alpha
        assert shadow.surface.get_width() > 0

    assert sprites.badge.surface.get_alpha() == settings.theme.badge_alpha
    assert sprites.badge_offset > 0


def test_lip_strips_prescaled_to_screen_width(sprites: ThemeSprites) -> None:
    layout = Layout(settings.rules.default_max_height)
    for upper in (True, False):
        lip = sprites.lip(upper=upper)
        assert lip.surface.get_width() == layout.screen_width
        assert 0 <= lip.anchor[1] <= lip.surface.get_height()


def test_lip_glint_variant_brighter_than_base(sprites: ThemeSprites) -> None:
    for upper in (True, False):
        base = sprites.lip(upper=upper)
        glint = sprites.lip_glint(upper=upper)
        assert average_brightness(glint.surface) > average_brightness(base.surface)
        assert glint.anchor == base.anchor
        assert glint.surface.get_size() == base.surface.get_size()


def test_shear_lines_brighter_than_chamber(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
) -> None:
    game = Game(screen, sample_lock, renderer_mode=RendererMode.STYLED)
    game.draw()
    layout = game.layout
    for upper in (True, False):
        line_y = layout.shear_line_y(upper=upper)
        inward = 20 if upper else -20
        line_band = screen.subsurface((0, line_y - 2, layout.screen_width // 8, 4))
        chamber_band = screen.subsurface((0, line_y + inward - 2, layout.screen_width // 8, 4))
        assert average_brightness(line_band) > average_brightness(chamber_band)


def test_pick_idle_variant_dimmed(sprites: ThemeSprites) -> None:
    for shape in set(settings.pick.shapes):
        active = sprites.pick(shape, active=True)
        idle = sprites.pick(shape, active=False)
        assert idle.surface.get_alpha() == settings.theme.pick_idle_alpha
        assert average_brightness(active.surface) > average_brightness(idle.surface)
        assert idle.surface is not active.surface
        assert idle.anchor == active.anchor


def test_styled_states_change_rendered_output(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
) -> None:
    game = Game(screen, sample_lock, renderer_mode=RendererMode.STYLED)
    tumbler = next(iter(sample_lock.get_tumblers_by_location().values()))
    baseline = render_bytes(game)

    tumbler.set_master(True)
    with_badge = render_bytes(game)
    assert with_badge != baseline

    tumbler.jam()
    jammed = render_bytes(game)
    assert jammed != with_badge


def test_styled_pick_switch_changes_output(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
) -> None:
    game = Game(screen, sample_lock, renderer_mode=RendererMode.STYLED)
    if sample_lock.level.number_of_picks < 2:
        pytest.skip("level has a single pick")

    baseline = render_bytes(game)
    sample_lock.change_current_pick()
    switched = render_bytes(game)
    assert switched != baseline


def test_glint_changes_output_and_decays_to_baseline(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
) -> None:
    game = Game(screen, sample_lock, renderer_mode=RendererMode.STYLED)
    baseline = render_bytes(game)

    location = next(iter(sample_lock.get_tumblers_by_location()))
    game.effects.observe(location, 2.0)
    game.effects.observe(location, 1.0)
    assert render_bytes(game) != baseline

    for _ in range(settings.theme.lip_glint_frames):
        game.effects.advance()

    assert render_bytes(game) == baseline


def test_flourish_changes_output(
    screen: pygame.surface.Surface,
    sample_lock: Lock,
) -> None:
    game = Game(screen, sample_lock, renderer_mode=RendererMode.STYLED)
    baseline = render_bytes(game)

    game.effects.start_flourish()
    for _ in range(settings.theme.win_flourish_frames // 2):
        game.effects.advance()

    assert render_bytes(game) != baseline
