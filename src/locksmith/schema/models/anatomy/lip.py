from locksmith.schema.models.anatomy.bevel import EdgeBevel
from locksmith.schema.models.base import SceneModel


class LipAnatomy(SceneModel):
    """Polished shear lip crossing the slots at the first height line.

    The bar is built z-centered on its object origin and the builder places
    that origin exactly on the shear line, so the sprite anchor publishes the
    line row; the beveled long edges catch the key sun as the polished-wear
    highlight.
    """

    thickness_pixels: float
    face_y: float
    depth: float
    bevel: EdgeBevel
