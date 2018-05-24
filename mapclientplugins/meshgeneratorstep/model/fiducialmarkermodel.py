from opencmiss.zinc.field import Field
from opencmiss.zinc.glyph import Glyph

from opencmiss.utils.zinc import createFiniteElementField


FIDUCIAL_MARKER_LABELS = ['LV apex', 'RV apex', 'LAD CFX junction', 'RV wall extent']


class FiducialMarkerModel(object):

    def __init__(self, region):
        self._parent_region = region
        self._region_name = 'fiducial'
        self._markers = {}
        self._settings = {'display-fiducial-markers': True,
                          'active-marker-label': FIDUCIAL_MARKER_LABELS[0]}
        self._clear()
        self._reset()

    def registerGetPlaneInfoMethod(self, method):
        self._get_plane_info = method

    def getPlaneDescription(self):
        plane_normal, _, point_on_plane = self._get_plane_info()
        return point_on_plane, plane_normal

    def setDisplayFiducialMarkers(self, state):
        self._settings['display-fiducial-markers'] = state

    def isDisplayFiducialMarkers(self):
        return self._settings['display-fiducial-markers']

    def setActiveMarker(self, marker_label):
        self._settings['active-marker-label'] = marker_label

    def getActiveMarker(self):
        return self._settings['active-marker-label']

    def getSettings(self):
        return self._settings

    def setSettings(self, settings):
        self._settings.update(settings)

    def setNodeLocation(self, position):
        marker = self._markers[self._settings['active-marker-label']]
        marker.setPosition(position)

    def _clear(self):
        self._region = None
        self._scene = None
        self._get_plane_info = None

    def _reset(self):
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        self._scene = self._region.getScene()
        self._createModel()
        # self._createGraphics()

    def _createModel(self):
        # self._coordinate_field = createFiniteElementField(self._region)
        # fieldmodule = self._region.getFieldmodule()
        for label in FIDUCIAL_MARKER_LABELS:
            self._markers[label] = FiducialMarker(self._region, label)


def _createGraphics(scene, coordinate_field, label):
    scene.beginChange()
    scene.removeAllGraphics()
    materialmodule = scene.getMaterialmodule()
    blue = materialmodule.findMaterialByName('blue')
    graphic = scene.createGraphicsPoints()
    graphic.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
    graphic.setCoordinateField(coordinate_field)
    graphic.setMaterial(blue)
    label_graphic = scene.createGraphicsPoints()
    label_graphic.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
    label_graphic.setCoordinateField(coordinate_field)
    attributes = graphic.getGraphicspointattributes()
    attributes.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
    attributes.setBaseSize([0.02])
    label_attributes = label_graphic.getGraphicspointattributes()
    label_attributes.setBaseSize([0.02])
    label_attributes.setLabelText(1, label)
    label_attributes.setLabelOffset(1.0)
    scene.endChange()

    return graphic


class FiducialMarker(object):

    def __init__(self, region, label):
        self._region = region.createChild(label)
        self._coordinate_field = createFiniteElementField(self._region)
        self._fieldmodule = self._region.getFieldmodule()
        self._label = label
        # self._label_field = self._fieldmodule.createFieldStoredString()
        scene = self._fieldmodule.getRegion().getScene()
        self._graphic = _createGraphics(scene, self._coordinate_field, label)
        self._node = None

    def _create(self):
        nodeset = self._fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        template = nodeset.createNodetemplate()
        template.defineField(self._coordinate_field)
        # template.defineField(self._label_field)
        self._node = nodeset.createNode(-1, template)
        self._group_field = self._fieldmodule.createFieldGroup()
        node_group = self._group_field.createFieldNodeGroup(nodeset)
        self._nodeset_group = node_group.getNodesetGroup()

    def setPosition(self, position):
        if self._node is None:
            self._create()
        fieldcache = self._fieldmodule.createFieldcache()
        self._fieldmodule.beginChange()
        fieldcache.setNode(self._node)
        self._coordinate_field.assignReal(fieldcache, position)
        # self._label_field.assignString(fieldcache, self._label)
        self._fieldmodule.endChange()
