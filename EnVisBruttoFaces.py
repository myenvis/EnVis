import FreeCAD,Draft
import math
import BOPTools.SplitAPI as split
import EnVisHelper
import EnVisOuterSpace

class EnVisBruttoFace:
    def __init__(self, obj):
        self.full_covers = []  # Objects related to this face
        self.partial_covers = []
        obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.addProperty('App::PropertyLink', 'Space', 'Envis', '')
        obj.addProperty("App::PropertyLinkList",'CoversSpace', 'Envis', 'Bekleidungen auf der Raumseite')
        obj.addProperty('App::PropertyLink', 'Space2', 'Envis', '')
        obj.addProperty("App::PropertyLinkList",'CoversSpace2', 'Envis', 'Bekleidungen auf der Außenseite bzw. Raum2')
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

def copyBruttoFace(orig):
    obj = makeBruttoFace(orig.SpaceBoundary, orig.Space2, BaseFace=orig.BaseFace, doc=orig.Document)
    obj.Proxy.full_covers = orig.Proxy.full_covers.copy()
    obj.Proxy.partial_covers = orig.Proxy.partial_covers.copy()

    return obj

def setup_coverings(bf):
    """Check for full/partial covers"""

    def nameify(obj):
        if type(obj) == str:
            return str
        return obj.Name

    doc = bf.Document
    full_covers = {nameify(o) for o in bf.Proxy.full_covers}
    partial_covers = set(bf.Proxy.partial_covers)
    bf.Proxy.partial_covers = []
    to_delete = []

    for c in partial_covers:
        if type(c) == str:
            c = doc.getObject(c)
        test_shape = make_intersection_candidate(c.Shape, bf.Shape)
        f = bf.Shape.common(test_shape)
        if f.Area < 100:  # mm^2
            to_delete.append(c)
        elif f.Area > bf.Shape.Area - 100:
            full_covers.add(c.Name)
        else:
            bf.Proxy.partial_covers.append(c.Name)

    bf.Proxy.full_covers = list(full_covers)
    bf.CoversSpace = list(filter(lambda o: o not in to_delete, bf.CoversSpace))
    bf.CoversSpace2 = list(filter(lambda o: o not in to_delete, bf.CoversSpace2))

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

    building_objs = list(filter(lambda o: "isBuildingObj(o)" and hasattr(o, "IfcType") and hasattr(o, "Shape") and o.Shape.Solids, doc.Objects))  # TODO

    brutto_faces = []
    extra = []
    windows = []
    walls = []
    slabs = [] # Tuples (ZMax, BruttoFace)

    def handle_external_case(sb):
        """Return a BruttoFace for SpaceBoundary or None, if it shoule be dropped

        The BruttoFace is linked to the proper Außenraum"""
        support_objs = [faceFromLinkSub(sb.BaseFace)]
        coverings_full = []
        coverings_partial = []
        outer_space = None
        while support_objs:
            obj, faceind = support_objs.pop()
            outer_face_ind = EnVisHelper.get_opposite_face(obj.Shape, faceind)
            outer_face = obj.Shape.Faces[outer_face_ind]
            d = EnVisHelper.get_distance_vector(sb.Shape, outer_face)
            offset = d.add(outer_face.normalAt(0,0).multiply(project.intersectionTolerance))
            offset_sb = sb.Shape.copy()
            offset_sb.translate(offset)
            bbox = offset_sb.BoundBox
            bbox.enlarge(project.intersectionTolerance)
            candidates = list(filter(lambda o: o != obj and bbox.intersect(o.Shape.BoundBox), building_objs))
            print("Found", len(candidates), "intersection candidates")
            for o in candidates:
                cover = offset_sb.common(o.Shape)
                if cover.Faces:
                    f = cover.Faces[0]
                    if o.IfcType == "Covering":
                        if EnVisHelper.isClose(f.Area, offset_sb.Area):
                            coverings_full.append(o)
                        else:
                            coverings_partial.append(o)
                        support_objs.append((o, EnVisHelper.get_aligned_face(o.Shape, outer_face)[0]))
                        print("adding", o.Name)
                        continue
                    print("candidate", o.Name, "has area ratio", f.Area/offset_sb.Area)
                    if isBuildingObj(o):
                        print("Dropping")
                        return None
                    else:  # Bedeckung durch Gelände oÄ
                        outer_space = EnVisOuterSpace.get_outer_space(o)
                        if EnVisHelper.isClose(f.Area, offset_sb.Area):
                            support_objs = []
                            break
                        coverings_partial.insert(0, outer_space)
                        outer_space = None
        if not outer_space:
            outer_space = EnVisOuterSpace.get_outer_space(math.degrees(FreeCAD.Vector(0,0,1).getAngle(outer_face.normalAt(0,0))))
        if project.moveOuterSB:
            obj, faceind = faceFromLinkSub(sb.BaseFace)
            outer_face_ind = EnVisHelper.get_opposite_face(obj.Shape, faceind)
            bf = makeBruttoFace(sb, outer_space, BaseFace=linkSubFromFace(obj, outer_face_ind))
        else:
            bf = makeBruttoFace(sb, outer_space)
        bf.CoversSpace2 = coverings_partial + coverings_full
        bf.Proxy.partial_covers = coverings_partial
        bf.Proxy.full_covers = coverings_full

        return bf

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

    # final step: split the brutto faces, that have more then one outer space
    # and also setup coverings
    news = []
    for bf in brutto_faces:
        while bf.Proxy.partial_covers and type(bf.Proxy.partial_covers[0].Proxy) == EnVisOuterSpace.EnVisOuterSpace:
            outer_space = bf.Proxy.partial_covers.pop(0)
            test_shape = EnVisHelper.make_intersection_candidate(outer_space.BaseObject.Shape, bf.Shape, project.intersectionTolerance.Value)
            new_face = bf.Shape.common(test_shape)
            rest_face = bf.Shape.cut(test_shape)
            new = copyBruttoFace(bf)
            while new.Proxy.partial_covers and type(new.Proxy.partial_covers[0].Proxy) == EnVisOuterSpace.EnVisOuterSpace:
                del new.Proxy.partial_covers[0]
            new.Shape = new_face
            new.Space2 = outer_space
            setup_coverings(new)
            news.append(new)
            bf.Shape = rest_face
        setup_coverings(bf)

    brutto_faces.extend(news)
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

