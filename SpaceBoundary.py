# TODO: rename file to EnVisIFCSpaceBoundaries

import FreeCAD
import Arch
import ArchIFC
import Part
import Draft
import importIFCHelper
import ifcopenshell


def getObject(doc, ent):
    """ get object by IFC global ID """
    
    if not ent:
        return None

    objs = doc.Objects
    for o in objs:
        if hasattr(o, "GlobalId") and o.GlobalId == ent.GlobalId:
            return o

    return None

class EnVisIfcSB: # TODO: rename to EnVisIFCSpaceBoundary
    def __init__(self, obj):
        obj.addProperty('App::PropertyLink', 'Space', 'IfcData', 'Zugehörges Raumobjekt')
        obj.addProperty('App::PropertyLink', 'BuildingElement', 'IfcData', 'Zugehörger Bauteil')
        obj.addProperty('App::PropertyBool', 'Internal', 'IfcData', 'Ein anderer Raum liegt gegenüber')
        obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'DerivedData', 'Die begrenzende Fläche des Bauteils')
        obj.Proxy = self
        obj.ViewObject.Proxy = 0

    def execute(self, obj):
        if obj.BuildingElement:
            faces = obj.BuildingElement.Shape.Faces
            i = 1
            while faces:
                f = faces.pop(0)
                if obj.Shape.isCoplanar(f):
                    obj.BaseFace = [obj.BuildingElement, "Face"+str(i)]
                    break
                i += 1


class SpaceBoundaries:
    def __init__(self, filename):
    
        "load SpaceBoundary relations from file as FreeCAD Objects"

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
            self.lay = Draft.makeLayer("IfcSpaceBoundaries", transparency=80)
            self.lay.ViewObject.OverrideShapeColorChildren = False

        self.sbrels = self.ifcfile.by_type('IfcRelSpaceBoundary')

    def show(self, sbrel):
        """ erzeugt FreeCAD Objekt von ifcopenshell object sbrel """
        def name(e):
            if e.Name:
                return e.Name
            else:
                return str(e.id())
        space = sbrel.RelatingSpace
        surface = sbrel.ConnectionGeometry.SurfaceOnRelatingElement
        building_element = getObject(FreeCAD.ActiveDocument, sbrel.RelatedBuildingElement)
        if building_element:
            name = 'Raum' + name(space) + '_zu_' + building_element.Label + '_' + str(sbrel.id())
        else:
            name = 'Raum' + name(space) + '_' + str(sbrel.id())
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
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
        EnVisIfcSB(obj)

        # Eliud: this `space.Name` is not found if the FreeCAD IFC import
        # does not create parametric Arch objects.
        # This needs to be set up in the IFC Import-Export Preferences
        # "Import arch IFC objects as Parametric Arch objects"
        # TODO: force setting the parameter on Workbench initialization
        # and all necessary preferences.
        obj.Space = FreeCAD.ActiveDocument.getObjectsByLabel(space.Name)[0]
        obj.BuildingElement = building_element

        if len(shape.Faces) == 1:
            obj.Shape = shape.Faces[0]
        else:
            print("SpaceBoundary has not exactly one face: ", sbrel)
            obj.Shape = shape
        obj.Internal = sbrel.InternalOrExternalBoundary == 'INTERNAL'
        if obj.Internal:
            obj.ViewObject.ShapeColor = (1.0, green, 0.0)
        else:
            obj.ViewObject.ShapeColor = (0.0, green, 1.0)

        return obj

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
