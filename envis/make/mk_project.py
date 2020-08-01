# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Functions to make the main project object."""

import FreeCAD as App

from envis.objects.project import Project
from envis.viewproviders.v_project import ViewProject


def make_project(filename=""):
    """Create a main project."""
    doc = App.ActiveDocument
    new_obj = doc.addObject("App::FeaturePython", "EnVisProject")
    Project(new_obj)

    new_obj.IFCFile = filename
    # new_obj.Proxy.ifc = ifcfile

    if App.GuiUp:
        ViewProject(new_obj.ViewObject)

    return new_obj
