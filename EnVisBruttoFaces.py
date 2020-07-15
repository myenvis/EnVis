import FreeCAD,Draft
import BOPTools.SplitAPI as split
import EnVisHelper

class EnVisBruttoFace:
    def __init__(self, obj):
        self.children = []  # Objects related to this face
        obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.addProperty('App::PropertyLink', 'Space', 'Envis', '')
        obj.addProperty('App::PropertyLink', 'Space2', 'Envis', '')
        obj.addProperty('App::PropertyLink', 'SpaceBoundary', 'Envis', '')
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
    obj.Space = space_boundary.Space
    obj.Space2 = other_space
    obj.SpaceBoundary = space_boundary
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

def isBuildingObj(obj):
    return hasattr(obj, "IfcType") and obj.IfcType in ["Wall", "Slab"]  # TODO extend list

def createModel(layer):
    """build a brutto faces model from a layer or a set containing space boundaries"""
    if hasattr(layer, "Group"):
        boundaries = layer.Group
    else: 
        boundaries = layer

    byBE = EnVisHelper.mapProperty(boundaries, lambda sb: sb.BuildingElement.Name)
    doc = FreeCAD.ActiveDocument
    project = doc.EnVisProject

    building_objs = list(filter(lambda o: isBuildingObj(o) and hasattr(o, "Shape") and o.Shape.Solids, doc.Objects))

    brutto_faces = []
    extra = []
    windows = []
    walls = []
    slabs = [] # Tuples (ZMax, BruttoFace)

    def handle_external_case(sb):
        """Return a BruttoFace for SpaceBoundary or None, if it shoule be dropped

        Not implemented: The BruttoFace is linked to the proper Außenraum"""
        obj, faceind = faceFromLinkSub(sb.BaseFace)
        outer_face_ind = get_opposite(obj.Shape, faceind)
        outer_face = obj.Shape.Faces[outer_face_ind]
        d = EnVisHelper.get_distance_vector(obj.Shape.Faces[faceind], outer_face)
        d.add(outer_face.normalAt(0,0).multiply(project.intersectionTolerance))
        offset_sb = sb.Shape.copy()
        offset_sb.translate(d)
        bbox = offset_sb.BoundBox
        bbox.enlarge(project.intersectionTolerance)
        candidates = list(filter(lambda o: o != obj and bbox.intersect(o.Shape.BoundBox), building_objs))
        print("Found", len(candidates), "intersection candidates")
        #offset_face = outer_face.translated(offset)
        for o in candidates:
            cover = offset_sb.common(o.Shape)
            if cover.Faces:
                f = cover.Faces[0]
                print("candiate", o.Name, "has area ratio", f.Area/offset_sb.Area)
                if isBuildingObj(o):
                    print("Dropping")
                    return None
                # TODO create proper Außenraum
        if project.moveOuterSB:
            return makeBruttoFace(sb, None, BaseFace=linkSubFromFace(obj, outer_face_ind))
        else:
            return makeBruttoFace(sb, None)

    for sbs in byBE.values():
        beObj = sbs[0].BuildingElement
        if beObj.IfcType == "Wall":
            walls.append(sbs)
        elif beObj.IfcType in ["Window", "Door"]:
            windows.extend(sbs)
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
                obj = handle_external_case(sb)
                if not obj:
                    continue
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
            (z_low, floor) = find_closest(slabs, low)
            orig_vertices = shape.OuterWire.Vertexes
            vh = filter(lambda v: EnVisHelper.isClose(v.Z, high), orig_vertices)
            vl = filter(lambda v: EnVisHelper.isClose(v.Z, low), orig_vertices)
            replacements = [(v, v.translated((0, 0, z_high - high))) for v in vh]
            replacements.extend([(v, v.translated((0, 0, z_low - low))) for v in vl])
            obj.Shape = shape.replaceShape(replacements)
            # TODO call Shape.fix() here?
            if project.followSlabs:
                new_shape = EnVisHelper.snap_by_resize_Zlength(obj.Shape, floor)
                if new_shape:
                    obj.Shape = new_shape

            brutto_faces.append(obj)

        for sb in external:
            obj = handle_external_case(sb)
            if not obj:
                continue
            if project.followSlabs:
                baseedge = EnVisHelper.find_lowest(obj.Shape.OuterWire.Edges)
                (z, slab) = find_closest(slabs, baseedge.BoundBox.ZMin)
                d = EnVisHelper.get_distance_vector(baseedge, slab.Shape)
                if abs(d.z) > 0.1:
                    raise RuntimeError("Non-horizontal movement for " + str(d.z))
                obj.Placement.move(d)
                #lambda e: baseedge.Curve.Direction.getAngle(e.Curve.Direction) > 0.0
                new_shape = EnVisHelper.snap_by_resize_Zlength(obj.Shape, slab)
                if new_shape:
                    obj.Shape = new_shape

            brutto_faces.append(obj)

    ws = iter(windows)
    for sb in ws:
        if sb.Internal:
            partner = next(ws)
            other = sb.Space
        else:
            other = None  # TODO: Außenraum
        obj = makeBruttoFace(sb, other)
        obj.Shape = sb.Shape
        obj.Placement = sb.Placement
        brutto_faces.append(obj)

    for sbs in extra:
        if sbs[0].BuildingElement.IfcType == "Covering":
            # TODO: Ev. Platzhalterbelegungen extrahieren
            continue
        if sbs[0].BuildingElement.IfcType == "Building Element Proxy":
            print("Found 'IfcBuildingElementProxy': Please fix your IFC file")
        else:
            print("Unhandled object", sbs[0].BuildingElement.Name, "has", len(sbs), "space boundaries")

    lay = Draft.makeLayer("BruttoFlächen", transparency=80)
    lay.Group = brutto_faces

    # gathering and placing all the faces is complete
    # next step: split the faces to match the related spaces
    by_BaseFace = EnVisHelper.mapProperty(brutto_faces, lambda o: (o.BaseFace[0], o.BaseFace[1][0]))
    for group in by_BaseFace.values():
        spaces = set()
        for obj in group:
            spaces.add(obj.Space)
            spaces.add(obj.Space2)
        pairs = set()
        for m in spaces:
            s = []
            for o in group:
                if o.Space2 == m:
                    s.append(o.Space)
                elif o.Space == m:
                    s.append(o.Space2)
            while s:
                cur = s.pop()
                for i in s:
                    pairs.add((cur, i))

        splitters = []
        while pairs:
            (s1, s2) = spaces = pairs.pop()
            pairs.discard((s2, s1))
            candidates = list(filter(lambda f: isBuildingObj(f.BaseFace[0]) and f.Space in spaces and f.Space2 in spaces, brutto_faces))
            if len(candidates) != 1:
                print("FIXME:", len(candidates), "candidates for splitting", group[0].Name)
                continue
            splitters.append(candidates[0].Shape.findPlane().toShape())
        if splitters:
            compound = split.slice(group[0].Shape, splitters, "Split")
            #print("Number of faces: splitters:", len(splitters), "compound:", len(compound.Faces), "group:", len(group))
            for f in compound.Faces:
                best = None
                dist = f.BoundBox.DiagonalLength
                for target in group:
                    d = f.BoundBox.Center.distanceToPoint(target.SpaceBoundary.Shape.BoundBox.Center)
                    if d < dist:
                        dist = d
                        best = target
                best.Shape = f

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

