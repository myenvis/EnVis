# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Functions to make the spaceboundary object."""

import FreeCAD as App

from envis.objects.spaceboundary import SpaceBoundary
from envis.viewproviders.v_spaceboundary import ViewSpaceBoundary


def make_spaceboundary(name,
                       space,
                       building_element,
                       shape,
                       sbrel):
    """Create the SpaceBoundary object."""
    if not name:
        name = "SpaceBoundary"

    new_obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
    SpaceBoundary(new_obj)

    if App.GuiUp:
        ViewSpaceBoundary(new_obj.ViewObject)

    new_obj.Space = space
    new_obj.BuildingElement = building_element

    if len(shape.Faces) == 1:
        new_obj.Shape = shape.Faces[0]
    else:
        print("SpaceBoundary has not exactly one face: ", sbrel)
        new_obj.Shape = shape

    if sbrel.PhysicalOrVirtualBoundary == 'PHYSICAL':
        green = 0.0
    else:
        green = 1.0

    new_obj.Internal = sbrel.InternalOrExternalBoundary == 'INTERNAL'

    if App.GuiUp and new_obj.Internal:
        new_obj.ViewObject.ShapeColor = (1.0, green, 0.0)
    else:
        new_obj.ViewObject.ShapeColor = (0.0, green, 1.0)

    return new_obj
