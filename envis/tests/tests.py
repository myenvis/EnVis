# -----------------------------------------------------------------------------
#
# Private license: 2020, EnVis
#
# -----------------------------------------------------------------------------
"""Tests for the workbench."""

import FreeCAD
import EnVisBruttoFaces

FreeCAD.loadFile('BruttoFl_2.FCStd')
layer = FreeCAD.ActiveDocument.getObjectsByLabel("IfcSpaceBoundaries")[0]
EnVisBruttoFaces.createModel(layer)
