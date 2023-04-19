from cmlibs.utils.zinc.general import ChangeManager
from cmlibs.zinc.field import Field
from cmlibs.zinc.glyph import Glyph
from cmlibs.zinc.result import RESULT_OK
from cmlibs.zinc.spectrum import Spectrum, Spectrumcomponent

STRING_FLOAT_FORMAT = '{:.8g}'


def get_field_coordinates_on_nodeset(fieldmodule, nodeset, name=None):
    '''
    Get Zinc finite element coordinates field defined on nodeset.
    :param nodeset: Nodeset field must be defined on.
    :param name: Optional name of field to try first.
    :return: Handle to Zinc field or None if none defined.
    '''
    node = nodeset.createNodeiterator().next()
    if not node.isValid():
        return None
    fieldcache = fieldmodule.createFieldcache()
    fieldcache.setNode(node)
    if name:
        field = fieldmodule.findFieldByName(name).castFiniteElement()
        if field.isValid() and field.isTypeCoordinate() and (field.getNumberOfComponents() <= 3) \
                and field.isDefinedAtLocation(fieldcache):
            return field
    fieldIter = fieldmodule.createFielditerator()
    field = fieldIter.next()
    while field.isValid():
        if field.isTypeCoordinate() and (field.getNumberOfComponents() <= 3) and field.isDefinedAtLocation(fieldcache):
            return field
        field = fieldIter.next()
    return None


