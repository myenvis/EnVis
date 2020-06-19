# main workbench class

class EnPlanWorkbench(Workbench):


    def __init__(self):

        self.__class__.MenuText = "EnPlan"
        self.__class__.ToolTip = "Energy planning workbench"
        self.__class__.Icon = """
/* XPM */
static char * IFC_xpm[] = {
"16 16 9 1",
" 	c None",
".	c #D80742",
"+	c #C20B5E",
"@	c #B11A71",
"#	c #0E4A94",
"$	c #A12288",
"%	c #61398E",
"&	c #983563",
"*	c #1E8BA6",
"                ",
"     #   ..     ",
"    ### ....    ",
"   ## ##+  ..   ",
"  ##  .##   ..  ",
" ##  +. ##   .. ",
" ## $$$+##**..  ",
"  #%$$$%#**&.   ",
"  $$% ##*+..&*  ",
" $$$###*@..  ** ",
" $$  #**$@@  ** ",
"  $$  **%$  **  ",
"   $$  **  **   ",
"    $$$$****    ",
"     $$  **     ",
"                "};
"""

    def Initialize(self):

        import DraftTools
        import Arch
        import EnPlanCommands
        try:
        #    import BimCommands,BimWindows,BimStructure,BimLayers
        #    FreeCADGui.addCommand('BIM_Column',BimStructure.BIM_Column())
        #    FreeCADGui.addCommand('BIM_Beam',BimStructure.BIM_Beam())
        #    FreeCADGui.addCommand('BIM_Slab',BimStructure.BIM_Slab())
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

        if "Draft_WorkingPlaneProxy" in Gui.listCommands():
            _tool = "Draft_WorkingPlaneProxy"
        else:
            _tool = "Draft_SetWorkingPlaneProxy"

        self.utils = ["BIM_TogglePanels","BIM_Trash","BIM_WPView",
                      "Draft_Slope", _tool, "Draft_AddConstruction",
                      "Arch_SplitMesh","Arch_MeshToShape",
                      "Arch_SelectNonSolidMeshes","Arch_RemoveShape",
                      "Arch_CloseHoles","Arch_MergeWalls","Arch_Check",
                      "Arch_ToggleIfcBrepFlag",
                      "Arch_ToggleSubs","Arch_Survey","BIM_Diff","BIM_IfcExplorer"]

        self.enplan = ["EnPlan_Import"]


        # post-0.18 tools

        if "Arch_Project" in Gui.listCommands():
            self.bimtools.insert(0,"Arch_Project")
        if "Arch_Reference" in Gui.listCommands():
            self.bimtools.insert(-5,"Arch_Reference")
        if "Draft_Arc_3Points" in Gui.listCommands():
            self.draftingtools.insert(5,"Draft_Arc_3Points")
        if "Arch_Truss" in Gui.listCommands():
            self.bimtools.insert(self.bimtools.index("Arch_Frame")+1,"Arch_Truss")
        if "Arch_CurtainWall" in Gui.listCommands():
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
            FreeCADGui.addCommand('BIMBots', BIMBots())
            self.utils.append("BIMBots")

        # load Reporting

        try:
            import report
        except ImportError:
            pass
        else:
            if "Report_Create" in Gui.listCommands():
                self.manage[self.manage.index("Arch_Schedule")] = "Report_Create"

        # load webtools

        try:
            import BIMServer, Git, Sketchfab
        except ImportError:
            pass
        else:
            self.utils.extend(["WebTools_Git","WebTools_BimServer","WebTools_Sketchfab"])

        def QT_TRANSLATE_NOOP(scope, text):
            return text

        # create toolbars

        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Drafting tools"),self.draftingtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","3D/BIM tools"),self.bimtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Annotation tools"),self.annotationtools)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Modification tools"),self.modify)
        self.appendToolbar(QT_TRANSLATE_NOOP("BIM","Manage tools"),self.manage)

        # create menus


        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&2D Drafting"),self.draftingtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&3D/BIM"),self.bimtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Annotation"),self.annotationtools)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Snapping"),self.snap)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Modify"),self.modify)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Manage"),self.manage)
        self.appendMenu(QT_TRANSLATE_NOOP("BIM","&Utils"),self.utils)
        self.appendMenu("EnPlan", self.enplan)


        # load Arch & Draft preference pages
        if hasattr(FreeCADGui,"draftToolBar"):
            if not hasattr(FreeCADGui.draftToolBar,"loadedArchPreferences"):
                import Arch_rc
                FreeCADGui.addPreferencePage(":/ui/preferences-arch.ui","Arch")
                FreeCADGui.addPreferencePage(":/ui/preferences-archdefaults.ui","Arch")
                FreeCADGui.draftToolBar.loadedArchPreferences = True
            if not hasattr(FreeCADGui.draftToolBar,"loadedPreferences"):
                import Draft_rc
                FreeCADGui.addPreferencePage(":/ui/preferences-draft.ui","Draft")
                FreeCADGui.addPreferencePage(":/ui/preferences-draftsnap.ui","Draft")
                FreeCADGui.addPreferencePage(":/ui/preferences-draftvisual.ui","Draft")
                FreeCADGui.addPreferencePage(":/ui/preferences-drafttexts.ui","Draft")
                FreeCADGui.draftToolBar.loadedPreferences = True

        Log ('Loading EnPlan module... done\n')
        FreeCADGui.updateLocale()

    def Activated(self):

        if hasattr(FreeCADGui,"draftToolBar"):
            FreeCADGui.draftToolBar.Activated()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.show()

        class EnPlanWatcher:

            def __init__(self,cmds,name,invert=False):

                self.commands = cmds
                self.title = name
                self.invert = invert

            def shouldShow(self):

                if self.invert:
                    return (FreeCAD.ActiveDocument != None) and (FreeCADGui.Selection.getSelection() != [])
                else:
                    return (FreeCAD.ActiveDocument != None) and (not FreeCADGui.Selection.getSelection())

        FreeCADGui.Control.addTaskWatcher([EnPlanWatcher(self.draftingtools+self.annotationtools,"2D geometry"),
                                           EnPlanWatcher(self.bimtools,"3D/BIM geometry"),
                                           EnPlanWatcher(self.modify,"Modify",invert=True)])

        Log("EnPlan workbench activated\n")


    def Deactivated(self):

        if hasattr(FreeCADGui,"draftToolBar"):
            FreeCADGui.draftToolBar.Deactivated()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.hide()

        FreeCADGui.Control.clearTaskWatcher()

        Log("EnPlan workbench deactivated\n")


    def ContextMenu(self, recipient):

        import DraftTools
        if (recipient == "Tree"):
            groups = False
            ungroupable = False
            for o in FreeCADGui.Selection.getSelection():
                if o.isDerivedFrom("App::DocumentObjectGroup") or o.hasExtension("App::GroupExtension"):
                    groups = True
                else:
                    groups = False
                    break
            for o in FreeCADGui.Selection.getSelection():
                for parent in o.InList:
                    if parent.isDerivedFrom("App::DocumentObjectGroup") or parent.hasExtension("App::GroupExtension"):
                        if o in parent.Group:
                            ungroupable = True
                        else:
                            ungroupable = False
                            break
            if groups:
                self.appendContextMenu("",["Draft_SelectGroup"])
        elif (recipient == "View"):
            self.appendContextMenu("Snapping",self.snap)
        if FreeCADGui.Selection.getSelection():
            self.appendContextMenu("",["Draft_AddConstruction"])
            allclones = False
            for obj in FreeCADGui.Selection.getSelection():
                if hasattr(obj,"CloneOf") and obj.CloneOf:
                    allclones = True
                else:
                    allclones = False
                    break


    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(EnPlanWorkbench)




