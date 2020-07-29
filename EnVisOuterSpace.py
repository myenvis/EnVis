import FreeCAD

class EnVisOuterSpace:
    def __init__(self, obj):
        #obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.addProperty('App::PropertyLink', 'BaseObject', 'Envis', 'Geländeobjekt')
        obj.addProperty('App::PropertyAngle', 'Angle', 'Envis', 'Neigungswinkel falls Luftraum')
        obj.Proxy = self
        if obj.ViewObject:
            obj.ViewObject.Proxy = 0

def add_outer_space(base_obj, doc):
    if hasattr(base_obj, "Name"):
        name = "Auszenraum_" + base_obj.Name
    else:
        name = "Auszenraum_Luft_" + str(base_obj)

    obj = doc.addObject("App::FeaturePython", name)
    EnVisOuterSpace(obj)
    if hasattr(base_obj, "Name"):
        obj.BaseObject = base_obj
    else:
        obj.Angle = base_obj

    l = doc.EnVisOuterSpaces.Group
    l.append(obj)
    doc.EnVisOuterSpaces.Group = l

    return obj

def get_outer_space(obj, doc = None):
    if not doc:
        doc = FreeCAD.ActiveDocument

    if not hasattr(doc, "EnVisOuterSpaces"):
        doc.addObject("App::DocumentObjectGroup","EnVisOuterSpaces")
        return add_outer_space(obj, doc)

    if hasattr(obj, "Name"):
        for o in doc.EnVisOuterSpaces.Group:
            if o.BaseObject == obj:
                return o
    else:
        for o in doc.EnVisOuterSpaces.Group:
            if o.BaseObject == None and o.Angle == obj:
                return o

    return add_outer_space(obj, doc)
