import FreeCAD
import Arch
import ArchIFC
import Part
import Draft
import importIFCHelper
import ifcopenshell

"""
import SpaceBoundary
sb = SpaceBoundary.SpaceBoundaries('/home/harald/architecture/manual.ifc')
"""

def getObject(doc, ent):
    objs = doc.Objects
    for o in objs:
        if hasattr(o, "GlobalId") and o.GlobalId == ent.GlobalId:
            return o

    return None

class EnVisIfcSB:
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

    def loadsb(self, sbrel):
        # Relevant members of sbrel:
        sbrel.GlobalId
        if sbrel.Name != '2ndLevel':
            print("Not a 2ndLevel Boundary: ", sbrel)
        if sbrel.Description != '2a':
            print("Boundary nof of type 2a: ", sbrel);
        space = sbrel.RelatingSpace
        boundary_elem = sbrel.RelatedBuildingElement
        surface = sbrel.ConnectionGeometry.SurfaceOnRelatingElement
        p = importIFCHelper.getPlacement(surface.BasisSurface.Position,self.ifcscale)
        if surface.InnerBoundaries:
            print("Boundary between ", space.Name, " and ", boundary_elem.Name, " has holes!")
        #boundary_segments = surface.OuterBoundary.Segments
        if sbrel.ConnectionGeometry.SurfaceOnRelatedElement:
            print("Boundary has Surface on non-space element: ", sbrel)
        isreal = sbrel.PhysicalOrVirtualBoundary == 'PHYSICAL'
        isinternal = sbrel.InternalOrExternalBoundary == 'INTERNAL'

        outer_boundary = importIFCHelper.get2DShape(surface)
        if not outer_boundary:
            print("zweite methode")
            outer_boundary = importIFCHelper.get2DShape(surface.OuterBoundary.Segments[0].ParentCurve)
        if not outer_boundary:
            print("returning entity")
            return surface
        
        f = Part.makeFilledFace(outer_boundary[0].SubShapes)
#        p.multiply(importIFCHelper.getPlacement(space.ObjectPlacement))
        f.Placement = p
        # f.Placement.move()

        return (f, 'Raum' + space.Name + '_zu_' + boundary_elem.Name + '_' + str(sbrel.id()))

    def show(self, sbrel):
#        (face, name) = self.loadsb(sbrel)
#        Part.show(face, name) # Insert as <Part::PartFeature> into active Document
        def name(e):
            if e.Name:
                return e.Name
            else:
                return str(e.id())
        space = sbrel.RelatingSpace
        boundary_elem = sbrel.RelatedBuildingElement
        surface = sbrel.ConnectionGeometry.SurfaceOnRelatingElement
        if boundary_elem:
            name = 'Raum' + name(space) + '_zu_' + name(boundary_elem) + '_' + str(sbrel.id())
        else:
            name = 'Raum' + name(space) + '_' + str(sbrel.id())
            print("SpaceBoundary without building element: ", sbrel)
        if sbrel.PhysicalOrVirtualBoundary == 'PHYSICAL':
            green = 0.0
        else:
            green = 1.0

        cr = ifcopenshell.geom.create_shape(self.settings,surface)
        shape = Part.Shape()
        shape.importBrepFromString(cr.brep_data)
        shape.scale(1000.0)
        shape.Placement = importIFCHelper.getPlacement(space.ObjectPlacement)
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
        EnVisIfcSB(obj)
        obj.Space = FreeCAD.ActiveDocument.getObjectsByLabel(space.Name)[0]
        obj.BuildingElement = getObject(FreeCAD.ActiveDocument, boundary_elem)

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

    def writeareas(self, filename):
        f = open(filename, 'a')
        for sbrel in self.sbrels:
            (face, name) = self.loadsb(sbrel)
            f.write(name)
            f.write("\t")
            f.write(str(face.Area/1000000)) # Wir wollen Quadratmeter
            f.write("\n")

        f.close()
