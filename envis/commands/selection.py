# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Selection tools."""

from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCADGui as Gui


class SelectRelated:
    """Selection of dependent objects."""

    def GetResources(self):
        return {'Pixmap': 'tree-item-drag',
                'MenuText': QT_TRANSLATE_NOOP("EnVis_SelectRelated",
                                              "Select related"),
                'ToolTip': QT_TRANSLATE_NOOP("EnVis_SelectRelated",
                                             "Automatisch abhängige Objekte auswählen")}

    def IsActive(self):
        return bool(Gui.Selection.getSelection())

    def Activated(self):
        new_sel = list()
        for o in Gui.Selection.getSelection():
            new_sel.extend(o.InList)

        Gui.Selection.clearSelection()
        for o in new_sel:
            Gui.Selection.addSelection(o)


Gui.addCommand('EnVis_SelectRelated', SelectRelated())
