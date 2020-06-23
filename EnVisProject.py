import FreeCAD,ifcopenshell

class EnVisProject:
    def __init__(self, obj):
        obj.addProperty("App::PropertyPath", "IFCFile", "EnVis", "Die IFC-Datei aus der das Modell stammt")
        obj.Proxy = self

    def execute(self, obj):
        pass

    def onChanged(self, obj, prop):
        if prop == "IFCFile":
            # This example does nothing yet
            pass