class SegmentationDataModel():
    """
    Manages segmentation data for building scaffold to.
    """

    def __init__(self, parent_region, material_module):
        self._parent_region = parent_region
        self._materialmodule = material_module
        self._data_filename = None
        self._region_name = "data"
        self._region = None
        self._fieldmodule = None
        self._scene = None
        self._settings = {
            'displayDataContours' : True,
            'displayDataPoints' : False,
            'displayDataRadius' : False,
            'displayDataMarkerPoints' : True,
            'displayDataMarkerNames' : True
            }
        scene = self._parent_region.getScene()
        spectrummodule = scene.getSpectrummodule()
        self._rgbSpectrum = spectrummodule.findSpectrumByName("rgb")
        if not self._rgbSpectrum.isValid():
            with ChangeManager(spectrummodule):
                self._rgbSpectrum = spectrummodule.createSpectrum()
                self._rgbSpectrum.setName("rgb")
                self._rgbSpectrum.setMaterialOverwrite(True)
                colourMappingTypes = ( Spectrumcomponent.COLOUR_MAPPING_TYPE_RED, Spectrumcomponent.COLOUR_MAPPING_TYPE_GREEN, Spectrumcomponent.COLOUR_MAPPING_TYPE_BLUE )
                for c in range(3):
                    spectrumcomponent = self._rgbSpectrum.createSpectrumcomponent()
                    spectrumcomponent.setFieldComponent(c + 1)
                    spectrumcomponent.setColourMappingType(colourMappingTypes[c])
                    spectrumcomponent.setColourMinimum(0.0)
                    spectrumcomponent.setColourMaximum(1.0)
                    spectrumcomponent.setRangeMinimum(0.0)
                    spectrumcomponent.setRangeMaximum(1.0)

    def setDataFilename(self, data_filename):
        self._data_filename = data_filename
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        result = self._region.readFile(self._data_filename)
        assert result == RESULT_OK
        self._fieldmodule = self._region.getFieldmodule()
        self._scene = self._region.getScene()

    def hasData(self):
        return (self._region is not None) and self._region.isValid()

    def getSettings(self):
        return self._settings

    def setSettings(self, settings):
        '''
        Called on loading settings from file.
        '''
        self._settings.update(settings)
        self._generateGraphics()

    def _getVisibility(self, graphicsName):
        return self._settings[graphicsName]

    def _setVisibility(self, graphicsName, show):
        self._settings[graphicsName] = show
        graphics = self._scene.findGraphicsByName(graphicsName)
        graphics.setVisibilityFlag(show)

    def isDisplayDataContours(self):
        return self._getVisibility("displayDataContours")

    def setDisplayDataContours(self, show):
        self._setVisibility("displayDataContours", show)

    def isDisplayDataRadius(self):
        return self._getVisibility("displayDataRadius")

    def setDisplayDataRadius(self, show):
        if show != self._settings["displayDataRadius"]:
            self._settings["displayDataRadius"] = show
            self._generateGraphics()

    def isDisplayDataPoints(self):
        return self._getVisibility("displayDataPoints")

    def setDisplayDataPoints(self, show):
        self._setVisibility("displayDataPoints", show)

    def isDisplayDataMarkerPoints(self):
        return self._getVisibility("displayDataMarkerPoints")

    def setDisplayDataMarkerPoints(self, show):
        self._setVisibility("displayDataMarkerPoints", show)

    def isDisplayDataMarkerNames(self):
        return self._getVisibility("displayDataMarkerNames")

    def setDisplayDataMarkerNames(self, show):
        self._setVisibility("displayDataMarkerNames", show)

    def _generateGraphics(self):
        if not self._scene:
            return
        with ChangeManager(self._scene):
            self._scene.removeAllGraphics()

            nodes = self._fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
            datapoints = self._fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)

            coordinates = get_field_coordinates_on_nodeset(self._fieldmodule, nodes if (nodes.getSize() > 0) else datapoints, "coordinates")
            radius = self._fieldmodule.findFieldByName("radius")
            rgb = self._fieldmodule.findFieldByName("rgb")
            markerGroup = self._fieldmodule.findFieldByName("marker").castGroup()
            markerName = self._fieldmodule.findFieldByName("marker_name")
            if markerGroup.isValid():
                markerNodeset = markerGroup.getFieldNodeGroup(datapoints).getNodesetGroup()
                markerDataCoordinates = get_field_coordinates_on_nodeset(self._fieldmodule, markerNodeset, "coordinates") if markerNodeset.isValid() else None
            else:
                markerDataCoordinates = None

            # data points - nodes if any, otherwise datapoints

            points = self._scene.createGraphicsPoints()
            points.setFieldDomainType(Field.DOMAIN_TYPE_NODES if (nodes.getSize() > 0) else Field.DOMAIN_TYPE_DATAPOINTS)
            if coordinates:
                points.setCoordinateField(coordinates)
            pointattr = points.getGraphicspointattributes()
            if self.isDisplayDataRadius() and radius.isValid():
                pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
                pointattr.setBaseSize([ 0.0 ])
                pointattr.setScaleFactors([ 2.0 ])
                pointattr.setOrientationScaleField(radius)
            else:
                pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_POINT)
                points.setRenderPointSize(2.0)
                points.setMaterial(self._materialmodule.findMaterialByName("grey50"))
            points.setDataField(rgb)
            points.setSpectrum(self._rgbSpectrum)
            points.setName("displayDataPoints")
            points.setVisibilityFlag(self.isDisplayDataPoints())

            # data contours

            lines = self._scene.createGraphicsLines()
            if coordinates:
                lines.setCoordinateField(coordinates)
            if self.isDisplayDataRadius() and radius.isValid():
                lineattr = lines.getGraphicslineattributes()
                lineattr.setShapeType(lineattr.SHAPE_TYPE_CIRCLE_EXTRUSION)
                lineattr.setBaseSize([ 0.0 ])
                lineattr.setScaleFactors([ 2.0 ])
                lineattr.setOrientationScaleField(radius)
            lines.setDataField(rgb)
            lines.setSpectrum(self._rgbSpectrum)
            lines.setName("displayDataContours")
            lines.setVisibilityFlag(self.isDisplayDataContours())

            # data marker points, names

            markerPoints = self._scene.createGraphicsPoints()
            markerPoints.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
            markerPoints.setSubgroupField(markerGroup)
            if markerDataCoordinates:
                markerPoints.setCoordinateField(markerDataCoordinates)
            pointattr = markerPoints.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_POINT)
            markerPoints.setRenderPointSize(2.0)
            markerPoints.setMaterial(self._materialmodule.findMaterialByName("yellow"))
            markerPoints.setName("displayDataMarkerPoints")
            markerPoints.setVisibilityFlag(self.isDisplayDataMarkerPoints())

            markerNames = self._scene.createGraphicsPoints()
            markerNames.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
            markerNames.setSubgroupField(markerGroup)
            if markerDataCoordinates:
                markerNames.setCoordinateField(markerDataCoordinates)
            pointattr = markerNames.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_NONE)
            pointattr.setLabelText(1, " ")
            pointattr.setLabelField(markerName)
            markerNames.setMaterial(self._materialmodule.findMaterialByName("yellow"))
            markerNames.setName("displayDataMarkerNames")
            markerNames.setVisibilityFlag(self.isDisplayDataMarkerNames())
