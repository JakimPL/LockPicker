import argparse
from pathlib import Path

from locksmith.blender.session import render_still, save_blend
from locksmith.builder import build_scene
from locksmith.config.loader import load_scene_config
from paths import BLEND_OUTPUT_PATH, CONFIG_DIRECTORY, LOOKDEV_STILL_PATH


class Arguments(argparse.Namespace):
    config: Path
    render: bool
    output: Path


def _parse_arguments() -> Arguments:
    parser = argparse.ArgumentParser(prog="locksmith", description="Build the LockPicker workshop scene")
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_DIRECTORY,
        help="scene description directory of YAML fragments (default: %(default)s)",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="render the look-dev board still after building",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=LOOKDEV_STILL_PATH,
        help="look-dev still destination (default: %(default)s)",
    )
    return parser.parse_args(namespace=Arguments())


def main() -> None:
    arguments = _parse_arguments()
    config = load_scene_config(arguments.config)
    scene = build_scene(config)
    save_blend(BLEND_OUTPUT_PATH)
    print(f"saved: {BLEND_OUTPUT_PATH}")
    if arguments.render:
        render_still(scene, arguments.output)
        print(f"rendered: {arguments.output}")


if __name__ == "__main__":
    main()
