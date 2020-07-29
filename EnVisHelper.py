import math

def get_object_by_guid(doc, guid):
    """ get object by IFC global ID """

    objs = doc.Objects
    for o in objs:
        if hasattr(o, "GlobalId") and o.GlobalId == guid:
            return o

def find_lowest(shapes):
    """Find the lowest shape in a list of shapes"""
    lowest = shapes[0].BoundBox.ZMax
    for s in shapes:
        if s.BoundBox.ZMax <= lowest:
            lowest = s.BoundBox.ZMax
            result = s
    return result

def get_distance_vector(base_shape, target_shape):
    (dist, proximity_points, info) = base_shape.distToShape(target_shape)
    (pp_base, pp_target) = proximity_points[0]
    d = pp_target - pp_base
    for (b, t) in proximity_points[1:]:
        if (t - b - d).Length > 0.1:
            raise RuntimeError("Solutions don't match")
    return d

def all_vertices_inside(vertices, shape):
    for v in vertices:
        if not shape.isInside(v.Point, 0.0, True):
            return False
    return True

def get_opposite_face(shape, faceidx):
    """Return the opposite face of shape"""
    n = shape.Faces[faceidx].normalAt(0,0)
    i = 0
    while n.getAngle(-shape.Faces[i].normalAt(0,0)) > 0.001:
        i += 1
    return i

def face_is_aligned(face1, face2):
    dot = face1.normalAt(0,0).dot(face2.normalAt(0,0))
    return dot < -0.99 or dot > 0.99

def get_closest_aligned_faces(faces, face, tolerance=0.1):
    """Return indices of closest (within 1-2 tolerance) faces with the same (anti)normal"""

    n = face.normalAt(0,0)
    p = face.findPlane()
   
    best = math.inf
    i = 0
    for f in faces:
        dot = n.dot(f.normalAt(0,0))
        if dot < -0.99 or dot > 0.99:  # check if faces are (anti)parallel
#            d = f.distToShape(face)[0] # maybe faster: (f2.valueAt(0,0) - f1.valueAt(0,0)).Length
            d = p.projectPoint(f.Vertexes[0].Point, Method="LowerDistance")
            if d < best - tolerance:
                best = d
                result = [i]
            elif d < best + tolerance:
                result.append(i)
        i += 1
    return result


def get_aligned_face(shape, face):
    """Return (index, offset_vector) of the closest face of shape, that has the same (anti)normal

    TODO: If there are multiple coplanar faces, a random one is selected, not the closest"""
    n = face.normalAt(0,0)
    p = face.findPlane()
    i = 0
    best = 2e100
    for f in shape.Faces:
        dot = n.dot(f.normalAt(0,0))
        if dot < -0.99 or dot > 0.99:  # check if faces are (anti)parallel
#            d = f.distToShape(face)[0] # maybe faster: (f2.valueAt(0,0) - f1.valueAt(0,0)).Length
            d = p.projectPoint(f.Vertexes[0].Point, Method="LowerDistance")
            if d < best:
                best = d
                best_i = i
        i += 1
    pos = shape.Faces[best_i].Surface.Position
    return (best_i, p.projectPoint(pos) - pos)

def make_intersection_candidate(shape, face, overlap=1):
    """make_intersection_candidate(shape, face, overlap=1):
    return a copy of shape translated along normals so that it might intersect face

    overlap is in mm"""
    (face_ind, d) = get_aligned_face(shape, face)
    if d.Length == 0.0:
        return shape
    d.multiply(1 + overlap/d.Length)
    test_shape = shape.copy()
    test_shape.translate(d)
    return test_shape

def shape_get_edges_by_vertices(shape, vertices):
    """Return list of all edges in shape, that have both vertices
    in vertices"""
    result = []
    for e in shape.Edges:
        if any(map(e.Vertexes[0].isEqual, vertices)) and any(map(e.Vertexes[1].isEqual, vertices)):
            result.append(e)
    return result

def snap_by_resize_Zlength(shape, target):
    replacements = []
    candidates = sorted(shape.OuterWire.Edges, key=lambda e: e.BoundBox.ZLength)[-2:]
    for e in candidates:
        d = get_distance_vector(e, target.Shape.OuterWire)
        if d.Length < 500 and d.Length > 0.0: # TODO: Add auto-detection
            e_new = e.translated(d)
            replacements.append((e, e_new))
            replacements.extend(zip(e.Vertexes, e_new.Vertexes))
    if replacements:
        new_shape = shape.replaceShape(replacements)
        if not new_shape.isValid():
            new_shape.fix(0, 0, 0)
        if not new_shape.isValid():  # This is somewhat drastic, maybe omit for releases
            new_shape.check()
        return new_shape
    return None

def isClose(x, y):
    return abs(x - y) < 0.1

def mapProperty(items, key_func):
    """Create a map for grouping items by some property

    items: any iterable as input
    key_func: how to calculate the property of items

    The map values are lists because key_func isn't expected to yield
    unique properties."""

    result = {}
    for i in items:
        key = key_func(i)
        try:
            result[key].append(i)
        except KeyError:
            result[key] = [i]
    return result

# Highly experimental function. Probably unuseable
def replaceEdge(shape, old_edge, new_edge):
    def get_other_edge(vertex, edge):
        [edge1, edge2] = shape.ancestorsOfType(v0, Part.Edge)
        if edge.isSame(edge1):
            return edge2
        return edge1

    def get_other_vertex(edge, vertex):
        if edge.Vertexes[0] == vertex:
            return edge.Vertexes[1]
        else:
            return edge.Vertexes[0]

    def resnap(edge, old_vertex, new_vertex):
        p = edge.Curve.parameter(new_vertex.Point)
        stable_vertex = get_other_vertex(edge, old_vertex)
        [c1, c2] = edge.split(p).Edges
        if old_vertex in c1.Vertexes:
            c = c2
        else:
            c = c1
        return c.replaceShape([(get_other_vertex(c, stable_vertex), new_vertex)])
        ## Don't support extending for now
        v = get_other_vertex(edge, old_vertex)
        p2 = edge.Curve.parameter(v)
        new_edge = edge.Curve.toShape(p, p2)

    [v0, v1] = old_edge.Vertexes
    e0 = get_other_edge(v0, old_edge)
    e1 = get_other_edge(v1, old_edge)
    new_e0 = resnap(e0, v0, new_edge.Vertexes[0])
    new_e1 = resnap(e1, v1, new_edge.Vertexes[1])
    replacements = [(old_edge,new_edge), (e0,new_e0), (e1,new_e1)]
    replacements.extend(zip(old_edge.Vertexes, new_edge.Vertexes))
    return shape.replaceShape(replacements)
