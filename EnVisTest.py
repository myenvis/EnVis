import FreeCAD,EnVisBruttoFaces

FreeCAD.loadFile('BruttoFl_2.FCStd')
layer = FreeCAD.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")[0]
EnVisBruttoFaces.createModel(layer)
