# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Initialization of EnVis workbench."""
from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD as App
import FreeCADGui as Gui

from draftutils.messages import _log


class EnVisWorkbench(Gui.Workbench):

    def __init__(self):
        self.__class__.MenuText = "EnVis"
        self.__class__.ToolTip = "Energy planning workbench"
        self.__class__.Icon = ":/icons/IFC.svg"

    def Initialize(self):
        from PySide.QtCore import QT_TRANSLATE_NOOP

        import DraftTools
        import Arch
        import envis.commands

        from draftutils.messages import _log

        try:
            Gui.activateWorkbench("BIMWorkbench")
        except KeyError:
            print("BIM Workbench not available. Some commands will be missing.")

        self.draftingtools = ["BIM_Sketch","Draft_Line","Draft_Wire","Draft_Circle",
                              "Draft_Arc","Draft_Arc_3Points","Draft_Ellipse",
                              "Draft_Polygon","Draft_Rectangle","Draft_Point"]

        self.annotationtools = ["Draft_Text", "Draft_ShapeString", "Draft_Dimension",
                                "Draft_Label","Arch_Axis","Arch_AxisSystem","Arch_Grid",
                                "Arch_SectionPlane"]

        self.bimtools = ["Arch_Site","Arch_Building","Arch_Floor","Arch_Space","Separator",
                         "Arch_Wall","BIM_Slab","BIM_Door","Arch_Window",
                         "Arch_Roof","Arch_Panel","Arch_Frame",
                         "Separator","BIM_Box","Draft_Facebinder","BIM_Library","Arch_Component"]

        self.modify = ["Draft_Move","BIM_Copy","Draft_Rotate","BIM_Clone","BIM_Unclone","Draft_Offset",
                       "BIM_Offset2D", "Draft_Trimex","Draft_Join","Draft_Split","Draft_Scale","Draft_Stretch",
                       "BIM_Rewire","BIM_Glue","Draft_Upgrade", "Draft_Downgrade",
                       "Draft_Draft2Sketch","Arch_CutPlane","Arch_Add","Arch_Remove","BIM_Reextrude",
                       "BIM_Cut","Draft_Shape2DView"]

        self.snap = ['Draft_ToggleGrid','Draft_Snap_Lock','Draft_Snap_Midpoint','Draft_Snap_Perpendicular',
                     'Draft_Snap_Grid','Draft_Snap_Intersection','Draft_Snap_Parallel',
                     'Draft_Snap_Endpoint','Draft_Snap_Angle','Draft_Snap_Center',
                     'Draft_Snap_Extension','Draft_Snap_Near','Draft_Snap_Ortho',
                     'Draft_Snap_Special','Draft_Snap_Dimensions','Draft_Snap_WorkingPlane',
                     'BIM_SetWPTop','BIM_SetWPFront','BIM_SetWPSide']

        self.manage = ["BIM_Setup","BIM_Project","BIM_Views","BIM_Windows","BIM_IfcElements",
                       "BIM_IfcQuantities","BIM_IfcProperties","BIM_Classification",
                       "BIM_Material","Arch_Schedule","BIM_Preflight","BIM_Layers"]

        self.utils = ["BIM_TogglePanels","BIM_Trash","BIM_WPView",
                      "Draft_Slope", "Draft_WorkingPlaneProxy", "Draft_AddConstruction",
                      "Arch_SplitMesh","Arch_MeshToShape",
                      "Arch_SelectNonSolidMeshes","Arch_RemoveShape",
                      "Arch_CloseHoles","Arch_MergeWalls","Arch_Check",
                      "Arch_ToggleIfcBrepFlag",
                      "Arch_ToggleSubs","Arch_Survey","BIM_Diff","BIM_IfcExplorer"]

        self.envis = ["EnVis_Import", "EnVis_BruttoFl",
                      "EnVis_Setup", "EnVis_SelectRelated"]

        # post-0.18 tools
        if "Arch_Project" in Gui.Command.listAll():
            self.bimtools.insert(0,"Arch_Project")
        if "Arch_Reference" in Gui.Command.listAll():
            self.bimtools.insert(-5,"Arch_Reference")
        if "Draft_Arc_3Points" in Gui.Command.listAll():
            self.draftingtools.insert(5,"Draft_Arc_3Points")
        if "Arch_Truss" in Gui.Command.listAll():
            self.bimtools.insert(self.bimtools.index("Arch_Frame")+1,"Arch_Truss")
        if "Arch_CurtainWall" in Gui.Command.listAll():
            self.bimtools.insert(self.bimtools.index("Arch_Wall")+1,"Arch_CurtainWall")

        # try to load bimbots
        try:
            import bimbots
        except ImportError:
            pass
        else:
            class BIMBots:
                def GetResources(self):
                    return bimbots.get_plugin_info()
                def Activated(self):
                    bimbots.launch_ui()
            Gui.addCommand('BIMBots', BIMBots())
            self.utils.append("BIMBots")

        # load Reporting
        try:
            import report
        except ImportError:
            pass
        else:
            if "Report_Create" in Gui.Command.listAll():
                self.manage[self.manage.index("Arch_Schedule")] = "Report_Create"

        # load webtools
        try:
            import BIMServer, Git, Sketchfab
        except ImportError:
            pass
        else:
            self.utils.extend(["WebTools_Git","WebTools_BimServer","WebTools_Sketchfab"])

        # create toolbars
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Drafting tools"),self.draftingtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","3D/BIM tools"),self.bimtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Annotation tools"),self.annotationtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Modification tools"),self.modify)
        self.appendToolbar("EnVis tools", self.envis)

        # create menus
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&2D Drafting"),self.draftingtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&3D/BIM"),self.bimtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Annotation"),self.annotationtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Snapping"),self.snap)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Modify"),self.modify)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Manage"),self.manage)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Utils"),self.utils)
        self.appendMenu("EnVis", self.envis)

        # load Arch & Draft preference pages
        if hasattr(Gui, "draftToolBar"):
            if not hasattr(Gui.draftToolBar, "loadedArchPreferences"):
                import Arch_rc
                Gui.addPreferencePage(":/ui/preferences-arch.ui", "Arch")
                Gui.addPreferencePage(":/ui/preferences-archdefaults.ui", "Arch")
                Gui.draftToolBar.loadedArchPreferences = True

            if not hasattr(Gui.draftToolBar, "loadedPreferences"):
                import Draft_rc
                Gui.addPreferencePage(":/ui/preferences-draft.ui", "Draft")
                Gui.addPreferencePage(":/ui/preferences-draftsnap.ui", "Draft")
                Gui.addPreferencePage(":/ui/preferences-draftvisual.ui", "Draft")
                Gui.addPreferencePage(":/ui/preferences-drafttexts.ui", "Draft")
                Gui.draftToolBar.loadedPreferences = True

        _log('Loading EnVis module... done')
        Gui.updateLocale()

    def Activated(self):
        from draftutils.messages import _log

        if hasattr(Gui,"draftToolBar"):
            Gui.draftToolBar.Activated()
        if hasattr(Gui,"Snapper"):
            Gui.Snapper.show()

        class EnVisWatcher:
            def __init__(self, cmds, name, invert=False):
                self.commands = cmds
                self.title = name
                self.invert = invert

            def shouldShow(self):
                if self.invert:
                    return (App.ActiveDocument is not None) and (Gui.Selection.getSelection() != [])
                else:
                    return (App.ActiveDocument is not None) and (not Gui.Selection.getSelection())

        Gui.Control.addTaskWatcher([EnVisWatcher(self.draftingtools + self.annotationtools, "2D geometry"),
                                    EnVisWatcher(self.bimtools, "3D/BIM geometry"),
                                    EnVisWatcher(self.modify, "Modify", invert=True)])

        _log("EnVis workbench activated")

    def Deactivated(self):
        from draftutils.messages import _log

        if hasattr(Gui, "draftToolBar"):
            Gui.draftToolBar.Deactivated()
        if hasattr(Gui, "Snapper"):
            Gui.Snapper.hide()

        Gui.Control.clearTaskWatcher()
        _log("EnVis workbench deactivated")

    def ContextMenu(self, recipient):
        import DraftTools
        if recipient == "Tree":
            groups = False
            ungroupable = False
            for o in Gui.Selection.getSelection():
                if o.isDerivedFrom("App::DocumentObjectGroup") or o.hasExtension("App::GroupExtension"):
                    groups = True
                else:
                    groups = False
                    break

            for o in Gui.Selection.getSelection():
                for parent in o.InList:
                    if parent.isDerivedFrom("App::DocumentObjectGroup") or parent.hasExtension("App::GroupExtension"):
                        if o in parent.Group:
                            ungroupable = True
                        else:
                            ungroupable = False
                            break
            if groups:
                self.appendContextMenu("", ["Draft_SelectGroup"])

        elif recipient == "View":
            self.appendContextMenu("Snapping", self.snap)

        if Gui.Selection.getSelection():
            self.appendContextMenu("", ["Draft_AddConstruction"])
            allclones = False
            for obj in Gui.Selection.getSelection():
                if hasattr(obj,"CloneOf") and obj.CloneOf:
                    allclones = True
                else:
                    allclones = False
                    break

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(EnVisWorkbench)
