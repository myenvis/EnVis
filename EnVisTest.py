import FreeCAD,EnVisBruttoFaces

FreeCAD.loadFile('BruttoFl_Ref.FCStd')
layer = FreeCAD.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")[0]
EnVisBruttoFaces.createModel(layer)
