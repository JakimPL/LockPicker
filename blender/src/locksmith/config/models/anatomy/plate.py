from locksmith.config.models.base import SceneModel


class PlateAnatomy(SceneModel):
    """Front housing plate with one boolean-cut slot per column.

    `subdivision_cuts` densifies the plate faces before the boolean so
    pointiness-driven shading stays local to the slot rims; on a plate whose
    only vertices sit on those rims, pointiness interpolates across the whole
    face and the entire plate reads as a worn edge.
    """

    margin: float
    face_y: float
    back_y: float
    subdivision_cuts: int
    slot_clearance: float
    cutter_depth_margin: float
    cutter_height_margin: float
