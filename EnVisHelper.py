
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

