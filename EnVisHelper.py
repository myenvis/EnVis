
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

def snap_by_resize_Zlength(shape, target):
    replacements = []
    candidates = sorted(shape.OuterWire.Edges, key=lambda e: e.BoundBox.ZLength)[-2:]
    for e in candidates:
        d = get_distance_vector(e, target.Shape.OuterWire)
        if d.Length < 500 and d.Length > 0.0: # TODO: Add configuration setting or auto-detection
            replacements.extend(zip(e.Vertexes, e.translated(d).Vertexes))
    if replacements:
        new_shape = shape.replaceShape(replacements)
        if not new_shape.isValid():
            new_shape.fix(0, 0, 0)
        if not new_shape.isValid():  # This is somewhat drastic, maybe ommit for releases
            new_shape.check()
        return new_shape
    return None

def isClose(x, y):
    return abs(x - y) < 0.1

def mapProperty(items, key_func):
    """Create a map for grouping items by some property

    items: any iterable as input
    key_func: how to calculate the property of items

    The map values are lists because key_func isn't exepected to yield
    unique properties."""

    result = {}
    for i in items:
        key = key_func(i)
        try:
            result[key].append(i)
        except KeyError:
            result[key] = [i]
    return result

