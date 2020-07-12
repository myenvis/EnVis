import FreeCAD,Draft
import EnVisHelper

class EnVisBruttoFace:
    def __init__(self, obj):
        self.children = []  # Objects related to this face
        obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.Proxy = self
        if obj.ViewObject:
            obj.ViewObject.Proxy = 0

#    def execute(self, obj):
#        parent, face = faceFromLinkSub(obj.BaseFace)
#        obj.Shape = parent.Shape.Faces[face]
#        obj.Shape.Placement = parent.Shape.Placement

def makeBruttoFace(space_boundary, other_space, BaseFace=None, doc=None):
    if not doc:
        doc = FreeCAD.ActiveDocument

    obj = doc.addObject("Part::FeaturePython", "BruttoFace" + space_boundary.Name)
    EnVisBruttoFace(obj)
    if BaseFace:
        obj.BaseFace = BaseFace
    else:
        obj.BaseFace = space_boundary.BaseFace
    parent, face = faceFromLinkSub(obj.BaseFace)
    obj.Shape = parent.Shape.Faces[face]
    obj.Placement = parent.Shape.Faces[face].Placement
#    obj.Placement.multiply(parent.Placement)

    return obj

def innerOuter(sbs):
    i = set()
    e = set()
    for sb in sbs:
        if sb.Internal:
            i.add(sb)
        else:
            e.add(sb)
    return i,e

def pop_pair(sbs):
    sb = sbs.pop()
    old_d = None
    for o in sbs:
        if sb.Shape.Area - o.Shape.Area > 0.001 or sb.BaseFace[1] == o.BaseFace[1]:
            continue
        d = (sb.Shape.CenterOfMass - o.Shape.CenterOfMass).Length
        if not old_d or old_d > d:
            old_d = d
            other = o
    sbs.remove(other)
    
    return sb, other

def get_opposite(shape, faceidx):
    """Return the opposite face of shape"""
    n = shape.Faces[faceidx].normalAt(0,0)
    i = 0
    while n.getAngle(-shape.Faces[i].normalAt(0,0)) > 0.001:
        i += 1
    return i

def faceFromLinkSub(prop):
    """returns tuple id, faceidx"""
    return prop[0], int(prop[1][0][4:])-1 # string "faceX"

def linkSubFromFace(obj, faceind):
    return (obj, ["Face" + str(faceind + 1)])

def createModel(layer):
    """build a brutto faces model from a layer or a set containing space boundaries"""
    if hasattr(layer, "Group"):
        boundaries = layer.Group
    else: 
        boundaries = layer

    byBE = {} # map: name -> list<space boundaries>
    # TODO: which name is this?
    for sb in boundaries:
        try:
            byBE[sb.BuildingElement.Name].append(sb)
        except KeyError:
            byBE[sb.BuildingElement.Name] = [sb]

    doc = FreeCAD.ActiveDocument
    project = doc.EnVisProject

    brutto_faces = []
    extra = []
    windows = []
    doors = [] # TODO: not yet used
    walls = []
    slabs = [] # Tuples (ZMax, BruttoFace)

    def handle_external_case(sb):
        obj, faceind = faceFromLinkSub(sb.BaseFace)
        if project.moveOuterSB:
            return makeBruttoFace(sb, None, BaseFace=linkSubFromFace(obj, get_opposite(obj.Shape, faceind)))
        else:
            return makeBruttoFace(sb, None)

    for sbs in byBE.values():
        beObj = sbs[0].BuildingElement
        if beObj.IfcType == "Wall":
            walls.append(sbs)
        elif beObj.IfcType == "Window":
            windows.append(sbs)
        elif beObj.IfcType == "Slab":
            internal,external = innerOuter(sbs)
            while internal:
                a,b = pop_pair(internal)
                if a.Shape.BoundBox.ZMax > b.Shape.BoundBox.ZMax:  # Obere Fläche als Grenze, weil darüber ist Trittschalldämmung
                    obj = makeBruttoFace(a, b.Space)
                else:
                    obj = makeBruttoFace(b, a.Space)
                brutto_faces.append(obj)
                slabs.append((obj.Shape.BoundBox.ZMax, obj))
            for sb in external:
                # TODO Detect faces to drop
                obj = handle_external_case(sb)
                brutto_faces.append(obj)
                slabs.append((obj.Shape.BoundBox.ZMax, obj))
        else:
            extra.append(sbs)

#    slabs.sort()
    def find_closest(elements, target):
        # TODO: Implement something faster
        diff = abs(elements[0][0] - target) + 1
        for e in elements:
            (value, obj) = e
            d = abs(value - target)
            if d < diff:
                diff = d
                result = e
        return result

    for sbs in walls:
        internal,external = innerOuter(sbs)
        while internal:
            a,b = pop_pair(internal)
            # TODO Ev Orientierung der Wand beachten
            d = b.Shape.CenterOfMass - a.Shape.CenterOfMass
            d.multiply(0.5)
            obj = makeBruttoFace(a, b.Space)
            obj.Placement.move(d)

            shape = obj.Shape
            high = shape.BoundBox.ZMax
            low = shape.BoundBox.ZMin
            (z_high, slab) = find_closest(slabs, high)
            (z_low, slab) = find_closest(slabs, low)
            vh = filter(lambda v: EnVisHelper.isClose(v.Z, high), shape.Vertexes)
            vl = filter(lambda v: EnVisHelper.isClose(v.Z, low), shape.Vertexes)
            replacements = [(v, v.translated((0, 0, z_high - high))) for v in vh]
            replacements.extend([(v, v.translated((0, 0, z_low - low))) for v in vl])
            obj.Shape = shape.replaceShape(replacements)

            brutto_faces.append(obj)

        for sb in external:
            obj = handle_external_case(sb)
            if project.followSlabs:
                baseedge = EnVisHelper.find_lowest(obj.Shape.Edges)
                (z, slab) = find_closest(slabs, baseedge.BoundBox.ZMin)
                d = EnVisHelper.get_distance_vector(baseedge, slab.Shape)
                if abs(d.z) > 0.1:
                    raise RuntimeError("Non-horizontal movement for " + str(d.z))
                obj.Placement.move(d)
            brutto_faces.append(obj)

    lay = Draft.makeLayer("BruttoFlächen", transparency=80)
    lay.Group = brutto_faces
    doc.recompute()

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtGui,QtCore

class _CommandBruttoFl:
    def GetResources(self):
        return {
            'MenuText': QtCore.QT_TRANSLATE_NOOP("EnVis_BruttoFl","Bruttoflächen erzeugen"),
            'ToolTip': QtCore.QT_TRANSLATE_NOOP("EnVis_BruttoFl","Erzeugt das Flächenmodell aus SpaceBoundaries")}

    def IsActive(self):
        return FreeCAD.ActiveDocument and hasattr(FreeCAD.ActiveDocument, "EnVisProject")

    def Activated(self):
        layer = FreeCAD.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")[0]
        createModel(layer)

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('EnVis_BruttoFl',_CommandBruttoFl())

