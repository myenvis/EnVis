# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""SpaceBoundary object."""

import envis.helpers.helper as helper

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
        if obj.BuildingElement.Shape and obj.BuildingElement.Shape.Faces:
            indices = helper.get_closest_aligned_faces(obj.BuildingElement.Shape.Faces, obj.Shape)
            obj.BaseFace = [obj.BuildingElement, "Face" + str(indices[0] + 1)]
        else:
            obj.BaseFace = None
