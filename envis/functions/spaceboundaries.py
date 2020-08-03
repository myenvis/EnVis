# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Module to create all SpaceBoundaries object.

TODO: rethink whether it is really necessary to have a class,
as it is a persistent piece of code in the document.
Since it just creates document objects (various `SpaceBoundary`)
maybe it should just be a function that processes input values
and returns these new objects.
"""

import FreeCAD
import Arch
import Part
import Draft
import importIFCHelper
import ifcopenshell
import envis.make.mk_spaceboundary as mk_space


def getObject(doc, ent):
    """Get object by IFC global ID.

    TODO: this function probably can be moved to a helper module.
    """
    if not ent:
        return None

    objs = doc.Objects
    for o in objs:
        if hasattr(o, "GlobalId") and o.GlobalId == ent.GlobalId:
            return o

    return None


class SpaceBoundaries:
    """Load SpaceBoundary relations from file as FreeCAD Objects.

    TODO: check if we really need it to be a class or a function is better.
    """

    def __init__(self, filename):
        self.ifcfile = ifcopenshell.open(filename)
        self.ifcscale = importIFCHelper.getScaling(self.ifcfile)

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_BREP_DATA,True)
        settings.set(settings.SEW_SHELLS,True)
        settings.set(settings.USE_WORLD_COORDS,True)
        self.settings = settings

        lay = FreeCAD.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")
        if lay:
            self.lay = lay[0]
        else:
            self.lay = Draft.make_layer("IfcSpaceBoundaries", transparency=80)
            self.lay.ViewObject.OverrideShapeColorChildren = False

        self.sbrels = self.ifcfile.by_type('IfcRelSpaceBoundary')

    def show(self, sbrel):
        """ erzeugt FreeCAD Objekt von ifcopenshell object sbrel """
        doc = FreeCAD.activeDocument()

        def _name(e):
            if e.Name:
                return e.Name
            else:
                return str(e.id())

        space = sbrel.RelatingSpace
        surface = sbrel.ConnectionGeometry.SurfaceOnRelatingElement
        building_element = getObject(doc, sbrel.RelatedBuildingElement)
        if building_element:
            name = 'Raum' + _name(space) + '_zu_' + building_element.Label + '_' + str(sbrel.id())
        else:
            name = 'Raum' + _name(space) + '_' + str(sbrel.id())
            print("SpaceBoundary without building element: ", sbrel)
            building_element = Arch.makeComponent(None, name="BrokenSpaceBoundary")

        if sbrel.PhysicalOrVirtualBoundary == 'PHYSICAL':
            green = 0.0
        else:
            green = 1.0

        cr = ifcopenshell.geom.create_shape(self.settings,surface)
        shape = Part.Shape()
        shape.importBrepFromString(cr.brep_data)
        shape.scale(1000.0) # m <-> mm
        shape.Placement = importIFCHelper.getPlacement(space.ObjectPlacement)

        # TODO: check that this make_spaceboundary works as intended.
        #
        # The value `space.Name` is not found if the FreeCAD IFC import
        # does not create parametric Arch objects.
        # This needs to be set up in the IFC Import-Export Preferences
        # "Import arch IFC objects as Parametric Arch objects"
        #
        # TODO: force setting the parameter on Workbench initialization
        # and all necessary preferences.
        new_obj = mk_space.make_spaceboundary(name,
                                              doc.getObjectsByLabel(space.Name)[0],
                                              building_element,
                                              shape,
                                              sbrel)
        return new_obj

    def show_all(self):
        lay_grp = [self.show(s) for s in self.sbrels]
        self.lay.Group = self.lay.Group + lay_grp

        FreeCAD.ActiveDocument.recompute()

    def write_areas(self, filename):
        f = open(filename, 'a')
        for sbrel in self.sbrels:
            (face, name) = self.loadsb(sbrel)
            f.write(name)
            f.write("\t")
            f.write(str(face.Area/1000000)) # Wir wollen Quadratmeter
            f.write("\n")

        f.close()
