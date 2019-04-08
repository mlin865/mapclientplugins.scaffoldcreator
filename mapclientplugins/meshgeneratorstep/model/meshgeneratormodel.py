"""
Created on 9 Mar, 2018 from mapclientplugins.meshgeneratorstep.

@author: Richard Christie
"""

from __future__ import division
import copy
import os
import string

from opencmiss.zinc.field import Field
from opencmiss.zinc.glyph import Glyph
from opencmiss.zinc.graphics import Graphics
from opencmiss.zinc.node import Node
from scaffoldmaker.scaffolds import Scaffolds
from scaffoldmaker.scaffoldpackage import ScaffoldPackage
from scaffoldmaker.utils.exportvtk import ExportVtk
from scaffoldmaker.utils.zinc_utils import *

STRING_FLOAT_FORMAT = '{:.8g}'


class MeshGeneratorModel(object):
    """
    Framework for generating meshes of a number of types, with mesh type specific options
    """

    def __init__(self, region, material_module):
        super(MeshGeneratorModel, self).__init__()
        self._region_name = "generated_mesh"
        self._parent_region = region
        self._materialmodule = material_module
        self._region = None
        self._annotationGroups = None
        self._sceneChangeCallback = None
        self._deleteElementRanges = []
        self._scale = [ 1.0, 1.0, 1.0 ]
        self._nodeDerivativeLabels = [ 'D1', 'D2', 'D3', 'D12', 'D13', 'D23', 'D123' ]
        self._settings = {
            'meshTypeName' : '',
            'meshTypeOptions' : { },
            'deleteElementRanges' : '',
            'scale' : '*'.join(STRING_FLOAT_FORMAT.format(value) for value in self._scale),
            'displayNodePoints' : False,
            'displayNodeNumbers' : False,
            'displayNodeDerivatives' : False,
            'displayNodeDerivativeLabels' : self._nodeDerivativeLabels[0:3],
            'displayLines' : True,
            'displayLinesExterior' : False,
            'displaySurfaces' : True,
            'displaySurfacesExterior' : True,
            'displaySurfacesTranslucent' : True,
            'displaySurfacesWireframe' : False,
            'displayElementNumbers' : False,
            'displayElementAxes' : False,
            'displayAxes' : True,
            'displayAnnotationPoints' : False
        }
        self._customMeshTypeOptions = None  # temporary storage of last custom mesh type options, to switch back to
        self._parameterSetName = None
        self._scaffoldPackages = []
        self._scaffoldPackageOptionNames = []
        # discover all mesh types and set the current from the default
        scaffolds = Scaffolds()
        self._allMeshTypes = scaffolds.getMeshTypes()
        # list of nested scaffold packages to that being edited, with their parent option names
        self._scaffoldPackages = []
        self._scaffoldPackageOptionNames = []
        self._setScaffoldType(scaffolds.getDefaultMeshType())

    def _setScaffoldType(self, scaffoldType):
        parentScaffoldType = self.getParentScaffoldType()
        if parentScaffoldType:
            optionName = self._scaffoldPackageOptionNames[-1]
            self._scaffoldPackages[-1].deepcopy(parentScaffoldType.getOptionScaffoldPackage(optionName, scaffoldType))
        else:
            self._currentMeshType = scaffoldType
            self._settings['meshTypeName'] = scaffoldType.getName()
            self._settings['meshTypeOptions'] = scaffoldType.getDefaultOptions()
        self._customMeshTypeOptions = None
        self._parameterSetName = self.getEditScaffoldParameterSetNames()[0]

    def setMeshTypeByName(self, name):
        meshType = self._getMeshTypeByName(name)
        if meshType is not None:
            parentScaffoldType = self.getParentScaffoldType()
            assert (not parentScaffoldType) or (meshType in parentScaffoldType.getOptionValidScaffoldTypes(self._scaffoldPackageOptionNames[-1])), 'Invalid scaffold type for parent scaffold'
            if meshType != self.getEditScaffoldType():
                self._setScaffoldType(meshType)
                self._generateMesh()

    def getAvailableMeshTypeNames(self):
        meshTypeNames = []
        parentScaffoldType = self.getParentScaffoldType()
        validScaffoldTypes = parentScaffoldType.getOptionValidScaffoldTypes(self._scaffoldPackageOptionNames[-1]) if parentScaffoldType else None
        for meshType in self._allMeshTypes:
            if (not parentScaffoldType) or (meshType in validScaffoldTypes):
                meshTypeNames.append(meshType.getName())
        return meshTypeNames

    def _getMeshTypeByName(self, name):
        for meshType in self._allMeshTypes:
            if meshType.getName() == name:
                return meshType
        return None

    def getMeshTypeName(self):
        return self.getEditScaffoldType().getName()

    def getRootScaffoldType(self):
        '''
        Get root scaffold type being edited, NOT including nested scaffolds.
        '''
        return self._currentMeshType

    def getEditScaffoldType(self):
        '''
        Get scaffold type currently being edited, including nested scaffolds.
        '''
        if self._scaffoldPackages:
            return self._scaffoldPackages[-1].getScaffoldType()
        return self._currentMeshType

    def getEditScaffoldSettings(self):
        '''
        Get settings for scaffold type currently being edited, including nested scaffolds.
        '''
        if self._scaffoldPackages:
            return self._scaffoldPackages[-1].getScaffoldSettings()
        return self._settings['meshTypeOptions']

    def getEditScaffoldOptionDisplayName(self):
        '''
        Get option display name for sub scaffold package being edited.
        '''
        return '/'.join(self._scaffoldPackageOptionNames)

    def getEditScaffoldOrderedOptionNames(self):
        return self.getEditScaffoldType().getOrderedOptionNames()

    def getEditScaffoldParameterSetNames(self):
        if self._scaffoldPackages:
            # may need to change if scaffolds nested two deep
            return self.getParentScaffoldType().getOptionScaffoldTypeParameterSetNames( \
                self._scaffoldPackageOptionNames[-1], self._scaffoldPackages[-1])
        return self._currentMeshType.getParameterSetNames()

    def getEditScaffoldDefaultOptions(self, parameterSetName):
        '''
        :return: Settings dict for root scaffold, ScaffoldPackage for sub-scaffold.
        '''
        if self._scaffoldPackages:
            # may need to change if scaffolds nested two deep
            return self.getParentScaffoldType().getOptionScaffoldPackage( \
                self._scaffoldPackageOptionNames[-1], self._scaffoldPackages[-1], parameterSetName)
        return self._currentMeshType.getDefaultOptions(parameterSetName)

    def getEditScaffoldOption(self, key):
        return self.getEditScaffoldSettings()[key]

    def getParentScaffoldType(self):
        '''
        :return: Parent scaffold type or None if top scaffold.
        '''
        if self._scaffoldPackages:
            if len(self._scaffoldPackages) > 1:
                return self._scaffoldPackages[-2].getScaffoldType()
            return self._currentMeshType
        return None

    def getParentScaffoldOption(self, key):
        assert self._scaffoldPackages
        if len(self._scaffoldPackages) > 1:
            parentScaffoldSettings = self._scaffoldPackages[-2].getScaffoldSettings()
        else:
            parentScaffoldSettings = self._settings['meshTypeOptions']
        return parentScaffoldSettings[key]

    def _checkCustomParameterSet(self):
        '''
        Work out whether settings are a particular named parameter set or custom
        '''
        self._customMeshTypeOptions = None
        self._parameterSetName = None
        if self._scaffoldPackages:
            scaffoldSettings = self.getParentScaffoldOption(self._scaffoldPackageOptionNames[-1])
        else:
            scaffoldSettings = self._settings['meshTypeOptions']
        for parameterSetName in reversed(self.getAvailableParameterSetNames()):
            tmpScaffoldSettings = self.getEditScaffoldDefaultOptions(parameterSetName)
            if scaffoldSettings == tmpScaffoldSettings:
                self._parameterSetName = parameterSetName
                break
        if not self._parameterSetName:
            self._customMeshTypeOptions = copy.deepcopy(scaffoldSettings)
            self._parameterSetName = 'Custom'

    def _clearMeshEdits(self):
        if self._scaffoldPackages:
            self._scaffoldPackages[-1].setMeshEdits(None)

    def editScaffoldPackageOption(self, optionName):
        '''
        Switch to editing a nested scaffold.
        '''
        settings = self.getEditScaffoldSettings()
        scaffoldPackage = settings.get(optionName)
        assert isinstance(scaffoldPackage, ScaffoldPackage), 'Option is not a ScaffoldPackage'
        self._scaffoldPackages.append(scaffoldPackage)
        self._scaffoldPackageOptionNames.append(optionName)
        self._checkCustomParameterSet()
        self._generateMesh()

    def endEditScaffoldPackageOption(self):
        '''
        End editing of the last ScaffoldPackage, moving up to parent or top scaffold type.
        '''
        assert self._scaffoldPackages, 'No currently edited ScaffoldPackage'
        self._scaffoldPackages.pop()
        self._scaffoldPackageOptionNames.pop()
        self._checkCustomParameterSet()
        self._generateMesh()

    def getAvailableParameterSetNames(self):
        parameterSetNames = self.getEditScaffoldParameterSetNames()
        if self._customMeshTypeOptions:
            parameterSetNames.insert(0, 'Custom')
        return parameterSetNames

    def getParameterSetName(self):
        '''
        :return: Name of currently active parameter set.
        '''
        return self._parameterSetName

    def setParameterSetName(self, parameterSetName):
        if parameterSetName == 'Custom':
            scaffoldSettings = copy.deepcopy(self._customMeshTypeOptions)
        else:
            scaffoldSettings = self.getEditScaffoldDefaultOptions(parameterSetName)
        if self._scaffoldPackages:
            self._scaffoldPackages[-1].deepcopy(scaffoldSettings)
        else:
            self._settings['meshTypeOptions'] = scaffoldSettings
        self._parameterSetName = parameterSetName
        self._generateMesh()

    def setMeshTypeOption(self, key, value):
        '''
        :return: True if other dependent options have changed, otherwise False.
        This happens when 
        On True return client is expected to refresh all option values in UI.
        '''
        scaffoldType = self.getEditScaffoldType()
        settings = self.getEditScaffoldSettings()
        oldValue = settings[key]
        # print('setMeshTypeOption: key ', key, ' value ', str(value))
        newValue = None
        try:
            if type(oldValue) is bool:
                newValue = bool(value)
            elif type(oldValue) is int:
                newValue = int(value)
            elif type(oldValue) is float:
                newValue = float(value)
            elif type(oldValue) is str:
                newValue = str(value)
            else:
                newValue = value
        except:
            print('setMeshTypeOption: Invalid value')
            return
        settings[key] = newValue
        dependentChanges = scaffoldType.checkOptions(settings)
        # print('final value = ', settings[key])
        if settings[key] != oldValue:
            self._customMeshTypeOptions = copy.deepcopy(settings)
            self._parameterSetName = 'Custom'
            self._clearMeshEdits()
            self._generateMesh()
        return dependentChanges

    def getDeleteElementsRangesText(self):
        return self._settings['deleteElementRanges']

    def _parseDeleteElementsRangesText(self, elementRangesTextIn):
        """
        :return: True if ranges changed, otherwise False
        """
        elementRanges = []
        for elementRangeText in elementRangesTextIn.split(','):
            try:
                elementRangeEnds = elementRangeText.split('-')
                # remove trailing non-numeric characters, workaround for select 's' key ending up there
                for e in range(len(elementRangeEnds)):
                    size = len(elementRangeEnds[e])
                    for i in range(size):
                        if elementRangeEnds[e][size - i - 1] in string.digits:
                            break;
                    if i > 0:
                        elementRangeEnds[e] = elementRangeEnds[e][:(size - i)]
                elementRangeStart = int(elementRangeEnds[0])
                if len(elementRangeEnds) > 1:
                    elementRangeStop = int(elementRangeEnds[1])
                else:
                    elementRangeStop = elementRangeStart
                if elementRangeStop >= elementRangeStart:
                    elementRanges.append([elementRangeStart, elementRangeStop])
                else:
                    elementRanges.append([elementRangeStop, elementRangeStart])
            except:
                pass
        elementRanges.sort()
        elementRangesText = ''
        first = True
        for elementRange in elementRanges:
            if first:
                first = False
            else:
                elementRangesText += ','
            elementRangesText += str(elementRange[0])
            if elementRange[1] != elementRange[0]:
                elementRangesText += '-' + str(elementRange[1])
        changed = self._deleteElementRanges != elementRanges
        self._deleteElementRanges = elementRanges
        self._settings['deleteElementRanges'] = elementRangesText
        return changed

    def setDeleteElementsRangesText(self, elementRangesTextIn):
        if self._parseDeleteElementsRangesText(elementRangesTextIn):
            self._generateMesh()

    def getScaleText(self):
        return self._settings['scale']

    def _parseScaleText(self, scaleTextIn):
        """
        :return: True if scale changed, otherwise False
        """
        scale = []
        for valueText in scaleTextIn.split('*'):
            try:
                scale.append(float(valueText))
            except:
                scale.append(1.0)
        for i in range(3 - len(scale)):
            scale.append(scale[-1])
        if len(scale) > 3:
            scale = scale[:3]
        scaleText = '*'.join(STRING_FLOAT_FORMAT.format(value) for value in scale)
        changed = self._scale != scale
        self._scale = scale
        self._settings['scale'] = scaleText
        return changed

    def setScaleText(self, scaleTextIn):
        if self._parseScaleText(scaleTextIn):
            self._generateMesh()

    def registerSceneChangeCallback(self, sceneChangeCallback):
        self._sceneChangeCallback = sceneChangeCallback

    def _getVisibility(self, graphicsName):
        return self._settings[graphicsName]

    def _setVisibility(self, graphicsName, show):
        self._settings[graphicsName] = show
        graphics = self._region.getScene().findGraphicsByName(graphicsName)
        graphics.setVisibilityFlag(show)

    def isDisplayAnnotationPoints(self):
        return self._getVisibility('displayAnnotationPoints')

    def setDisplayAnnotationPoints(self, show):
        self._setVisibility('displayAnnotationPoints', show)
        self._setVisibility('displayAnnotationPointsEmbedded', show)

    def isDisplayAxes(self):
        return self._getVisibility('displayAxes')

    def setDisplayAxes(self, show):
        self._setVisibility('displayAxes', show)

    def isDisplayElementNumbers(self):
        return self._getVisibility('displayElementNumbers')

    def setDisplayElementNumbers(self, show):
        self._setVisibility('displayElementNumbers', show)

    def isDisplayLines(self):
        return self._getVisibility('displayLines')

    def setDisplayLines(self, show):
        self._setVisibility('displayLines', show)

    def isDisplayLinesExterior(self):
        return self._settings['displayLinesExterior']

    def setDisplayLinesExterior(self, isExterior):
        self._settings['displayLinesExterior'] = isExterior
        lines = self._region.getScene().findGraphicsByName('displayLines')
        lines.setExterior(self.isDisplayLinesExterior())

    def isDisplayNodeDerivatives(self):
        return self._getVisibility('displayNodeDerivatives')

    def setDisplayNodeDerivatives(self, show):
        self._settings['displayNodeDerivatives'] = show
        for nodeDerivativeLabel in self._nodeDerivativeLabels:
            graphics = self._region.getScene().findGraphicsByName('displayNodeDerivatives' + nodeDerivativeLabel)
            graphics.setVisibilityFlag(show and self.isDisplayNodeDerivativeLabels(nodeDerivativeLabel))

    def isDisplayNodeDerivativeLabels(self, nodeDerivativeLabel):
        '''
        :param nodeDerivativeLabel: Label from self._nodeDerivativeLabels ('D1', 'D2' ...)
        '''
        return nodeDerivativeLabel in self._settings['displayNodeDerivativeLabels']

    def setDisplayNodeDerivativeLabels(self, nodeDerivativeLabel, show):
        '''
        :param nodeDerivativeLabel: Label from self._nodeDerivativeLabels ('D1', 'D2' ...)
        '''
        shown = nodeDerivativeLabel in self._settings['displayNodeDerivativeLabels']
        if show:
            if not shown:
                # keep in same order as self._nodeDerivativeLabels
                nodeDerivativeLabels = []
                for label in self._nodeDerivativeLabels:
                    if (label == nodeDerivativeLabel) or self.isDisplayNodeDerivativeLabels(label):
                        nodeDerivativeLabels.append(label)
                self._settings['displayNodeDerivativeLabels'] = nodeDerivativeLabels
        else:
            if shown:
                self._settings['displayNodeDerivativeLabels'].remove(nodeDerivativeLabel)
        graphics = self._region.getScene().findGraphicsByName('displayNodeDerivatives' + nodeDerivativeLabel)
        graphics.setVisibilityFlag(show and self.isDisplayNodeDerivatives())

    def isDisplayNodeNumbers(self):
        return self._getVisibility('displayNodeNumbers')

    def setDisplayNodeNumbers(self, show):
        self._setVisibility('displayNodeNumbers', show)

    def isDisplayNodePoints(self):
        return self._getVisibility('displayNodePoints')

    def setDisplayNodePoints(self, show):
        self._setVisibility('displayNodePoints', show)

    def isDisplaySurfaces(self):
        return self._getVisibility('displaySurfaces')

    def setDisplaySurfaces(self, show):
        self._setVisibility('displaySurfaces', show)

    def isDisplaySurfacesExterior(self):
        return self._settings['displaySurfacesExterior']

    def setDisplaySurfacesExterior(self, isExterior):
        self._settings['displaySurfacesExterior'] = isExterior
        surfaces = self._region.getScene().findGraphicsByName('displaySurfaces')
        surfaces.setExterior(self.isDisplaySurfacesExterior() if (self.getMeshDimension() == 3) else False)

    def isDisplaySurfacesTranslucent(self):
        return self._settings['displaySurfacesTranslucent']

    def setDisplaySurfacesTranslucent(self, isTranslucent):
        self._settings['displaySurfacesTranslucent'] = isTranslucent
        surfaces = self._region.getScene().findGraphicsByName('displaySurfaces')
        surfacesMaterial = self._materialmodule.findMaterialByName('trans_blue' if isTranslucent else 'solid_blue')
        surfaces.setMaterial(surfacesMaterial)

    def isDisplaySurfacesWireframe(self):
        return self._settings['displaySurfacesWireframe']

    def setDisplaySurfacesWireframe(self, isWireframe):
        self._settings['displaySurfacesWireframe'] = isWireframe
        surfaces = self._region.getScene().findGraphicsByName('displaySurfaces')
        surfaces.setRenderPolygonMode(Graphics.RENDER_POLYGON_MODE_WIREFRAME if isWireframe else Graphics.RENDER_POLYGON_MODE_SHADED)

    def isDisplayElementAxes(self):
        return self._getVisibility('displayElementAxes')

    def setDisplayElementAxes(self, show):
        self._setVisibility('displayElementAxes', show)

    def needPerturbLines(self):
        """
        Return if solid surfaces are drawn with lines, requiring perturb lines to be activated.
        """
        if self._region is None:
            return False
        mesh2d = self._region.getFieldmodule().findMeshByDimension(2)
        if mesh2d.getSize() == 0:
            return False
        return self.isDisplayLines() and self.isDisplaySurfaces() and not self.isDisplaySurfacesTranslucent()

    def _getMesh(self):
        fm = self._region.getFieldmodule()
        for dimension in range(3,0,-1):
            mesh = fm.findMeshByDimension(dimension)
            if mesh.getSize() > 0:
                break
        if mesh.getSize() == 0:
            mesh = fm.findMeshByDimension(3)
        return mesh

    def getMeshDimension(self):
        return self._getMesh().getDimension()

    def getNodeLocation(self, node_id):
        fm = self._region.getFieldmodule()
        fm.beginChange()
        coordinates = fm.findFieldByName('coordinates')
        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        node = nodes.findNodeByIdentifier(node_id)
        fc = fm.createFieldcache()
        fc.setNode(node)
        _, position = coordinates.evaluateReal(fc, 3)
        fm.endChange()

        return self._getSceneTransformationFromAdjustedPosition(position)

    def getSettings(self):
        return self._settings

    def setSettings(self, settings):
        '''
        Called on loading settings from file.
        '''
        self._settings.update(settings)
        self._currentMeshType = self._getMeshTypeByName(self._settings['meshTypeName'])
        # merge any new options for this generator
        savedMeshTypeOptions = self._settings['meshTypeOptions']
        self._settings['meshTypeOptions'] = self._currentMeshType.getDefaultOptions()
        self._settings['meshTypeOptions'].update(savedMeshTypeOptions)
        self._parseDeleteElementsRangesText(self._settings['deleteElementRanges'])
        self._parseScaleText(self._settings['scale'])
        self._scaffoldPackages = []
        self._scaffoldPackageOptionNames = []
        self._checkCustomParameterSet()
        self._generateMesh()

    def _generateMesh(self):
        scaffoldType = self.getEditScaffoldType()
        scaffoldSettings = self.getEditScaffoldSettings()
        isRootScaffold = not self._scaffoldPackages
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        self._scene = self._region.getScene()
        fm = self._region.getFieldmodule()
        fm.beginChange()
        # logger = self._context.getLogger()
        if self._scaffoldPackages:
            annotationGroups = self._scaffoldPackages[-1].generate(self._region)
        else:
            annotationGroups = scaffoldType.generateMesh(self._region, scaffoldSettings)
        # loggerMessageCount = logger.getNumberOfMessages()
        # if loggerMessageCount > 0:
        #     for i in range(1, loggerMessageCount + 1):
        #         print(logger.getMessageTypeAtIndex(i), logger.getMessageTextAtIndex(i))
        #     logger.removeAllMessages()
        mesh = self._getMesh()
        # meshDimension = mesh.getDimension()
        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        if isRootScaffold and (len(self._deleteElementRanges) > 0):
            deleteElementIdentifiers = []
            elementIter = mesh.createElementiterator()
            element = elementIter.next()
            while element.isValid():
                identifier = element.getIdentifier()
                for deleteElementRange in self._deleteElementRanges:
                    if (identifier >= deleteElementRange[0]) and (identifier <= deleteElementRange[1]):
                        deleteElementIdentifiers.append(identifier)
                element = elementIter.next()
            #print('delete elements ', deleteElementIdentifiers)
            for identifier in deleteElementIdentifiers:
                element = mesh.findElementByIdentifier(identifier)
                mesh.destroyElement(element)
            del element
            # destroy all orphaned nodes
            #size1 = nodes.getSize()
            nodes.destroyAllNodes()
            #size2 = nodes.getSize()
            #print('deleted', size1 - size2, 'nodes')
        fm.defineAllFaces()
        if annotationGroups is not None:
            for annotationGroup in annotationGroups:
                annotationGroup.addSubelements()
        self._annotationGroups = annotationGroups
        if isRootScaffold and (self._settings['scale'] != '1*1*1'):
            coordinates = fm.findFieldByName('coordinates').castFiniteElement()
            scale = fm.createFieldConstant(self._scale)
            newCoordinates = fm.createFieldMultiply(coordinates, scale)
            fieldassignment = coordinates.createFieldassignment(newCoordinates)
            fieldassignment.assign()
            del newCoordinates
            del scale
        fm.endChange()
        self._createGraphics(self._region)
        if self._sceneChangeCallback is not None:
            self._sceneChangeCallback()

    def _getNodeCoordinatesRange(self, coordinates):
        '''
        :return: min, max range of coordinates field over nodes.
        '''
        fm = coordinates.getFieldmodule()
        fm.beginChange()
        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        minCoordinates = fm.createFieldNodesetMinimum(coordinates, nodes)
        maxCoordinates = fm.createFieldNodesetMaximum(coordinates, nodes)
        componentsCount = coordinates.getNumberOfComponents()
        cache = fm.createFieldcache()
        result, minX = minCoordinates.evaluateReal(cache, componentsCount)
        result, maxX = maxCoordinates.evaluateReal(cache, componentsCount)
        minCoordinates = maxCoordinates = None
        cache = None
        fm.endChange()
        return minX, maxX

    def _createGraphics(self, region):
        fm = region.getFieldmodule()
        fm.beginChange()
        meshDimension = self.getMeshDimension()
        coordinates = fm.findFieldByName('coordinates')
        componentsCount = coordinates.getNumberOfComponents()
        # fields in same order as self._nodeDerivativeLabels
        nodeDerivativeFields = [
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D_DS1, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D_DS2, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D_DS3, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D2_DS1DS2, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D2_DS1DS3, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D2_DS2DS3, 1),
            fm.createFieldNodeValue(coordinates, Node.VALUE_LABEL_D3_DS1DS2DS3, 1)
        ]
        elementDerivativeFields = []
        for d in range(meshDimension):
            elementDerivativeFields.append(fm.createFieldDerivative(coordinates, d + 1))
        elementDerivativesField = fm.createFieldConcatenate(elementDerivativeFields)
        cmiss_number = fm.findFieldByName('cmiss_number')
        dataCoordinates = getOrCreateCoordinateField(fm, 'data_coordinates')
        dataLabel = getOrCreateLabelField(fm, 'data_label')
        dataElementXi = getOrCreateElementXiField(fm, 'data_element_xi')
        dataHostCoordinates = fm.createFieldEmbedded(coordinates, dataElementXi)

        # get sizing for axes
        axesScale = 1.0
        minX, maxX = self._getNodeCoordinatesRange(coordinates)
        if componentsCount == 1:
            maxRange = maxX - minX
        else:
            maxRange = maxX[0] - minX[0]
            for c in range(1, componentsCount):
                maxRange = max(maxRange, maxX[c] - minX[c])
        if maxRange > 0.0:
            while axesScale*10.0 < maxRange:
                axesScale *= 10.0
            while axesScale*0.1 > maxRange:
                axesScale *= 0.1

        # fixed width glyph size is based on average element size in all dimensions
        mesh1d = fm.findMeshByDimension(1)
        meanLineLength = 0.0
        lineCount = mesh1d.getSize()
        if lineCount > 0:
            one = fm.createFieldConstant(1.0)
            sumLineLength = fm.createFieldMeshIntegral(one, coordinates, mesh1d)
            cache = fm.createFieldcache()
            result, totalLineLength = sumLineLength.evaluateReal(cache, 1)
            glyphWidth = 0.1*totalLineLength/lineCount
            del cache
            del sumLineLength
            del one
        if (lineCount == 0) or (glyphWidth == 0.0):
            # use function of coordinate range if no elements
            if componentsCount == 1:
                maxScale = maxX - minX
            else:
                first = True
                for c in range(componentsCount):
                    scale = maxX[c] - minX[c]
                    if first or (scale > maxScale):
                        maxScale = scale
                        first = False
            if maxScale == 0.0:
                maxScale = 1.0
            glyphWidth = 0.01*maxScale

        # make graphics
        scene = region.getScene()
        scene.beginChange()

        axes = scene.createGraphicsPoints()
        pointattr = axes.getGraphicspointattributes()
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_AXES_XYZ)
        pointattr.setBaseSize([ axesScale, axesScale, axesScale ])
        pointattr.setLabelText(1, '  ' + str(axesScale))
        axes.setMaterial(self._materialmodule.findMaterialByName('grey50'))
        axes.setName('displayAxes')
        axes.setVisibilityFlag(self.isDisplayAxes())

        lines = scene.createGraphicsLines()
        lines.setCoordinateField(coordinates)
        lines.setExterior(self.isDisplayLinesExterior())
        lines.setName('displayLines')
        lines.setVisibilityFlag(self.isDisplayLines())

        nodePoints = scene.createGraphicsPoints()
        nodePoints.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
        nodePoints.setCoordinateField(coordinates)
        pointattr = nodePoints.getGraphicspointattributes()
        pointattr.setBaseSize([glyphWidth, glyphWidth, glyphWidth])
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
        nodePoints.setMaterial(self._materialmodule.findMaterialByName('white'))
        nodePoints.setName('displayNodePoints')
        nodePoints.setVisibilityFlag(self.isDisplayNodePoints())

        nodeNumbers = scene.createGraphicsPoints()
        nodeNumbers.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
        nodeNumbers.setCoordinateField(coordinates)
        pointattr = nodeNumbers.getGraphicspointattributes()
        pointattr.setLabelField(cmiss_number)
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_NONE)
        nodeNumbers.setMaterial(self._materialmodule.findMaterialByName('green'))
        nodeNumbers.setName('displayNodeNumbers')
        nodeNumbers.setVisibilityFlag(self.isDisplayNodeNumbers())

        # names in same order as self._nodeDerivativeLabels 'D1', 'D2', 'D3', 'D12', 'D13', 'D23', 'D123' and nodeDerivativeFields
        nodeDerivativeMaterialNames = [ 'gold', 'silver', 'green', 'cyan', 'magenta', 'yellow', 'blue' ]
        derivativeScales = [ 1.0, 1.0, 1.0, 0.5, 0.5, 0.5, 0.25 ]
        for i in range(len(self._nodeDerivativeLabels)):
            nodeDerivativeLabel = self._nodeDerivativeLabels[i]
            nodeDerivatives = scene.createGraphicsPoints()
            nodeDerivatives.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
            nodeDerivatives.setCoordinateField(coordinates)
            pointattr = nodeDerivatives.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_ARROW_SOLID)
            pointattr.setOrientationScaleField(nodeDerivativeFields[i])
            pointattr.setBaseSize([0.0, glyphWidth, glyphWidth])
            pointattr.setScaleFactors([ derivativeScales[i], 0.0, 0.0 ])
            material = self._materialmodule.findMaterialByName(nodeDerivativeMaterialNames[i])
            nodeDerivatives.setMaterial(material)
            nodeDerivatives.setSelectedMaterial(material)
            nodeDerivatives.setName('displayNodeDerivatives' + nodeDerivativeLabel)
            nodeDerivatives.setVisibilityFlag(self.isDisplayNodeDerivatives() and self.isDisplayNodeDerivativeLabels(nodeDerivativeLabel))

        elementNumbers = scene.createGraphicsPoints()
        elementNumbers.setFieldDomainType(Field.DOMAIN_TYPE_MESH_HIGHEST_DIMENSION)
        elementNumbers.setCoordinateField(coordinates)
        pointattr = elementNumbers.getGraphicspointattributes()
        pointattr.setLabelField(cmiss_number)
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_NONE)
        elementNumbers.setMaterial(self._materialmodule.findMaterialByName('cyan'))
        elementNumbers.setName('displayElementNumbers')
        elementNumbers.setVisibilityFlag(self.isDisplayElementNumbers())
        surfaces = scene.createGraphicsSurfaces()
        surfaces.setCoordinateField(coordinates)
        surfaces.setRenderPolygonMode(Graphics.RENDER_POLYGON_MODE_WIREFRAME if self.isDisplaySurfacesWireframe() else Graphics.RENDER_POLYGON_MODE_SHADED)
        surfaces.setExterior(self.isDisplaySurfacesExterior() if (meshDimension == 3) else False)
        surfacesMaterial = self._materialmodule.findMaterialByName('trans_blue' if self.isDisplaySurfacesTranslucent() else 'solid_blue')
        surfaces.setMaterial(surfacesMaterial)
        surfaces.setName('displaySurfaces')
        surfaces.setVisibilityFlag(self.isDisplaySurfaces())

        elementAxes = scene.createGraphicsPoints()
        elementAxes.setFieldDomainType(Field.DOMAIN_TYPE_MESH_HIGHEST_DIMENSION)
        elementAxes.setCoordinateField(coordinates)
        pointattr = elementAxes.getGraphicspointattributes()
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_AXES_123)
        pointattr.setOrientationScaleField(elementDerivativesField)
        if meshDimension == 1:
            pointattr.setBaseSize([0.0, 2*glyphWidth, 2*glyphWidth])
            pointattr.setScaleFactors([0.25, 0.0, 0.0])
        elif meshDimension == 2:
            pointattr.setBaseSize([0.0, 0.0, 2*glyphWidth])
            pointattr.setScaleFactors([0.25, 0.25, 0.0])
        else:
            pointattr.setBaseSize([0.0, 0.0, 0.0])
            pointattr.setScaleFactors([0.25, 0.25, 0.25])
        elementAxes.setMaterial(self._materialmodule.findMaterialByName('yellow'))
        elementAxes.setName('displayElementAxes')
        elementAxes.setVisibilityFlag(self.isDisplayElementAxes())

        # annotation points
        annotationPoints = scene.createGraphicsPoints()
        annotationPoints.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
        annotationPoints.setCoordinateField(dataCoordinates)
        pointattr = annotationPoints.getGraphicspointattributes()
        pointattr.setLabelText(1, '  ')
        pointattr.setLabelField(dataLabel)
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_CROSS)
        pointattr.setBaseSize(2*glyphWidth)
        annotationPoints.setMaterial(self._materialmodule.findMaterialByName('green'))
        annotationPoints.setName('displayAnnotationPoints')
        annotationPoints.setVisibilityFlag(self.isDisplayAnnotationPoints())

        annotationPoints = scene.createGraphicsPoints()
        annotationPoints.setFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
        annotationPoints.setCoordinateField(dataHostCoordinates)
        pointattr = annotationPoints.getGraphicspointattributes()
        pointattr.setLabelText(1, '  ')
        pointattr.setLabelField(dataLabel)
        pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_CROSS)
        pointattr.setBaseSize(2*glyphWidth)
        annotationPoints.setMaterial(self._materialmodule.findMaterialByName('yellow'))
        annotationPoints.setName('displayAnnotationPointsEmbedded')
        annotationPoints.setVisibilityFlag(self.isDisplayAnnotationPoints())

        fm.endChange()
        scene.endChange()

    def writeModel(self, file_name):
        self._region.writeFile(file_name)

    def exportToVtk(self, filenameStem):
        base_name = os.path.basename(filenameStem)
        description = 'Scaffold ' + self._currentMeshType.getName() + ': ' + base_name
        exportvtk = ExportVtk(self._region, description, self._annotationGroups)
        exportvtk.writeFile(filenameStem + '.vtk')
