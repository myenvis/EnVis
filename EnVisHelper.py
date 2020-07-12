
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

def isClose(x, y):
    return abs(x - y) < 0.1
