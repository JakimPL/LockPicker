from __future__ import annotations

import pytest
from lockpicker.game.assets.library import theme_directory, validate_manifest
from lockpicker.game.assets.manifest import ThemeManifest, load_manifest
from lockpicker.game.assets.sprites import scaled_pair


@pytest.fixture
def manifest() -> ThemeManifest:
    return load_manifest(theme_directory())


def test_manifest_is_valid_against_config(manifest: ThemeManifest) -> None:
    assert manifest.schema_version == 1
    assert manifest.image_scale >= 1
    validate_manifest(manifest)


def test_manifest_anchors_inside_canvas(manifest: ThemeManifest) -> None:
    sprites = [manifest.tumblers.upper, manifest.tumblers.lower, *manifest.picks.values()]
    for sprite in sprites:
        assert 0 <= sprite.tip_anchor[0] < sprite.size[0]
        assert 0 <= sprite.tip_anchor[1] < sprite.size[1]


def test_manifest_groups_cover_both_orientations(manifest: ThemeManifest) -> None:
    for orientation in (manifest.tumblers.upper, manifest.tumblers.lower):
        assert set(orientation.images) == set(manifest.tumblers.groups)


def test_validate_manifest_rejects_group_mismatch(manifest: ThemeManifest) -> None:
    tumblers = manifest.tumblers.model_copy(update={"groups": manifest.tumblers.groups[:-1]})
    broken = manifest.model_copy(update={"tumblers": tumblers})
    with pytest.raises(ValueError, match="groups"):
        validate_manifest(broken)


def test_validate_manifest_rejects_board_size_mismatch(manifest: ThemeManifest) -> None:
    board = manifest.board.model_copy(update={"logical_size": (1, 1)})
    broken = manifest.model_copy(update={"board": board})
    with pytest.raises(ValueError, match="board size"):
        validate_manifest(broken)


def test_validate_manifest_rejects_missing_pick_shapes(manifest: ThemeManifest) -> None:
    broken = manifest.model_copy(update={"picks": {}})
    with pytest.raises(ValueError, match="pick shapes"):
        validate_manifest(broken)


def test_scaled_pair_rounds_each_axis_independently() -> None:
    assert scaled_pair((88, 800), scale_x=1.0, scale_y=795 / 11 / 72) == (88, 803)
    assert scaled_pair((44, 796), scale_x=0.5, scale_y=1.0) == (22, 796)
    assert scaled_pair((29, -11), scale_x=1.0, scale_y=1.0) == (29, -11)
