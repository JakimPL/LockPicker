import argparse
from pathlib import Path
from typing import Optional

from locksmith.assets.batch.pipeline import render_assets
from locksmith.assets.manifest.theme import MANIFEST_FILENAME, load_manifest
from locksmith.assets.preview import render_preview
from locksmith.blender.session import render_still, save_blend
from locksmith.builder import build_scene
from locksmith.paths import BLEND_OUTPUT_PATH, CONFIG_DIRECTORY, LOOKDEV_DIRECTORY, LOOKDEV_STILL_PATH, THEMES_DIRECTORY
from locksmith.schema.loader import load_scene_config
from locksmith.schema.models.scene import SceneConfig


class Arguments(argparse.Namespace):
    command: str
    config: Path
    blend: Path
    output: Optional[Path]
    theme: Optional[Path]
    still: Path


def _parse_arguments() -> Arguments:
    parser = argparse.ArgumentParser(prog="locksmith", description="LockPicker workshop scene and asset tooling")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_DIRECTORY,
        help="scene description directory of YAML fragments (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="build the scene and save the .blend")
    build.add_argument(
        "--blend",
        type=Path,
        default=BLEND_OUTPUT_PATH,
        help="blend file destination (default: %(default)s)",
    )

    still = subparsers.add_parser("still", help="build the scene and render the look-dev board still")
    still.add_argument(
        "--output",
        type=Path,
        default=LOOKDEV_STILL_PATH,
        help="still destination (default: %(default)s)",
    )

    assets = subparsers.add_parser("assets", help="render the theme sprites and write the manifest")
    assets.add_argument(
        "--output",
        type=Path,
        default=None,
        help="theme directory to write (default: assets/themes/<theme>)",
    )

    preview = subparsers.add_parser("preview", help="composite the look-dev arrangement from rendered sprites")
    preview.add_argument(
        "--theme",
        type=Path,
        default=None,
        help="theme directory to read (default: assets/themes/<theme>)",
    )
    preview.add_argument(
        "--still",
        type=Path,
        default=LOOKDEV_STILL_PATH,
        help="approved still the parity composite is compared against (default: %(default)s)",
    )

    return parser.parse_args(namespace=Arguments())


def _theme_directory(override: Optional[Path], *, config: SceneConfig) -> Path:
    return override if override is not None else THEMES_DIRECTORY / config.assets.theme


def main() -> None:
    arguments = _parse_arguments()
    config = load_scene_config(arguments.config)
    match arguments.command:
        case "build":
            build_scene(config)
            save_blend(arguments.blend)
            print(f"saved: {arguments.blend}")
        case "still":
            workshop = build_scene(config)
            output = arguments.output if arguments.output is not None else LOOKDEV_STILL_PATH
            render_still(workshop.scene, output)
            print(f"rendered: {output}")
        case "assets":
            directory = _theme_directory(arguments.output, config=config)
            workshop = build_scene(config)
            render_assets(workshop, config=config, directory=directory)
            print(f"manifest: {directory / MANIFEST_FILENAME}")
        case "preview":
            directory = _theme_directory(arguments.theme, config=config)
            manifest = load_manifest(directory / MANIFEST_FILENAME)
            result = render_preview(
                manifest,
                config=config,
                theme_directory=directory,
                output_directory=LOOKDEV_DIRECTORY,
                still_path=arguments.still,
            )
            print(f"preview: {result.preview_path}")
            if result.metrics is None:
                print(f"no comparison reference at {arguments.still}")
            else:
                print(
                    f"vs {arguments.still.name}: mean |diff| {result.metrics.mean_absolute:.4f}, "
                    f"max {result.metrics.max_absolute}, "
                    f">2/255 on {result.metrics.noticeable_fraction:.4%} of compared pixels"
                )


if __name__ == "__main__":
    main()
