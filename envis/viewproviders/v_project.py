# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Viewprovider for the main project object.

Viewproviders must only be used when the GUI is available.
"""


class ViewProject:
    """Viewprovider for the main project object."""

    def __init__(self, vobj):
        self.Object = vobj.Object
        vobj.Proxy = self

    def getIcon(self):
        """Return the icon used by this object."""
        return ":/icons/IFC.svg"

    def attach(self, vobj):
        """Set up the Coin scenegraph."""
        return

    def __getstate__(self):
        """Return a tuple of objects to save or None."""
        return None

    def __setstate__(self, state):
        """Set the internal properties from the restored state."""
        return None
