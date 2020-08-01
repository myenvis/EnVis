# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""SpaceBoundary object."""


class SpaceBoundary:
    """SpaceBoundary object."""

    def __init__(self, obj):
        obj.addProperty('App::PropertyLink',
                        'Space',
                        'IfcData',
                        'Zugehörges Raumobjekt')
        obj.addProperty('App::PropertyLink',
                        'BuildingElement',
                        'IfcData',
                        'Zugehörger Bauteil')
        obj.addProperty('App::PropertyBool',
                        'Internal',
                        'IfcData',
                        'Ein anderer Raum liegt gegenüber')
        obj.addProperty('App::PropertyLinkSub',
                        'BaseFace',
                        'DerivedData',
                        'Die begrenzende Fläche des Bauteils')
        obj.Proxy = self
        self.Type = "EnVis::SpaceBoundary"

    def execute(self, obj):
        """Execute when the object is created or recomputed."""
        if obj.BuildingElement.Shape:
            faces = obj.BuildingElement.Shape.Faces
            i = 1
            while faces:
                f = faces.pop(0)
                if obj.Shape.isCoplanar(f):
                    obj.BaseFace = [obj.BuildingElement, "Face"+str(i)]
                    break
                i += 1
