from locksmith.schema.models.base import SceneModel


class PlateAnatomy(SceneModel):
    """Front housing plate with one boolean-cut slot per column.

    `subdivision_cuts` densifies the plate faces before the boolean so
    pointiness-driven shading stays local to the slot rims; on a plate whose
    only vertices sit on those rims, pointiness interpolates across the whole
    face and the entire plate reads as a worn edge.

    The plate spans the slot columns plus a slim symmetric bezel on each
    side, so the pocket reads as a whole number of columns; the wooden
    bench panels fill the rest of the board on both flanks. `margin` still
    stretches the plate vertically past the visible board so full-travel
    pins bake inside its emission field.

    `chamber_depth` sinks everything between the shear lines into the depth
    fade, leaving the shell face proud only on the first-height-unit bands,
    so each column reads as a pocket in the shell and the middle reads as
    the open raceway, cut through both bezels — the mechanism passes the
    case on either side rather than dead-ending in it.

    `countersink_width`/`countersink_depth` bevel the front vertical edges of
    each slot: a second cutter widens the mouth by `countersink_width` on
    each side at the plate face and tapers back to the bore over
    `countersink_depth`, so every hole reads as a real drilled countersink —
    a machined shoulder graded by the depth fade — instead of a knife-sharp
    slot edge with a bare pointiness glint. Sized so neighbouring
    countersinks leave a slim flat land between them.
    """

    margin: float
    bezel_left: float
    bezel_right: float
    chamber_depth: float
    face_y: float
    back_y: float
    subdivision_cuts: int
    slot_clearance: float
    land_inset: float
    cutter_depth_margin: float
    cutter_height_margin: float
    countersink_width: float
    countersink_depth: float
