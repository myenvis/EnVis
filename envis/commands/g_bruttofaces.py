# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Brutto faces tools."""
import os
from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD as App
import FreeCADGui as Gui


class BruttoFlache:
    """Creation of the Bruttoface model."""

    def GetResources(self):
        dirn = os.path.dirname(os.path.dirname(__file__))
        icon = os.path.join(dirn, 'resources', 'EnVis_bruttoface.svg')

        return {'Pixmap': icon,
                'MenuText': QT_TRANSLATE_NOOP("EnVis_BruttoFlache",
                                              "Bruttoflächen erzeugen"),
                'ToolTip': QT_TRANSLATE_NOOP("EnVis_BruttoFlache",
                                             "Erzeugt das Flächenmodell aus SpaceBoundaries")}

    def IsActive(self):
        doc = App.ActiveDocument
        return doc and hasattr(doc, "EnVisProject")

    def Activated(self):
        layer = App.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")[0]
        Gui.addModule("envis.functions.bruttofacemodel")
        Gui.doCommand("bruttofacemodel = envis.functions.bruttofacemodel")
        Gui.doCommand("_layer_ = App.ActiveDocument." + layer.Name)
        Gui.doCommand("bruttofacemodel.createModel(_layer_)")


Gui.addCommand('EnVis_BruttoFl', BruttoFlache())
