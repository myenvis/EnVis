# TODO: rename to Import
# TODO: move to module "commands"

import FreeCAD,os,EnVisProject

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui,QtCore

def translate(ctxt,txt):
    return txt

# ONEOF(IfcFlowFitting, IfcFlowSegment, IfcFlowController, IfcFlowTerminal, IfcFlowMovingDevice, IfcEnergyConversionDevice, IfcFlowStorageDevice, IfcFlowTreatmentDevice, IfcDistributionChamberElement)
# IfcDistributionControlElement
# IfcTransportElement
# IfcRamp
uselessElements = ["IfcFlowTerminal", "IfcSanitaryTerminal", "IfcFurniture", "IfcFurnishingElement", "IfcStairFlight", "IfcStair"]

class _CommandImport:
    def GetResources(self):
        """ Defines Menu as GUI element """
        return { #'Pixmap'  : 'Arch_Add',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("EnVis_Import","Import IFC file"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("EnVis_Import","Import IFC Elements useful for energy calculations")}

    def Activated(self):
        # TODO: separate import function
        import ifcopenshell,importIFC,SpaceBoundary
        from PySide import QtCore,QtGui

        self.filename = None
        lastfolder = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/EnVis").GetString("lastImportFolder","")
        filename = QtGui.QFileDialog.getOpenFileName(None,translate("EnVis","Select an IFC file"),lastfolder,translate("EnVis","IFC files (*.ifc)"))
        if filename:
            self.filename = filename[0]
            FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/EnVis").SetString("lastImportFolder",os.path.dirname(self.filename))

        if not os.path.exists(self.filename):
            FreeCAD.Console.PrintError(translate("EnVis","File not found")+"\n")
            return

        ifcfile = ifcopenshell.open(self.filename)
        if FreeCAD.ActiveDocument:
            docname = FreeCAD.ActiveDocument.Name
        else:
            docname = os.path.basename(self.filename)
        try:
            importIFC.insert(ifcfile, docname, skip=uselessElements, only=[e.id() for e in ifcfile.by_type("IfcBuilding")])
        except TypeError:
            importIFC.insert(self.filename, docname, skip=uselessElements, only=[e.id() for e in ifcfile.by_type("IfcBuilding")])

        p = FreeCAD.ActiveDocument.addObject("App::FeaturePython","EnVisProject")
        EnVisProject.EnVisProject(p)
        p.IFCFile = self.filename
#        p.Proxy.ifc = ifcfile

        sb = SpaceBoundary.SpaceBoundaries(self.filename)
        sb.show_all()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('EnVis_Import',_CommandImport())

# TODO: Unit Test with trivial import
