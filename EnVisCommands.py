# TODO: rename to EnVisImport

import os

import FreeCAD
import envis.objects.project as project
import envis.helpers.helper as helper

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
        import ArchWindow
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
            importIFC.insert(ifcfile, docname, skip=uselessElements, only=[e.id() for e in ifcfile.by_type("IfcBuilding") + ifcfile.by_type("IfcVirtualElement")])
#            importIFC.insert(ifcfile, FreeCAD.ActiveDocument.Name, root="IfcVirtualElement")
        except TypeError:
            importIFC.insert(self.filename, docname, skip=uselessElements, only=[e.id() for e in ifcfile.by_type("IfcBuilding") + ifcfile.by_type("IfcVirtualElement")])

        doc = FreeCAD.ActiveDocument
        for window in filter(lambda o: hasattr(o, "Proxy") and type(o.Proxy) == ArchWindow._Window, doc.Objects):
            ifc_window = ifcfile.by_guid(window.GlobalId)
            ifc_wall = ifc_window.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
            wall = helper.get_object_by_guid(doc, ifc_wall.GlobalId)
            window.Hosts = [wall]
        p = FreeCAD.ActiveDocument.addObject("App::FeaturePython","EnVisProject")
        project.Project(p)
        p.IFCFile = self.filename
#        p.Proxy.ifc = ifcfile

        # TODO: review creating the space boundaries objects.
        # Eliud: I find this confusing because this creates a class
        # to show something? But this is inside a command that is called
        # from the press of a button or menu.
        # Is this supposed to be persistent? What does it do?
        sb = SpaceBoundary.SpaceBoundaries(self.filename)
        sb.show_all()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('EnVis_Import',_CommandImport())

# TODO: Unit Test with trivial import
