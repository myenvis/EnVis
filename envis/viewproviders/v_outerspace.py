# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Viewprovider for the outer space object.

Viewproviders must only be used when the GUI is available.
"""
import os


class ViewOuterSpace:
    """Viewprovider for the outer space object."""

    def __init__(self, vobj):
        self.Object = vobj.Object
        vobj.Proxy = self

    def getIcon(self):
        """Return the icon used by this object."""
        dirn = os.path.dirname(os.path.dirname(__file__))
        icon = os.path.join(dirn, 'resources', 'EnVis_outerspace.svg')
        return icon

    def attach(self, vobj):
        """Set up the Coin scenegraph."""
        return

    def __getstate__(self):
        """Return a tuple of objects to save or None."""
        return None

    def __setstate__(self, state):
        """Set the internal properties from the restored state."""
        return None
