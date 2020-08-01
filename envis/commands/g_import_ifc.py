# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""IFC importing tools."""

import os
import ifcopenshell
import PySide.QtGui as QtGui
from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD as App
import FreeCADGui as Gui
import importIFC
import ArchWindow
import SpaceBoundary
import envis.helpers.helper as helper
import envis.make.mk_project as mk_project

from draftutils.messages import _err
from draftutils.translate import translate

# ONEOF(IfcFlowFitting, IfcFlowSegment, IfcFlowController, IfcFlowTerminal,
# IfcFlowMovingDevice, IfcEnergyConversionDevice, IfcFlowStorageDevice,
# IfcFlowTreatmentDevice, IfcDistributionChamberElement)
# IfcDistributionControlElement
# IfcTransportElement
# IfcRamp
uselessElements = ["IfcFlowTerminal", "IfcSanitaryTerminal",
                   "IfcFurniture", "IfcFurnishingElement",
                   "IfcStairFlight", "IfcStair"]

param = App.ParamGet("User parameter:BaseApp/Preferences/Mod/EnVis")


class Import:
    """Tool to import IFC files."""

    def GetResources(self):
        """Define icon, menu text, and tooltip in the GUI."""
        dirn = os.path.dirname(os.path.dirname(__file__))
        icon = os.path.join(dirn, 'resources', 'EnVis_ifc_open.svg')

        return {'Pixmap': icon,
                'MenuText': QT_TRANSLATE_NOOP("EnVis_Import",
                                              "Import IFC file"),
                'ToolTip': QT_TRANSLATE_NOOP("EnVis_Import",
                                             "Import IFC Elements useful for energy calculations")}

    def Activated(self):
        # TODO: separate import function
        doc = App.activeDocument()

        self.filename = None
        lastfolder = param.GetString("lastImportFolder", "")
        filename = QtGui.QFileDialog.getOpenFileName(None,
                                                     translate("EnVis","Select an IFC file"),
                                                     lastfolder,
                                                     translate("EnVis","IFC files (*.ifc)"))
        if filename:
            self.filename = filename[0]
            param.SetString("lastImportFolder",
                            os.path.dirname(self.filename))

        if not os.path.exists(self.filename):
            _err(translate("EnVis", "File not found"))
            return

        ifcfile = ifcopenshell.open(self.filename)

        if doc:
            docname = doc.Name
        else:
            docname = os.path.basename(self.filename)

        only_elements = [e.id() for e in ifcfile.by_type("IfcBuilding") + ifcfile.by_type("IfcVirtualElement")]

        try:
            importIFC.insert(ifcfile, docname,
                             skip=uselessElements, only=only_elements)
            # importIFC.insert(ifcfile, FreeCAD.ActiveDocument.Name, root="IfcVirtualElement")
        except TypeError:
            importIFC.insert(self.filename, docname,
                             skip=uselessElements, only=only_elements)

        doc = App.activeDocument()
        all_windows = filter(lambda o: hasattr(o, "Proxy") and type(o.Proxy) == ArchWindow._Window, doc.Objects)

        for window in all_windows:
            ifc_window = ifcfile.by_guid(window.GlobalId)
            ifc_wall = ifc_window.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
            wall = helper.get_object_by_guid(doc, ifc_wall.GlobalId)
            window.Hosts = [wall]

        _p_ = mk_project.make_project(self.filename)

        # TODO: review creating the space boundaries objects.
        # Eliud: I find this confusing because this creates a class
        # to show something? But this is inside a command that is called
        # from the press of a button or menu.
        # Is this supposed to be persistent? If it is, then it should be
        # a document object, not a class.
        sb = SpaceBoundary.SpaceBoundaries(self.filename)
        sb.show_all()


Gui.addCommand('EnVis_Import', Import())

# TODO: Unit Test with trivial import
