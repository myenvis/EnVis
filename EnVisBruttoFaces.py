import FreeCAD,Draft

class EnVisBruttoFace:
    def __init__(self, obj):
        self.children = []  # Objects related to this face
        obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.Proxy = self
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
    return prop[0], int(prop[1][0][4:])-1

def linkSubFromFace(obj, faceind):
    return (obj, ["Face" + str(faceind + 1)])

def createModel(layer):
    """build a brutto faces model from a layer or set containing space boundaries"""
    if hasattr(layer, "Group"):
        boundaries = layer.Group
    else: 
        boundaries = layer

    byBE = {}
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
    doors = []

    def handle_external_case(sb):
        obj, faceind = faceFromLinkSub(sb.BaseFace)
        if project.moveOuterSB:
            return makeBruttoFace(sb, None, BaseFace=linkSubFromFace(obj, get_opposite(obj.Shape, faceind)))
        else:
            return makeBruttoFace(sb, None)

    for sbs in byBE.values():
        beObj = sbs[0].BuildingElement
        if beObj.IfcType == "Wall":
            internal,external = innerOuter(sbs)
            while internal:
                a,b = pop_pair(internal)
                # TODO Ev Orientierung der Wand beachten
                d = b.Shape.CenterOfMass - a.Shape.CenterOfMass
                d.multiply(0.5)
                obj = makeBruttoFace(a, b.Space)
                obj.Placement.move(d)
                brutto_faces.append(obj)
            for sb in external:
                brutto_faces.append(handle_external_case(sb))

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
            for sb in external:
                # TODO Detect faces to drop
                brutto_faces.append(handle_external_case(sb))

        else:
            extra.append(sbs)

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

