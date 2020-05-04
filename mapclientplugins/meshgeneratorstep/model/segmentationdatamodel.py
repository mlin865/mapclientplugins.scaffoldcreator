from opencmiss.utils.zinc.general import ChangeManager
from opencmiss.zinc.field import Field
from opencmiss.zinc.glyph import Glyph
from opencmiss.zinc.result import RESULT_OK
from opencmiss.zinc.spectrum import Spectrum, Spectrumcomponent

STRING_FLOAT_FORMAT = '{:.8g}'


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
        #with ChangeManager(self._region.
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

            markerGroup = self._fieldmodule.findFieldByName("marker").castGroup()
            markerName = self._fieldmodule.findFieldByName("marker_name")
            coordinates = self._fieldmodule.findFieldByName("coordinates")
            radius = self._fieldmodule.findFieldByName("radius")
            rgb = self._fieldmodule.findFieldByName("rgb")

            # data contours

            lines = self._scene.createGraphicsLines()
            lines.setCoordinateField(coordinates)
            lines.setDataField(rgb)
            lines.setSpectrum(self._rgbSpectrum)
            lines.setName("displayDataContours")
            lines.setVisibilityFlag(self.isDisplayDataContours())

            # data marker points, names

            markerPoints = self._scene.createGraphicsPoints()
            markerPoints.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
            markerPoints.setSubgroupField(markerGroup)
            markerPoints.setCoordinateField(coordinates)
            pointattr = markerPoints.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_POINT)
            markerPoints.setRenderPointSize(2.0)
            markerPoints.setMaterial(self._materialmodule.findMaterialByName("yellow"))
            markerPoints.setName("displayDataMarkerPoints")
            markerPoints.setVisibilityFlag(self.isDisplayDataMarkerPoints())

            markerNames = self._scene.createGraphicsPoints()
            markerNames.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
            markerNames.setSubgroupField(markerGroup)
            markerNames.setCoordinateField(coordinates)
            pointattr = markerNames.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_NONE)
            pointattr.setLabelText(1, " ")
            pointattr.setLabelField(markerName)
            markerNames.setMaterial(self._materialmodule.findMaterialByName("yellow"))
            markerNames.setName("displayDataMarkerNames")
            markerNames.setVisibilityFlag(self.isDisplayDataMarkerNames())
