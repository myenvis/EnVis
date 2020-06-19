import FreeCAD,os

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
        return { #'Pixmap'  : 'Arch_Add',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("EnPlan_Import","Import IFC file"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("EnPlan_Import","Import IFC Elements useful for energy calculations")}

    def Activated(self):
        import ifcopenshell,importIFC,SpaceBoundary
        from PySide import QtCore,QtGui

        self.filename = None
        lastfolder = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/EnPlan").GetString("lastImportFolder","")
        filename = QtGui.QFileDialog.getOpenFileName(None,translate("EnPlan","Select an IFC file"),lastfolder,translate("EnPlan","IFC files (*.ifc)"))
        if filename:
            self.filename = filename[0]
            FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/EnPlan").SetString("lastImportFolder",os.path.dirname(self.filename))

        if not os.path.exists(self.filename):
            FreeCAD.Console.PrintError(translate("EnPlan","File not found")+"\n")
            return

        ifcfile = ifcopenshell.open(self.filename)
        if FreeCAD.ActiveDocument:
            docname = FreeCAD.ActiveDocument.Name
        else:
            docname = os.path.basename(self.filename)
        try:
            importIFC.insert(ifcfile, docname, skip=uselessElements, only=[e.id() for e in ifcfile.by_type("IfcBuilding")])
        except TypeError:
            importIFC.insert(self.filename, docname, skip=uselessElements)
        sb = SpaceBoundary.SpaceBoundaries(self.filename)
        sb.show_all()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('EnPlan_Import',_CommandImport())
