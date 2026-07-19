from contextlib import AbstractContextManager, contextmanager
from typing import Callable, Iterator, List, Tuple, TypeVar, Union

from bpy.types import Collection, Object, Scene

from locksmith.blender.objects import set_camera_ray_visibility

_Renderable = Union[Object, Collection]

_SubjectT = TypeVar("_SubjectT")
_ValueT = TypeVar("_ValueT")


@contextmanager
def _restored(
    subjects: Tuple[_SubjectT, ...],
    *,
    read: Callable[[_SubjectT], _ValueT],
    write: Callable[[_SubjectT, _ValueT], None],
    value: _ValueT,
) -> Iterator[None]:
    previous: List[_ValueT] = [read(subject) for subject in subjects]
    for subject in subjects:
        write(subject, value)
    try:
        yield
    finally:
        for subject, restored in zip(subjects, previous):
            write(subject, restored)


def _hide_render_of(subject: _Renderable) -> bool:
    return bool(subject.hide_render)


def _set_hide_render(subject: _Renderable, value: bool) -> None:
    subject.hide_render = value


def _camera_ray_of(instance: Object) -> bool:
    return bool(instance.visible_camera)


def _set_camera_ray(instance: Object, value: bool) -> None:
    set_camera_ray_visibility(instance, visible=value)


def rendered(*objects: _Renderable) -> AbstractContextManager[None]:
    return _restored(objects, read=_hide_render_of, write=_set_hide_render, value=False)


def hidden(*objects: _Renderable) -> AbstractContextManager[None]:
    return _restored(objects, read=_hide_render_of, write=_set_hide_render, value=True)


def camera_ray_visible(*objects: Object) -> AbstractContextManager[None]:
    return _restored(objects, read=_camera_ray_of, write=_set_camera_ray, value=True)


def camera_ray_hidden(*objects: Object) -> AbstractContextManager[None]:
    return _restored(objects, read=_camera_ray_of, write=_set_camera_ray, value=False)


@contextmanager
def film_transparent(scene: Scene, *, transparent: bool) -> Iterator[None]:
    previous = scene.render.film_transparent
    scene.render.film_transparent = transparent
    try:
        yield
    finally:
        scene.render.film_transparent = previous


@contextmanager
def world_disabled(scene: Scene) -> Iterator[None]:
    previous = scene.world
    scene.world = None
    try:
        yield
    finally:
        scene.world = previous
