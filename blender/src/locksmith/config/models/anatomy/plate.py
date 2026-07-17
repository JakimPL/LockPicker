from locksmith.config.models.base import SceneModel


class PlateAnatomy(SceneModel):
    """Front housing plate with one boolean-cut slot per column.

    `subdivision_cuts` densifies the plate faces before the boolean so
    pointiness-driven shading stays local to the slot rims; on a plate whose
    only vertices sit on those rims, pointiness interpolates across the whole
    face and the entire plate reads as a worn edge.

    The plate spans the slot columns plus `bezel` on each side; the wooden
    bench panels fill the rest of the board. `margin` still stretches it
    vertically past the visible board so full-travel pins bake inside its
    emission field.

    `rebate_depth` sinks the whole slot bed behind the bezel so the thin
    rails between columns fall into the material's depth fade — at full
    plate emission a 5 px rail between two dark channels reads as a glowing
    wire. `rebate_margin` opens the rebate slightly past the outer slots.
    """

    margin: float
    bezel: float
    rebate_depth: float
    rebate_margin: float
    face_y: float
    back_y: float
    subdivision_cuts: int
    slot_clearance: float
    cutter_depth_margin: float
    cutter_height_margin: float
