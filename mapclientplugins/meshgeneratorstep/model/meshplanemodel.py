
from opencmiss.utils.zinc import createFiniteElementField, createSquare2DFiniteElement

from mapclientplugins.meshgeneratorstep.model.meshalignmentmodel import MeshAlignmentModel


class MeshPlaneModel(MeshAlignmentModel):

    def _createModel(self):
        self._modelCoordinateField = createFiniteElementField(self._region)
        fieldmodule = self._region.getFieldmodule()
        createSquare2DFiniteElement(fieldmodule, self._modelCoordinateField,
                                    [[-2.0, -2.0, 0.0], [2.0, -2.0, 0.0], [-2.0, 2.0, 0.0], [2.0, 2.0, 0.0]])

    def _createGraphics(self):
        scene = self._region.getScene()
        scene.beginChange()
        scene.removeAllGraphics()
        materialmodule = scene.getMaterialmodule()
        lines = scene.createGraphicsLines()
        lines.setExterior(True)
        lines.setName('plane-lines')
        lines.setCoordinateField(self._modelTransformedCoordinateField)
        surfaces = scene.createGraphicsSurfaces()
        surfaces.setName('plane-surfaces')
        surfaces.setCoordinateField(self._modelTransformedCoordinateField)
        surfaces.setMaterial(materialmodule.findMaterialByName('silver'))
        scene.endChange()

