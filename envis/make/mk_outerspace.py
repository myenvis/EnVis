# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Functions to make an outer space object."""
import FreeCAD as App

from envis.objects.outerspace import OuterSpace


def add_outer_space(base_obj, doc):
    """Add an OuterSpace object."""
    if hasattr(base_obj, "Name"):
        name = "Auszenraum_" + base_obj.Name
    else:
        name = "Auszenraum_Luft_" + str(base_obj)

    obj = doc.addObject("App::FeaturePython", name)
    OuterSpace(obj)

    if App.GuiUp:
        obj.ViewObject.Proxy = 0

    if hasattr(base_obj, "Name"):
        obj.BaseObject = base_obj
    else:
        obj.Angle = base_obj

    outer_spaces = doc.getObject("EnVisOuterSpaces")

    lst = outer_spaces.Group
    lst.append(obj)
    outer_spaces.Group = lst

    return obj


def get_outer_space(obj, doc=None):
    """Get an OuterSpaces object from the OuterSpaces group.

    Create the OuterSpaces group if it doesn't exist.
    """
    if not doc:
        doc = App.activeDocument()

    if not hasattr(doc, "EnVisOuterSpaces"):
        doc.addObject("App::DocumentObjectGroup", "EnVisOuterSpaces")
        return add_outer_space(obj, doc)

    # What does this do?
    # In both cases it runs the loop, so it's better to place the loop outside.
    # In both cases it returns the object in the loop, so we can test
    # both cases at the same time
    # ========================================================================
    # if hasattr(obj, "Name"):
    #     for o in doc.EnVisOuterSpaces.Group:
    #         if o.BaseObject == obj:
    #             return o
    # else:
    #     for o in doc.EnVisOuterSpaces.Group:
    #         if o.BaseObject is None and o.Angle == obj:
    #             return o
    # ========================================================================

    outer_spaces = doc.getObject("EnVisOuterSpaces")

    # In one case the obj has a 'Name', in the other case, it's an angle?
    # That seems a bit strange to handle with the same variable.
    # Maybe it would be better to use two different input variables
    # to this function, which are set appropriately by whatever function
    # calls this.
    #
    # get_outer_spaces(obj=None, angle=None, doc=None)
    #
    # if ((not angle and hassatr(obj, "Name") and o.BaseObject == obj)
    #         or
    #         (not obj and o.BaseObject is None and o.Angle == angle)):
    #     return o

    for o in outer_spaces.Group:
        if ((hasattr(obj, "Name") and o.BaseObject == obj)
                or
                (o.BaseObject is None and o.Angle == obj)):
            return o

    return add_outer_space(obj, doc)
