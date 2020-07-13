import FreeCAD,ifcopenshell

class EnVisProject:
    def __init__(self, obj):
        obj.addProperty("App::PropertyPath", "IFCFile", "EnVis", "Die IFC-Datei aus der das Modell stammt")
        obj.addProperty("App::PropertyBool", "moveOuterSB", "Bruttoflächen", "Verschiebe äußere SpaceBoundaries auf die andere Seite des Bauteils")
        obj.addProperty("App::PropertyBool", "followSlabs", "Bruttoflächen", "Platziere Außenflächen an Deckenkanten")
        obj.addProperty("App::PropertyLength", "intersectionTolerance", "Einstellungen", "Toleranz für berührende Objekte")
        obj.moveOuterSB = True
        obj.followSlabs = True
        obj.intersectionTolerance = 1.0
        obj.Proxy = self

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "IFCFile":
            # This example does nothing yet
            pass

