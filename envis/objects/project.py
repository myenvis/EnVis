# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Project object."""

class Project:
    """Main project object."""

    def __init__(self, obj):
        obj.addProperty("App::PropertyPath",
                        "IFCFile",
                        "EnVis",
                        "Die IFC-Datei aus der das Modell stammt")
        obj.addProperty("App::PropertyBool",
                        "MoveOuterSB",
                        "Bruttofaces",
                        "Verschiebe äußere SpaceBoundaries auf die andere Seite des Bauteils")
        obj.addProperty("App::PropertyBool",
                        "FollowSlabs",
                        "Bruttofaces",
                        "Platziere Außenflächen an Deckenkanten")
        obj.addProperty("App::PropertyLength",
                        "IntersectionTolerance",
                        "Einstellungen",
                        "Toleranz für berührende Objekte")
        obj.MoveOuterSB = True
        obj.FollowSlabs = True
        obj.IntersectionTolerance = 1.0
        obj.Proxy = self
        self.Type = "EnVis::Project"

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "IFCFile":
            # This example does nothing yet
            pass
