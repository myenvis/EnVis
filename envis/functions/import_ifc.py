# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Non-GUI IFC importing functions."""

import os
import ifcopenshell

import FreeCAD as App
import importIFC
import ArchWindow
import envis.functions.spaceboundaries
import envis.helpers.helper as helper
import envis.make.mk_project as mk_project

# TODO: check the import rules of Python 3.
# This doesn't work and I don't understand why
# import envis.functions.spaceboundaries as spaceboundaries
#
# This works but I don't like it
# from envis.functions import spaceboundaries
#
# Maybe it's because we use a class from `spaceboundaries` instead
# of a function.
# As noted in `spaceboundaries`, I prefer (Eliud) if it's a function
# instead of a class.

uselessElements = ["IfcFlowTerminal", "IfcSanitaryTerminal",
                   "IfcFurniture", "IfcFurnishingElement",
                   "IfcStairFlight", "IfcStair"]


def process_file(doc=None, filename=None):
    """Process a filename in the current document or create a new one."""
    if not doc:
        doc = App.activeDocument()

    ifcfile = ifcopenshell.open(filename)

    if doc:
        docname = doc.Name
    else:
        docname = os.path.basename(filename)

    main_types = ifcfile.by_type("IfcBuilding") + ifcfile.by_type("IfcVirtualElement")
    only_elements = [e.id() for e in main_types]

    try:
        importIFC.insert(ifcfile, docname,
                         skip=uselessElements, only=only_elements)
        # importIFC.insert(ifcfile, doc.Name, root="IfcVirtualElement")
    except TypeError:
        importIFC.insert(filename, docname,
                         skip=uselessElements, only=only_elements)

    # The importIFC.insert function creates a new document is none existed,
    # so we capture it
    doc = App.activeDocument()
    all_windows = filter(lambda o: hasattr(o, "Proxy") and type(o.Proxy) == ArchWindow._Window, doc.Objects)

    # Arch and Draft objects have a "Type", so this can be done as well
    # filter(lambda o: Draft.get_type(o) == "Window", doc.Objects)

    for window in all_windows:
        ifc_window = ifcfile.by_guid(window.GlobalId)
        ifc_wall = ifc_window.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
        wall = helper.get_object_by_guid(doc, ifc_wall.GlobalId)
        window.Hosts = [wall]

    return ifcfile, filename


def import_ifc(doc=None, filename=None):
    """Import an IFC file, create a Project, and SpaceBoundaries."""
    ifcfile, filename = process_file(doc=doc, filename=filename)

    mk_project.make_project(filename)

    # TODO: review creating the space boundaries objects.
    # Eliud: I find this confusing because this creates a class
    # to show something?
    # Is this supposed to be persistent? If it is, then it should be
    # a document object, not a class.
    sb = envis.functions.spaceboundaries.SpaceBoundaries(filename)
    sb.show_all()
