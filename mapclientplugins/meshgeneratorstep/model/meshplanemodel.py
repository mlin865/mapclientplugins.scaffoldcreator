
from opencmiss.utils.zinc import createFiniteElementField, createSquare2DFiniteElement

from mapclientplugins.meshgeneratorstep.model.meshalignmentmodel import MeshAlignmentModel


class MeshPlaneModel(MeshAlignmentModel):

    def __init__(self, region):
        super(MeshPlaneModel, self).__init__()
        self._region_name = "plane_mesh"
        self._parent_region = region
        self._region = None
        self._reset()

    def _reset(self):
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        self._scene = self._region.getScene()
        self._createModel()
        self._createGraphics()

    def _createModel(self):
        self._modelCoordinateField = createFiniteElementField(self._region)
        fieldmodule = self._region.getFieldmodule()
        createSquare2DFiniteElement(fieldmodule, self._modelCoordinateField,
                                    [[-2.0, -2.0, 0.0], [2.0, -2.0, 0.0], [-2.0, 2.0, 0.0], [2.0, 2.0, 0.0]])

    def _createGraphics(self):
        scene = self._scene
        scene.beginChange()
        scene.removeAllGraphics()
        materialmodule = scene.getMaterialmodule()
        lines = scene.createGraphicsLines()
        lines.setExterior(True)
        lines.setName('plane-lines')
        lines.setCoordinateField(self._modelCoordinateField)
        surfaces = scene.createGraphicsSurfaces()
        surfaces.setName('plane-surfaces')
        surfaces.setCoordinateField(self._modelCoordinateField)
        surfaces.setMaterial(materialmodule.findMaterialByName('silver'))
        scene.endChange()

