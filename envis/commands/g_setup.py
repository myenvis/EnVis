#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2017 Yorik van Havre <yorik@uncreated.net>              *
#*   Private license: 2020, EnVis                                          *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
"""This module contains a simplified BIM setup.

TODO: assume only Python 3; do not test for Python 2.
"""

import os
import sys
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from PySide.QtCore import QT_TRANSLATE_NOOP

import FreeCAD as App
import FreeCADGui as Gui

from draftutils.translate import translate


class EnVisSetup:
    """Command to setup the system."""

    def GetResources(self):
        return {'Pixmap': ":icons/preferences-system.svg",
                'MenuText': QT_TRANSLATE_NOOP("EnVis_Setup", "EnVis Setup..."),
                'ToolTip': QT_TRANSLATE_NOOP("EnVis_Setup",
                                             "Set some common FreeCAD preferences for EnVis workflow")}

    def Activated(self):
        # How many times TechDraw dim arrows are smaller than Draft
        TECHDRAWDIMFACTOR = 0.16

        # Load dialog, in the proper directory above this one
        dirn = os.path.dirname(os.path.dirname(__file__))
        ui = os.path.join(dirn, 'resources', 'dialog_setup.ui')
        self.form = Gui.PySideUic.loadUi(ui)

        # center the dialog over FreeCAD window
        mw = Gui.getMainWindow()
        self.form.move(mw.frameGeometry().topLeft()
                       + mw.rect().center() - self.form.rect().center())

        # connect signals / slots
        self.form.labelIfcOpenShell.linkActivated.connect(self.handleLink)

        # check missing addons
        self.form.labelMissingWorkbenches.hide()
        self.form.labelIfcOpenShell.hide()
        self.form.labelSnapTip.hide()
        m = []
        try:
            import RebarTools
        except ImportError:
            m.append("Reinforcement")

        try:
            import BIMServer
        except ImportError:
            m.append("WebTools")

        try:
            import CFrame
        except ImportError:
            m.append("Dodo")

        try:
            import FastenerBase
        except ImportError:
            m.append("Fasteners")

        try:
            import report
        except ImportError:
            m.append("Reporting")

        try:
            import ifcopenshell
        except ImportError:
            ifcok = False
        else:
            ifcok = True

        libok = False
        librarypath = App.ParamGet('User parameter:Plugins/parts_library').GetString('destination','')
        if librarypath and os.path.exists(librarypath):
            libok = True
        else:
            # check if the library is at the standard addon location
            librarypath = os.path.join(App.getUserAppDataDir(), "Mod", "parts_library")
            if os.path.exists(librarypath):
                App.ParamGet('User parameter:Plugins/parts_library').SetString('destination',librarypath)
                libok = True

        if not libok:
            m.append("Parts Library")
        if m:
            t = (translate("EnVis",
                           "Some additional workbenches are not installed "
                           "that extend EnVis functionality:")
                 + " <b>" + ", ".join(m) + "</b>. "
                 + translate("EnVis", "You can install them from menu Tools -> Addon manager."))
            self.form.labelMissingWorkbenches.setText(t)
            self.form.labelMissingWorkbenches.show()

        if not ifcok:
            self.form.labelIfcOpenShell.show()
        if App.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").GetString("snapModes","111111111101111") == "111111111101111":
            self.form.labelSnapTip.show()

        # show dialog and exit if cancelled
        Gui.EnVisSetupDialog = True  # this is there to be easily detected by the EnVis tutorial
        result = self.form.exec_()
        del Gui.EnVisSetupDialog
        if not result:
            return

        # set preference values
        App.ParamGet("User parameter:BaseApp/Preferences/Mod/EnVis").SetBool("FirstTime",False)
        unit = self.form.settingUnits.currentIndex()
        unit = [0,4,1,3,7,5][unit] # less choices in our simplified dialog
        App.ParamGet("User parameter:BaseApp/Preferences/Units").SetInt("UserSchema",unit)
        if hasattr(App.Units,"setSchema"):
            App.Units.setSchema(unit)
        decimals = self.form.settingDecimals.value()
        App.ParamGet("User parameter:BaseApp/Preferences/Units").SetInt("Decimals",decimals)
        App.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Dimensions").SetBool("UseGlobalDecimals",True)

        # TODO: check if we truly need to remove these options.
        # They were copied from the BIM code, but they were removed from
        # our .ui interface file, so calling them would cause errors.
        # =====================================================================
        # squares = self.form.settingSquares.value()
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetInt("gridEvery",squares)
        # wp = self.form.settingWP.currentIndex()
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetInt("defaultWP",wp)
        # tsize = self.form.settingText.text()
        # tsize = FreeCAD.Units.Quantity(tsize).Value
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetFloat("textheight",tsize)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Dimensions").SetFloat("FontSize",tsize) # TODO - check if this needs a mult factor?
        # font = self.form.settingFont.currentFont().family()
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetString("textfont",font)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Labels").SetString("LabelFont",font)
        # linewidth = self.form.settingLinewidth.value()
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetInt("DefautShapeLineWidth",linewidth)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetInt("linewidth",linewidth)
        # TODO - TechDraw default line styles
        # dimstyle = self.form.settingDimstyle.currentIndex()
        # ddimstyle = [0,2,3,4][dimstyle] # less choices in our simplified dialog
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetInt("dimsymbol",ddimstyle)
        # tdimstyle = [3,0,2,2][dimstyle] # TechDraw has different order than Draft
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Dimensions").SetInt("dimsymbol",tdimstyle)
        # asize = self.form.settingArrowsize.text()
        # asize = FreeCAD.Units.Quantity(asize).Value
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetFloat("arrowsize",asize)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/TechDraw/Dimensions").SetFloat("ArrowSize",asize*TECHDRAWDIMFACTOR)
        # =====================================================================

        author = self.form.settingAuthor.text()
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetString("prefAuthor",author)
        lic = self.form.settingLicense.currentIndex()
        lic = [0,1,2,4,5][lic] # less choices in our simplified dialog
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("prefLicenseType",lic)
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetString("prefLicenseUrl","") # TODO - set correct license URL
        bimdefault = self.form.settingWorkbench.currentIndex()
        if bimdefault == 1:
            App.ParamGet("User parameter:BaseApp/Preferences/General").SetString("AutoloadModule","EnVis")
        elif bimdefault == 2:
            App.ParamGet("User parameter:BaseApp/Preferences/General").SetString("AutoloadModule","StartWorkbench")
            App.ParamGet("User parameter:BaseApp/Preferences/Mod/Start").SetString("AutoloadModule","EnVis")
        newdoc = self.form.settingNewdocument.isChecked()
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetBool("CreateNewDoc",newdoc)
        bkp = self.form.settingBackupfiles.value()
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetInt("CountBackupFiles",bkp)

        # =====================================================================
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("BackgroundColor2",self.form.colorButtonTop.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("BackgroundColor3",self.form.colorButtonBottom.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("DefaultShapeColor",self.form.colorButtonFaces.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetUnsigned("color",self.form.colorButtonFaces.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("DefaultShapeLineColor",self.form.colorButtonLines.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch").SetUnsigned("ColorHelpers",self.form.colorButtonHelpers.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetUnsigned("constructioncolor",self.form.colorButtonConstruction.property("color").rgb()<<8)
        # FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("ConstructionColor",self.form.colorButtonConstruction.property("color").rgb()<<8)
        # height = self.form.settingCameraHeight.value()
        #FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").SetInt("defaultCameraHeight",height)
        # =====================================================================

        # set the orbit mode to turntable
        App.ParamGet("User parameter:BaseApp/Preferences/View").SetInt("OrbitStyle",0)
        # turn thumbnails on
        App.ParamGet("User parameter:BaseApp/Preferences/Document").SetBool("SaveThumbnail",True)

        # TODO: check if we need to remove them.
        # Without getting the working plane preference above, we cannot
        # use this code to set up the working plane
        # =====================================================================
        # set the working plane
        # if hasattr(FreeCAD,"DraftWorkingPlane") and hasattr(FreeCADGui,"draftToolBar"):
        #     if wp == 1:
        #         FreeCAD.DraftWorkingPlane.alignToPointAndAxis(App.Vector(0,0,0), App.Vector(0,0,1), 0)
        #         FreeCADGui.draftToolBar.wplabel.setText("Top(XY)")
        #     elif wp == 2:
        #         FreeCAD.DraftWorkingPlane.alignToPointAndAxis(App.Vector(0,0,0), App.Vector(0,1,0), 0)
        #         FreeCADGui.draftToolBar.wplabel.setText("Front(XZ)")
        #     elif wp == 3:
        #         FreeCAD.DraftWorkingPlane.alignToPointAndAxis(App.Vector(0,0,0), App.Vector(1,0,0), 0)
        #         FreeCADGui.draftToolBar.wplabel.setText("Side(YZ)")
        #     else:
        #         FreeCADGui.draftToolBar.wplabel.setText("Auto")

        # set Draft toolbar
        # if hasattr(FreeCADGui,"draftToolBar"):
        #     FreeCADGui.draftToolBar.widthButton.setValue(linewidth)
        #     FreeCADGui.draftToolBar.fontsizeButton.setValue(tsize)
        # =====================================================================

        # set the status bar widgets
        mw = Gui.getMainWindow()
        if mw:
            st = mw.statusBar()
            statuswidget = st.findChild(QtGui.QToolBar, "EnVisStatusWidget")
            if statuswidget:
                statuswidget.unitLabel.setText(statuswidget.unitsList[self.form.settingUnits.currentIndex()])
                # change the unit of the nudge button
                nudgeactions = statuswidget.nudge.menu().actions()
                if unit in [2, 3, 5, 7]:
                    nudgelabels = statuswidget.nudgeLabelsI
                else:
                    nudgelabels = statuswidget.nudgeLabelsM
                for i in range(len(nudgelabels)):
                    nudgeactions[i].setText(nudgelabels[i])
                if not "auto" in statuswidget.nudge.text().replace("&","").lower():
                    statuswidget.nudge.setText(App.Units.Quantity(statuswidget.nudge.text().replace("&","")).UserString)

    def handleLink(self, link):
        if hasattr(self, "form"):
            if "#install" in link:
                getIfcOpenShell()
            else:
                # print("Opening link:",link)
                url = QtCore.QUrl(link)
                QtGui.QDesktopServices.openUrl(url)


Gui.addCommand('EnVis_Setup', EnVisSetup())


def getPrefColor(color):
    r = ((color >> 24) & 0xFF) / 255.0
    g = ((color >> 16) & 0xFF) / 255.0
    b = ((color >> 8) & 0xFF) / 255.0
    return QtGui.QColor.fromRgbF(r, g, b)


def getIfcOpenShell(force=False):
    """Download and install IfcOpenShell.

    TODO: this should be moved to the Arch Workbench. It's a more centralized
    way to handle installing this dependency.
    """
    ifcok = False

    if not force:
        try:
            import ifcopenshell
        except:
            ifcok = False
        else:
            ifcok = True

    if not ifcok:
        # ifcopenshell not installed
        import re, json
        import zipfile
        import addonmanager_utilities

        if not App.GuiUp:
            reply = QtGui.QMessageBox.Yes
        else:
            reply = QtGui.QMessageBox.question(None,
                                               translate("EnVis","IfcOpenShell not found"),
                                               translate("EnVis","IfcOpenShell is needed to import and export IFC files. It appears to be missing on your system. Would you like to download and install it now? It will be installed in FreeCAD's Macros directory."),
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, 
                                               QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            print("Loading list of latest IfcOpenBot builds from https://github.com/IfcOpenBot/IfcOpenShell...")
            url1 = "https://api.github.com/repos/IfcOpenBot/IfcOpenShell/comments?per_page=100"
            u = addonmanager_utilities.urlopen(url1)
            if u:
                r = u.read()
                u.close()
                d = json.loads(r)
                l = d[-1]['body']
                links = re.findall("http.*?zip",l)
                pyv = "python-"+str(sys.version_info.major)+str(sys.version_info.minor)
                if sys.platform.startswith("linux"):
                    plat = "linux"
                elif sys.platform.startswith("win"):
                    plat = "win"
                elif sys.platform.startswith("darwin"):
                    plat = "macos"
                else:
                    print("Error - unknown platform")
                    return
                if sys.maxsize > 2**32:
                    plat += "64"
                else:
                    plat += "32"
                print("Looking for", plat, pyv)
                for link in links:
                    if ("ifcopenshell-"+pyv in link) and (plat in link):
                        print("Downloading "+link+"...")
                        p = App.ParamGet("User parameter:BaseApp/Preferences/Macro")
                        fp = p.GetString("MacroPath", os.path.join(App.getUserAppDataDir(), "Macros"))
                        u = addonmanager_utilities.urlopen(link)
                        if u:
                            if sys.version_info.major < 3:
                                import StringIO as io
                                _stringio = io.StringIO
                            else:
                                import io
                                _stringio = io.BytesIO
                            zfile = _stringio()
                            zfile.write(u.read())
                            zfile = zipfile.ZipFile(zfile)
                            zfile.extractall(fp)
                            u.close()
                            zfile.close()
                            print("Successfully installed IfcOpenShell to",fp)
                            break
                else:
                    print("Unable to find a build for your version")
