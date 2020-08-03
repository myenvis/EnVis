# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""BruttoFace object."""


class BruttoFace:
    """BruttoFace object."""

    def __init__(self, obj):
        obj.addProperty('App::PropertyLinkSub',
                        'BaseFace',
                        'Envis',
                        '')
        obj.addProperty('App::PropertyLink',
                        'Space',
                        'Envis',
                        '')
        obj.addProperty("App::PropertyLinkList",
                        'CoversSpace',
                        'Envis',
                        'Bekleidungen auf der Raumseite')
        obj.addProperty('App::PropertyLink',
                        'Space2',
                        'Envis',
                        '')
        obj.addProperty("App::PropertyLinkList",
                        'CoversSpace2',
                        'Envis',
                        'Bekleidungen auf der Außenseite bzw. Raum2')
        obj.addProperty('App::PropertyLink',
                        'SpaceBoundary',
                        'Envis',
                        '')
        obj.Proxy = self
        self.Type = "EnVis::BruttoFace"

        # TODO: check where to store this information.
        # These variables will be stored inside the proxy class,
        # however, this is typically what properties are for.
        # Adding information to the class is not normally done.
        self.full_covers = []  # Objects related to this face
        self.partial_covers = []

#    def execute(self, obj):
#        parent, face = faceFromLinkSub(obj.BaseFace)
#        obj.Shape = parent.Shape.Faces[face]
#        obj.Shape.Placement = parent.Shape.Placement
