# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Functions to make a BruttoFace object."""

import FreeCAD as App

from envis.objects.bruttoface import BruttoFace
from envis.viewproviders.v_bruttoface import ViewBruttoFace


def faceFromLinkSub(prop):
    """Return tuple id, faceidx.

    TODO: this function probably could be moved to a helper module
    because it only provides support but doesn't actually do something
    special with BruttoFaces.
    """
    return prop[0], int(prop[1][0][4:]) - 1  # string "faceX"


def make_bruttoface(space_boundary, other_space, BaseFace=None, doc=None):
    """Create a BruttoFace object."""
    if not doc:
        doc = App.activeDocument()

    obj = doc.addObject("Part::FeaturePython",
                        "BruttoFace" + space_boundary.Name)
    BruttoFace(obj)

    obj.Space = space_boundary.Space
    obj.Space2 = other_space
    obj.SpaceBoundary = space_boundary

    if BaseFace:
        obj.BaseFace = BaseFace
    else:
        obj.BaseFace = space_boundary.BaseFace

    if obj.BaseFace:
        parent, face = faceFromLinkSub(obj.BaseFace)
        obj.Shape = parent.Shape.Faces[face]
        obj.Placement = parent.Shape.Faces[face].Placement

    if App.GuiUp:
        ViewBruttoFace(obj.ViewObject)

    return obj
