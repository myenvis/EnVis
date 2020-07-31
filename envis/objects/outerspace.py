# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Outer space object."""


class OuterSpace:
    """Outer space object."""

    def __init__(self, obj):
        # obj.addProperty('App::PropertyLinkSub', 'BaseFace', 'Envis', '')
        obj.addProperty('App::PropertyLink',
                        'BaseObject',
                        'Envis',
                        'Geländeobjekt')
        obj.addProperty('App::PropertyAngle',
                        'Angle',
                        'Envis',
                        'Neigungswinkel falls Luftraum')
        obj.Proxy = self

        # This attribute will be saved with our object
        # allowing us to query it later
        self.Type = "EnVis::OuterSpace"
