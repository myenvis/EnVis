# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""IFC importing tools."""

import os
import PySide.QtGui as QtGui
from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD as App
import FreeCADGui as Gui

from draftutils.messages import _wrn, _err
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
        lastfolder = param.GetString("lastImportFolder", "")
        _filename = QtGui.QFileDialog.getOpenFileName(None,
                                                      translate("EnVis", "Select an IFC file"),
                                                      lastfolder,
                                                      translate("EnVis", "IFC files (*.ifc)"))
        if _filename[0] == '' and _filename[1] == '':
            _wrn(translate("EnVis", "No file selected."))
            return

        if _filename:
            filename = _filename[0]
            param.SetString("lastImportFolder", os.path.dirname(filename))

        if not os.path.exists(filename):
            _err(translate("EnVis", "File not found"))
            return

        Gui.addModule('envis.functions.import_ifc')
        Gui.doCommand('import_ifc = envis.functions.import_ifc')
        Gui.doCommand('import_ifc.import_ifc(filename="{}")'.format(filename))


Gui.addCommand('EnVis_Import', Import())

# TODO: Unit Test with trivial import
