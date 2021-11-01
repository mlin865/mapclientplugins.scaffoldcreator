"""
Mesh generator class. Generates Zinc meshes using scaffoldmaker.
"""

from __future__ import division
import copy
import os
import math

from opencmiss.maths.vectorops import axis_angle_to_rotation_matrix, euler_to_rotation_matrix, matrix_mult, rotation_matrix_to_euler
from opencmiss.utils.zinc.field import findOrCreateFieldStoredMeshLocation, findOrCreateFieldStoredString, fieldIsManagedCoordinates
from opencmiss.utils.zinc.finiteelement import evaluateFieldNodesetRange
from opencmiss.utils.zinc.general import ChangeManager

from opencmiss.zinc.field import Field, FieldGroup
from opencmiss.zinc.glyph import Glyph
from opencmiss.zinc.graphics import Graphics
from opencmiss.zinc.node import Node
from opencmiss.zinc.result import RESULT_OK, RESULT_WARNING_PART_DONE
from opencmiss.zinc.scene import Scene
from opencmiss.zinc.scenecoordinatesystem import SCENECOORDINATESYSTEM_WORLD
from scaffoldmaker.annotation.annotationgroup import AnnotationGroup, findAnnotationGroupByName
from scaffoldmaker.scaffolds import Scaffolds
from scaffoldmaker.scaffoldpackage import ScaffoldPackage
from scaffoldmaker.utils.exportvtk import ExportVtk
from scaffoldmaker.utils.zinc_utils import group_add_group_elements, group_get_highest_dimension, \
    identifier_ranges_fix, identifier_ranges_from_string, identifier_ranges_to_string, mesh_group_to_identifier_ranges

STRING_FLOAT_FORMAT = '{:.8g}'


def parseListFloat(text: str, delimiter=','):
    """
    Parse a delimited list of floats from text.
    :param text: string containing floats separated by delimiter.
    :param delimiter: character delimiter between component values.
    :return: list of floats parsed from text.
    """
    values = []
    for s in text.split(delimiter):
        try:
            values.append(float(s))
        except:
            print('Invalid float')
            values.append(0.0)
    return values


def parseListInt(text: str, delimiter=','):
    """
    Parse a delimited list of integers from text.
    :param text: string containing integers separated by delimiter.
    :param delimiter: character delimiter between component values.
    :return: list of integers parsed from text.
    """
    values = []
    for s in text.split(delimiter):
        try:
            values.append(int(s))
        except:
            print('Invalid integer')
            values.append(0)
    return values


def parseVector3(vectorText: str, delimiter, defaultValue):
    """
    Parse a 3 component vector from a string.
    Repeats last component if too few.
    :param vectorText: string containing vector components separated by delimiter.
    :param delimiter: character delimiter between component values.
    :param defaultValue: Value to use for invalid components.
    :return: list of 3 component values parsed from vectorText.
    """
    vector = []
    for valueText in vectorText.split(delimiter):
        try:
            vector.append(float(valueText))
        except:
            vector.append(defaultValue)
    if len(vector) > 3:
        vector = vector[:3]
    else:
        for i in range(3 - len(vector)):
            vector.append(vector[-1])
    return vector


class MeshGeneratorModel(object):
    """
    Framework for generating meshes of a number of types, with mesh type specific options
    """

    def __init__(self, context, region, material_module):
        super(MeshGeneratorModel, self).__init__()
        self._region_name = "generated_mesh"
        self._context = context
        self._parent_region = region
        self._materialmodule = material_module
        self._region = None
        self._modelCoordinatesField = None
        self._fieldmodulenotifier = None
        self._currentAnnotationGroup = None
        self._customParametersCallback = None
        self._sceneChangeCallback = None
        self._transformationChangeCallback = None
        self._deleteElementRanges = []
        self._nodeDerivativeLabels = ['D1', 'D2', 'D3', 'D12', 'D13', 'D23', 'D123']
        # list of nested scaffold packages to that being edited, with their parent option names
        # discover all mesh types and set the current from the default
        scaffolds = Scaffolds()
        self._allScaffoldTypes = scaffolds.getScaffoldTypes()
        scaffoldType = scaffolds.getDefaultScaffoldType()
        scaffoldPackage = ScaffoldPackage(scaffoldType)
        self._parameterSetName = scaffoldType.getParameterSetNames()[0]
        self._scaffoldPackages = [scaffoldPackage]
        self._scaffoldPackageOptionNames = [None]
        self._settings = {
            'scaffoldPackage': scaffoldPackage,
            'deleteElementRanges': '',
            'displayNodePoints': False,
            'displayNodeNumbers': False,
            'displayNodeDerivatives': 0,  # tri-state: 0=show none, 1=show selected, 2=show all
            'displayNodeDerivativeLabels': self._nodeDerivativeLabels[0:3],
            'displayLines': True,
            'displayLinesExterior': False,
            'displayModelRadius': False,
            'displaySurfaces': True,
            'displaySurfacesExterior': True,
            'displaySurfacesTranslucent': True,
            'displaySurfacesWireframe': False,
            'displayElementNumbers': False,
            'displayElementAxes': False,
            'displayAxes': True,
            'displayMarkerPoints': False,
            'modelCoordinatesField': 'coordinates'
        }
        self._customScaffoldPackage = None  # temporary storage of custom mesh options and edits, to switch back to
        self._unsavedNodeEdits = False  # Whether nodes have been edited since ScaffoldPackage meshEdits last updated

    def _updateScaffoldEdits(self):
        """
        Ensure mesh and annotation group edits are up-to-date.
        """
        if self._unsavedNodeEdits:
            self._scaffoldPackages[-1].setMeshEdits(exnodeStringFromGroup(self._region, 'meshEdits', ['coordinates']))
            self._unsavedNodeEdits = False
        self._scaffoldPackages[-1].updateUserAnnotationGroups()

    def _saveCustomScaffoldPackage(self):
        """
        Copy current ScaffoldPackage to custom ScaffoldPackage to be able to switch back to later.
        """
        self._updateScaffoldEdits()
        self._customScaffoldPackage = copy.deepcopy(self._scaffoldPackages[-1])

    def _useCustomScaffoldPackage(self):
        if (not self._customScaffoldPackage) or (self._parameterSetName != 'Custom'):
            self._saveCustomScaffoldPackage()
            self._parameterSetName = 'Custom'
            if self._customParametersCallback:
                self._customParametersCallback()

    def getRegion(self):
        return self._region

    def _resetModelCoordinatesField(self):
        self._modelCoordinatesField = None

    def _setModelCoordinatesField(self, modelCoordinatesField):
        if modelCoordinatesField:
            self._modelCoordinatesField = modelCoordinatesField.castFiniteElement()
            if self._modelCoordinatesField.isValid():
                self._settings['modelCoordinatesField'] = modelCoordinatesField.getName()
                return
        # reset
        self._modelCoordinatesField = None
        self._settings['modelCoordinatesField'] = "coordinates"

    def _discoverModelCoordinatesField(self):
        """
        Discover new model coordintes field by previous name or default "coordinates" or first found.
        """
        fieldmodule = self._region.getFieldmodule()
        modelCoordinatesField = fieldmodule.findFieldByName(self._settings['modelCoordinatesField'])
        if not fieldIsManagedCoordinates(modelCoordinatesField):
            if self._settings['modelCoordinatesField'] != "coordinates":
                modelCoordinatesField = fieldmodule.findFieldByName("coordinates").castFiniteElement()
            if not fieldIsManagedCoordinates(modelCoordinatesField):
                fieldIter = fieldmodule.createFielditerator()
                field = fieldIter.next()
                while field.isValid():
                    if fieldIsManagedCoordinates(field):
                        modelCoordinatesField = field.castFiniteElement()
                        break
                    field = fieldIter.next()
                else:
                    modelCoordinatesField = None
        self._setModelCoordinatesField(modelCoordinatesField)

    def getModelCoordinatesField(self):
        return self._modelCoordinatesField

    def setModelCoordinatesField(self, modelCoordinatesField):
        """
        For outside use, sets field and rebuilds graphics.
        """
        self._setModelCoordinatesField(modelCoordinatesField)
        if not self._modelCoordinatesField:
            self._discoverModelCoordinatesField()
        self._createGraphics()

    def getMeshEditsGroup(self):
        fm = self._region.getFieldmodule()
        return fm.findFieldByName('meshEdits').castGroup()

    def getOrCreateMeshEditsNodesetGroup(self, nodeset):
        """
        Someone is about to edit a node, and must add the modified node to this nodesetGroup.
        """
        fm = self._region.getFieldmodule()
        with ChangeManager(fm):
            group = fm.findFieldByName('meshEdits').castGroup()
            if not group.isValid():
                group = fm.createFieldGroup()
                group.setName('meshEdits')
                group.setManaged(True)
            self._unsavedNodeEdits = True
            self._useCustomScaffoldPackage()
            fieldNodeGroup = group.getFieldNodeGroup(nodeset)
            if not fieldNodeGroup.isValid():
                fieldNodeGroup = group.createFieldNodeGroup(nodeset)
            nodesetGroup = fieldNodeGroup.getNodesetGroup()
        return nodesetGroup

    def interactionRotate(self, axis, angle):
        mat1 = axis_angle_to_rotation_matrix(axis, angle)
        mat2 = euler_to_rotation_matrix([deg * math.pi / 180.0 for deg in self._scaffoldPackages[-1].getRotation()])
        newmat = matrix_mult(mat1, mat2)
        rotation = [rad * 180.0 / math.pi for rad in rotation_matrix_to_euler(newmat)]
        if self._scaffoldPackages[-1].setRotation(rotation):
            self._setGraphicsTransformation()
            if self._transformationChangeCallback:
                self._transformationChangeCallback()

    def interactionScale(self, uniformScale):
        scale = self._scaffoldPackages[-1].getScale()
        if self._scaffoldPackages[-1].setScale([(scale[i] * uniformScale) for i in range(3)]):
            self._setGraphicsTransformation()
            if self._transformationChangeCallback:
                self._transformationChangeCallback()

    def interactionTranslate(self, offset):
        translation = self._scaffoldPackages[-1].getTranslation()
        if self._scaffoldPackages[-1].setTranslation([(translation[i] + offset[i]) for i in range(3)]):
            self._setGraphicsTransformation()
            if self._transformationChangeCallback:
                self._transformationChangeCallback()

    def interactionEnd(self):
        pass

    def getAnnotationGroups(self):
        """
        :return: Alphabetically sorted list of annotation group names.
        """
        return self._scaffoldPackages[-1].getAnnotationGroups()

    def createUserAnnotationGroup(self):
        """
        Create a new annotation group with automatic name, define it from
        the current selection and set it as the current annotation group.
        :return: New annotation group.
        """
        self._currentAnnotationGroup = self._scaffoldPackages[-1].createUserAnnotationGroup()
        self.redefineCurrentAnnotationGroupFromSelection()
        return self._currentAnnotationGroup

    def deleteAnnotationGroup(self, annotationGroup):
        """
        Delete the annotation group. If the current annotation group is deleted, set an empty group.
        :return: True on success, otherwise False
        """
        if self._scaffoldPackages[-1].deleteAnnotationGroup(annotationGroup):
            if annotationGroup is self._currentAnnotationGroup:
                self.setCurrentAnnotationGroup(None)
            return True
        print('Cannot delete annotation group')
        return False

    def redefineCurrentAnnotationGroupFromSelection(self):
        if not self._currentAnnotationGroup:
            return False
        scene = self._region.getScene()
        group = self._currentAnnotationGroup.getGroup()
        group.clear()
        selectionGroup = get_scene_selection_group(scene)
        if selectionGroup:
            fieldmodule = self._region.getFieldmodule()
            with ChangeManager(fieldmodule):
                group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
                highest_dimension = group_get_highest_dimension(selectionGroup)
                group_add_group_elements(group, selectionGroup, highest_dimension)
                # redefine selection to match group, removes orphaned lower dimensional elements.
                selectionGroup.clear()
                group_add_group_elements(selectionGroup, group, highest_dimension)
        return True

    def setCurrentAnnotationGroupName(self, newName):
        """
        Rename current annotation group, but ensure it is a user group and name is not already in use.
        :return: True on success, otherwise False
        """
        if self._currentAnnotationGroup and self.isUserAnnotationGroup(self._currentAnnotationGroup) and \
                (not findAnnotationGroupByName(self.getAnnotationGroups(), newName)):
            return self._currentAnnotationGroup.setName(newName)
        return False

    def setCurrentAnnotationGroupOntId(self, newOntId):
        """
        :return: True on success, otherwise False
        """
        if self._currentAnnotationGroup and self.isUserAnnotationGroup(self._currentAnnotationGroup):
            return self._currentAnnotationGroup.setId(newOntId)
        return False

    def isUserAnnotationGroup(self, annotationGroup):
        """
        :return: True if annotationGroup is user-created and editable.
        """
        return self._scaffoldPackages[-1].isUserAnnotationGroup(annotationGroup)

    def getCurrentAnnotationGroup(self):
        """
        Get the current annotation group stored for possible editing.
        """
        return self._currentAnnotationGroup

    def setCurrentAnnotationGroup(self, annotationGroup: AnnotationGroup):
        """
        Set annotationGroup as current and replace the selection with its objects.
        :param annotationGroup: Group to select, or None to clear selection.
        """
        # print('setCurrentAnnotationGroup', annotationGroup.getName() if annotationGroup else None)
        self._currentAnnotationGroup = annotationGroup
        fieldmodule = self._region.getFieldmodule()
        with ChangeManager(fieldmodule):
            scene = self._region.getScene()
            selectionGroup = get_scene_selection_group(scene)
            if annotationGroup:
                if selectionGroup:
                    selectionGroup.clear()
                else:
                    selectionGroup = create_scene_selection_group(scene)
                group = annotationGroup.getGroup()
                group_add_group_elements(selectionGroup, group, group_get_highest_dimension(group))
            else:
                if selectionGroup:
                    selectionGroup.clear()
                    scene.setSelectionField(Field())

    def setCurrentAnnotationGroupByName(self, annotationGroupName):
        annotationGroup = findAnnotationGroupByName(self.getAnnotationGroups(), annotationGroupName)
        self.setCurrentAnnotationGroup(annotationGroup)

    def _setScaffoldType(self, scaffoldType):
        if len(self._scaffoldPackages) == 1:
            # root scaffoldPackage
            self._settings['scaffoldPackage'] = self._scaffoldPackages[0] = ScaffoldPackage(scaffoldType)
        else:
            # nested ScaffoldPackage
            self._scaffoldPackages[-1] = self.getParentScaffoldType().getOptionScaffoldPackage(self._scaffoldPackageOptionNames[-1], scaffoldType)
        self._customScaffoldPackage = None
        self._unsavedNodeEdits = False
        self._parameterSetName = self.getEditScaffoldParameterSetNames()[0]
        self._generateMesh()

    def _getScaffoldTypeByName(self, name):
        for scaffoldType in self._allScaffoldTypes:
            if scaffoldType.getName() == name:
                return scaffoldType
        return None

    def setScaffoldTypeByName(self, name):
        scaffoldType = self._getScaffoldTypeByName(name)
        if scaffoldType is not None:
            parentScaffoldType = self.getParentScaffoldType()
            assert (not parentScaffoldType) or (scaffoldType in parentScaffoldType.getOptionValidScaffoldTypes(self._scaffoldPackageOptionNames[-1])), \
                'Invalid scaffold type for parent scaffold'
            if scaffoldType != self.getEditScaffoldType():
                self._setScaffoldType(scaffoldType)

    def getAvailableScaffoldTypeNames(self):
        scaffoldTypeNames = []
        parentScaffoldType = self.getParentScaffoldType()
        validScaffoldTypes = parentScaffoldType.getOptionValidScaffoldTypes(self._scaffoldPackageOptionNames[-1]) if parentScaffoldType else None
        for scaffoldType in self._allScaffoldTypes:
            if (not parentScaffoldType) or (scaffoldType in validScaffoldTypes):
                scaffoldTypeNames.append(scaffoldType.getName())
        return scaffoldTypeNames

    def getEditScaffoldTypeName(self):
        return self.getEditScaffoldType().getName()

    def editingRootScaffoldPackage(self):
        """
        :return: True if editing root ScaffoldPackage, else False.
        """
        return len(self._scaffoldPackages) == 1

    def getEditScaffoldType(self):
        """
        Get scaffold type currently being edited, including nested scaffolds.
        """
        return self._scaffoldPackages[-1].getScaffoldType()

    def getEditScaffoldSettings(self):
        """
        Get settings for scaffold type currently being edited, including nested scaffolds.
        """
        return self._scaffoldPackages[-1].getScaffoldSettings()

    def getEditScaffoldOptionDisplayName(self):
        """
        Get option display name for sub scaffold package being edited.
        """
        return '/'.join(self._scaffoldPackageOptionNames[1:])

    def getEditScaffoldOrderedOptionNames(self):
        return self._scaffoldPackages[-1].getScaffoldType().getOrderedOptionNames()

    def getEditScaffoldParameterSetNames(self):
        if self.editingRootScaffoldPackage():
            return self._scaffoldPackages[0].getScaffoldType().getParameterSetNames()
        # may need to change if scaffolds nested two deep
        return self.getParentScaffoldType().getOptionScaffoldTypeParameterSetNames( \
            self._scaffoldPackageOptionNames[-1], self._scaffoldPackages[-1].getScaffoldType())

    def getDefaultScaffoldPackageForParameterSetName(self, parameterSetName):
        """
        :return: Default ScaffoldPackage set up with named parameter set.
        """
        if self.editingRootScaffoldPackage():
            scaffoldType = self._scaffoldPackages[0].getScaffoldType()
            return ScaffoldPackage(scaffoldType, {'scaffoldSettings': scaffoldType.getDefaultOptions(parameterSetName)})
        # may need to change if scaffolds nested two deep
        return self.getParentScaffoldType().getOptionScaffoldPackage( \
            self._scaffoldPackageOptionNames[-1], self._scaffoldPackages[-1].getScaffoldType(), parameterSetName)

    def getEditScaffoldOption(self, key):
        return self.getEditScaffoldSettings()[key]

    def getEditScaffoldOptionStr(self, key):
        value = self.getEditScaffoldSettings()[key]
        if type(value) is list:
            if type(value[0]) is int:
                return ', '.join(str(v) for v in value)
            elif type(value[0]) is float:
                return ', '.join(STRING_FLOAT_FORMAT.format(v) for v in value)
        return str(value)

    def getParentScaffoldType(self):
        """
        :return: Parent scaffold type or None if root scaffold.
        """
        if len(self._scaffoldPackages) > 1:
            return self._scaffoldPackages[-2].getScaffoldType()
        return None

    def getParentScaffoldOption(self, key):
        assert len(self._scaffoldPackages) > 1, 'Attempt to get parent option on root scaffold'
        parentScaffoldSettings = self._scaffoldPackages[-2].getScaffoldSettings()
        return parentScaffoldSettings[key]

    def _checkCustomParameterSet(self):
        """
        Work out whether ScaffoldPackage has a predefined parameter set or 'Custom'.
        """
        self._customScaffoldPackage = None
        self._unsavedNodeEdits = False
        self._parameterSetName = None
        scaffoldPackage = self._scaffoldPackages[-1]
        for parameterSetName in reversed(self.getEditScaffoldParameterSetNames()):
            tmpScaffoldPackage = self.getDefaultScaffoldPackageForParameterSetName(parameterSetName)
            if tmpScaffoldPackage == scaffoldPackage:
                self._parameterSetName = parameterSetName
                break
        if not self._parameterSetName:
            self._useCustomScaffoldPackage()

    def _clearMeshEdits(self):
        self._scaffoldPackages[-1].setMeshEdits(None)
        self._unsavedNodeEdits = False

    def editScaffoldPackageOption(self, optionName):
        """
        Switch to editing a nested scaffold.
        """
        settings = self.getEditScaffoldSettings()
        scaffoldPackage = settings.get(optionName)
        assert isinstance(scaffoldPackage, ScaffoldPackage), 'Option is not a ScaffoldPackage'
        self._clearMeshEdits()
        self._scaffoldPackages.append(scaffoldPackage)
        self._scaffoldPackageOptionNames.append(optionName)
        self._checkCustomParameterSet()
        self._generateMesh()

    def endEditScaffoldPackageOption(self):
        """
        End editing of the last ScaffoldPackage, moving up to parent or top scaffold type.
        """
        assert len(self._scaffoldPackages) > 1, 'Attempt to end editing root ScaffoldPackage'
        self._updateScaffoldEdits()
        # store the edited scaffold in the settings option
        optionName = self._scaffoldPackageOptionNames.pop()
        scaffoldPackage = self._scaffoldPackages.pop()
        settings = self.getEditScaffoldSettings()
        settings[optionName] = copy.deepcopy(scaffoldPackage)
        self._checkCustomParameterSet()
        self._generateMesh()

    def getInteractiveFunctions(self):
        """
        Return list of interactive functions for current scaffold type.
        :return: list(tuples), (name : str, callable(region, options)).
        """
        return self._scaffoldPackages[-1].getScaffoldType().getInteractiveFunctions()

    def getInteractiveFunctionOptions(self, functionName):
        """
        :param functionName: Name of the interactive function.
        :return: Options dict for function with supplied name.
        """
        interactiveFunctions = self.getInteractiveFunctions()
        for interactiveFunction in interactiveFunctions:
            if interactiveFunction[0] == functionName:
                return interactiveFunction[1]
        return {}

    def performInteractiveFunction(self, functionName, functionOptions):
        """
        Perform interactive function of supplied name for current scaffold.
        :param functionName: Name of the interactive function.
        :param option: User-modified options to pass to the function.
        :return: True if scaffold settings changed.
        """
        interactiveFunctions = self.getInteractiveFunctions()
        for interactiveFunction in interactiveFunctions:
            if interactiveFunction[0] == functionName:
                settingsChanged, nodesChanged = interactiveFunction[2](self._region, self._scaffoldPackages[-1].getScaffoldSettings(), functionOptions, 'meshEdits')
                if nodesChanged:
                    self._unsavedNodeEdits = True
                self._updateScaffoldEdits()
                self._checkCustomParameterSet()
                return settingsChanged
        return False

    def getAvailableParameterSetNames(self):
        parameterSetNames = self.getEditScaffoldParameterSetNames()
        if self._customScaffoldPackage:
            parameterSetNames.insert(0, 'Custom')
        return parameterSetNames

    def getParameterSetName(self):
        """
        :return: Name of currently active parameter set.
        """
        return self._parameterSetName

    def setParameterSetName(self, parameterSetName):
        if self._parameterSetName == 'Custom':
            self._saveCustomScaffoldPackage()
        if parameterSetName == 'Custom':
            self._scaffoldPackages[-1] = copy.deepcopy(self._customScaffoldPackage)
        else:
            self._scaffoldPackages[-1] = self.getDefaultScaffoldPackageForParameterSetName(parameterSetName)
        if len(self._scaffoldPackages) == 1:
            self._settings['scaffoldPackage'] = self._scaffoldPackages[0]
        self._parameterSetName = parameterSetName
        self._unsavedNodeEdits = False
        self._generateMesh()

    def setScaffoldOption(self, key, value):
        """
        :param value: New option value as a string.
        :return: True if other dependent options have changed, otherwise False.
        On True return client is expected to refresh all option values in UI.
        """
        scaffoldType = self.getEditScaffoldType()
        settings = self.getEditScaffoldSettings()
        oldValue = settings[key]
        # print('setScaffoldOption: key ', key, ' value ', str(value))
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
            elif type(oldValue) is list:
                # requires at least one value to work:
                if type(oldValue[0]) is float:
                    newValue = parseListFloat(value)
                elif type(oldValue[0]) is int:
                    newValue = parseListInt(value)
                else:
                    assert False, 'Unimplemented type in list for scaffold option'
            else:
                assert False, 'Unimplemented type in scaffold option'
        except:
            print('setScaffoldOption: Invalid value')
            return
        settings[key] = newValue
        dependentChanges = scaffoldType.checkOptions(settings)
        # print('final value = ', settings[key])
        if settings[key] != oldValue:
            self._clearMeshEdits()
            self._useCustomScaffoldPackage()
            self._generateMesh()
        return dependentChanges

    def getDeleteElementsRangesText(self):
        return self._settings['deleteElementRanges']

    def _parseDeleteElementsRangesText(self, elementRangesTextIn):
        """
        :return: True if ranges changed, otherwise False
        """
        elementRanges = identifier_ranges_from_string(elementRangesTextIn)
        changed = self._deleteElementRanges != elementRanges
        self._deleteElementRanges = elementRanges
        self._settings['deleteElementRanges'] = identifier_ranges_to_string(elementRanges)
        return changed

    def setDeleteElementsRangesText(self, elementRangesTextIn):
        if self._parseDeleteElementsRangesText(elementRangesTextIn):
            self._generateMesh()

    def deleteElementsSelection(self):
        """
        Add the elements in the scene selection to the delete element ranges and delete.
        """
        fm = self._region.getFieldmodule()
        scene = self._region.getScene()
        mesh = self._getMesh()
        selectionGroup = scene.getSelectionField().castGroup()
        meshGroup = selectionGroup.getFieldElementGroup(mesh).getMeshGroup()
        if meshGroup.isValid() and (meshGroup.getSize() > 0):
            # merge selection with current delete element ranges
            elementRanges = self._deleteElementRanges + mesh_group_to_identifier_ranges(meshGroup)
            identifier_ranges_fix(elementRanges)
            self._deleteElementRanges = elementRanges
            oldText = self._settings['deleteElementRanges']
            self._settings['deleteElementRanges'] = identifier_ranges_to_string(elementRanges)
            if self._settings['deleteElementRanges'] != oldText:
                self._generateMesh()

    def applyTransformation(self):
        """
        Apply transformation to nodes and clear it, recording all modified nodes.
        """
        scaffoldPackage = self._scaffoldPackages[-1]
        fieldmodule = self._region.getFieldmodule()
        with ChangeManager(fieldmodule):
            if scaffoldPackage.applyTransformation():
                scaffoldPackage.setRotation([0.0, 0.0, 0.0])
                scaffoldPackage.setScale([1.0, 1.0, 1.0])
                scaffoldPackage.setTranslation([0.0, 0.0, 0.0])
                # mark all nodes as edited:
                coordinates = fieldmodule.findFieldByName('coordinates')
                if coordinates.isValid():
                    nodes = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
                    meshEditsNodeset = self.getOrCreateMeshEditsNodesetGroup(nodes)
                    meshEditsNodeset.addNodesConditional(fieldmodule.createFieldIsDefined(coordinates))
                self._updateScaffoldEdits()
                self._checkCustomParameterSet()
                self._setGraphicsTransformation()

    def getRotationText(self):
        return ', '.join(STRING_FLOAT_FORMAT.format(value) for value in self._scaffoldPackages[-1].getRotation())

    def setRotationText(self, rotationTextIn):
        rotation = parseVector3(rotationTextIn, delimiter=",", defaultValue=0.0)
        if self._scaffoldPackages[-1].setRotation(rotation):
            self._setGraphicsTransformation()

    def getScaleText(self):
        return ', '.join(STRING_FLOAT_FORMAT.format(value) for value in self._scaffoldPackages[-1].getScale())

    def setScaleText(self, scaleTextIn):
        scale = parseVector3(scaleTextIn, delimiter=",", defaultValue=1.0)
        if self._scaffoldPackages[-1].setScale(scale):
            self._setGraphicsTransformation()

    def getTranslationText(self):
        return ', '.join(STRING_FLOAT_FORMAT.format(value) for value in self._scaffoldPackages[-1].getTranslation())

    def setTranslationText(self, translationTextIn):
        translation = parseVector3(translationTextIn, delimiter=",", defaultValue=0.0)
        if self._scaffoldPackages[-1].setTranslation(translation):
            self._setGraphicsTransformation()

    def registerCustomParametersCallback(self, customParametersCallback):
        self._customParametersCallback = customParametersCallback

    def registerSceneChangeCallback(self, sceneChangeCallback):
        self._sceneChangeCallback = sceneChangeCallback

    def registerTransformationChangeCallback(self, transformationChangeCallback):
        self._transformationChangeCallback = transformationChangeCallback

    def _getVisibility(self, graphicsName):
        return self._settings[graphicsName]

    def _setVisibility(self, graphicsName, show):
        self._settings[graphicsName] = show
        graphics = self._region.getScene().findGraphicsByName(graphicsName)
        graphics.setVisibilityFlag(show)

    def isDisplayMarkerPoints(self):
        return self._getVisibility('displayMarkerPoints')

    def setDisplayMarkerPoints(self, show):
        self._setVisibility('displayMarkerPoints', show)

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

    def isDisplayModelRadius(self):
        return self._getVisibility('displayModelRadius')

    def setDisplayModelRadius(self, show):
        if show != self._settings['displayModelRadius']:
            self._settings['displayModelRadius'] = show
            self._createGraphics()

    def getDisplayNodeDerivatives(self):
        """
        :return: tri-state: 0=show none, 1=show selected, 2=show all
        """
        return self._settings['displayNodeDerivatives']

    def _setAllGraphicsVisibility(self, graphicsName, show, selectMode=None):
        """
        Ensure visibility of all graphics with graphicsName is set to boolean show.
        :param selectMode: Optional selectMode to set at the same time.
        """
        scene = self._region.getScene()
        graphics = scene.findGraphicsByName(graphicsName)
        while graphics.isValid():
            graphics.setVisibilityFlag(show)
            if selectMode:
                graphics.setSelectMode(selectMode)
            while True:
                graphics = scene.getNextGraphics(graphics)
                if (not graphics.isValid()) or (graphics.getName() == graphicsName):
                    break

    def setDisplayNodeDerivatives(self, triState):
        """
        :param triState: From Qt::CheckState: 0=show none, 1=show selected, 2=show all
        """
        self._settings['displayNodeDerivatives'] = triState
        for nodeDerivativeLabel in self._nodeDerivativeLabels:
            self._setAllGraphicsVisibility('displayNodeDerivatives' + nodeDerivativeLabel,
                                           bool(triState) and self.isDisplayNodeDerivativeLabels(nodeDerivativeLabel),
                                           selectMode=Graphics.SELECT_MODE_DRAW_SELECTED if (triState == 1) else Graphics.SELECT_MODE_ON)

    def isDisplayNodeDerivativeLabels(self, nodeDerivativeLabel):
        """
        :param nodeDerivativeLabel: Label from self._nodeDerivativeLabels ('D1', 'D2' ...)
        """
        return nodeDerivativeLabel in self._settings['displayNodeDerivativeLabels']

    def setDisplayNodeDerivativeLabels(self, nodeDerivativeLabel, show):
        """
        :param nodeDerivativeLabel: Label from self._nodeDerivativeLabels ('D1', 'D2' ...)
        """
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
        self._setAllGraphicsVisibility('displayNodeDerivatives' + nodeDerivativeLabel, show and bool(self.getDisplayNodeDerivatives()))

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
        lines = self._region.getScene().findGraphicsByName('displayLines')
        lineattr = lines.getGraphicslineattributes()
        isTranslucentLines = isTranslucent and (lineattr.getShapeType() == lineattr.SHAPE_TYPE_CIRCLE_EXTRUSION)
        linesMaterial = self._materialmodule.findMaterialByName('trans_blue' if isTranslucentLines else 'default')
        lines.setMaterial(linesMaterial)

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
        for dimension in range(3, 0, -1):
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
        with ChangeManager(fm):
            coordinates = fm.findFieldByName('coordinates')
            nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
            node = nodes.findNodeByIdentifier(node_id)
            fc = fm.createFieldcache()
            fc.setNode(node)
            _, position = coordinates.evaluateReal(fc, 3)
        return self._getSceneTransformationFromAdjustedPosition(position)

    def getSettings(self):
        return self._settings

    def setSettings(self, settings):
        """
        Called on loading settings from file.
        """
        scaffoldPackage = settings.get('scaffoldPackage')
        if not scaffoldPackage:
            # migrate obsolete options to scaffoldPackage:
            scaffoldType = self._getScaffoldTypeByName(settings['meshTypeName'])
            del settings['meshTypeName']
            scaffoldSettings = settings['meshTypeOptions']
            del settings['meshTypeOptions']
            scaffoldPackage = ScaffoldPackage(scaffoldType, {'scaffoldSettings': scaffoldSettings})
            settings['scaffoldPackage'] = scaffoldPackage
        # migrate boolean options which are now tri-state
        for name in ['displayNodeDerivatives']:
            value = settings[name]
            if type(value) == bool:
                settings[name] = 2 if value else 0
        self._settings.update(settings)
        self._parseDeleteElementsRangesText(self._settings['deleteElementRanges'])
        # migrate old scale text, now held in scaffoldPackage
        oldScaleText = self._settings.get('scale')
        if oldScaleText:
            scaffoldPackage.setScale(parseVector3(oldScaleText, delimiter="*", defaultValue=1.0))
            del self._settings['scale']  # remove so can't overwrite scale next time
        self._scaffoldPackages = [scaffoldPackage]
        self._scaffoldPackageOptionNames = [None]
        self._checkCustomParameterSet()
        self._generateMesh()

    def _deleteElementsInRanges(self):
        """
        If this is the root scaffold and there are ranges of element identifiers to delete,
        remove these from the model.
        Also remove marker group nodes embedded in those elements and any nodes used only by
        the deleted elements.
        """
        if (len(self._deleteElementRanges) == 0) or (len(self._scaffoldPackages) > 1):
            return
        fm = self._region.getFieldmodule()
        mesh = self._getMesh()
        meshDimension = mesh.getDimension()
        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        with ChangeManager(fm):
            # put the elements in a group and use subelement handling to get nodes in use by it
            destroyGroup = fm.createFieldGroup()
            destroyGroup.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
            destroyElementGroup = destroyGroup.createFieldElementGroup(mesh)
            destroyMesh = destroyElementGroup.getMeshGroup()
            elementIter = mesh.createElementiterator()
            element = elementIter.next()
            while element.isValid():
                identifier = element.getIdentifier()
                for deleteElementRange in self._deleteElementRanges:
                    if (identifier >= deleteElementRange[0]) and (identifier <= deleteElementRange[1]):
                        destroyMesh.addElement(element)
                element = elementIter.next()
            del elementIter
            # print("Deleting", destroyMesh.getSize(), "element(s)")
            if destroyMesh.getSize() > 0:
                destroyNodeGroup = destroyGroup.getFieldNodeGroup(nodes)
                destroyNodes = destroyNodeGroup.getNodesetGroup()
                markerGroup = fm.findFieldByName("marker").castGroup()
                if markerGroup.isValid():
                    markerNodes = markerGroup.getFieldNodeGroup(nodes).getNodesetGroup()
                    markerLocation = fm.findFieldByName("marker_location")
                    # markerName = fm.findFieldByName("marker_name")
                    if markerNodes.isValid() and markerLocation.isValid():
                        fieldcache = fm.createFieldcache()
                        nodeIter = markerNodes.createNodeiterator()
                        node = nodeIter.next()
                        while node.isValid():
                            fieldcache.setNode(node)
                            element, xi = markerLocation.evaluateMeshLocation(fieldcache, meshDimension)
                            if element.isValid() and destroyMesh.containsElement(element):
                                # print("Destroy marker '" + markerName.evaluateString(fieldcache) + "' node", node.getIdentifier(), "in destroyed element", element.getIdentifier(), "at", xi)
                                destroyNodes.addNode(node)  # so destroyed with others below; can't do here as
                            node = nodeIter.next()
                        del nodeIter
                        del fieldcache
                # must destroy elements first as Zinc won't destroy nodes that are in use
                mesh.destroyElementsConditional(destroyElementGroup)
                nodes.destroyNodesConditional(destroyNodeGroup)
                # clean up group so no external code hears is notified of its existence
                del destroyNodes
                del destroyNodeGroup
            del destroyMesh
            del destroyElementGroup
            del destroyGroup

    def _generateMesh(self):
        currentAnnotationGroupName = self._currentAnnotationGroup.getName() if self._currentAnnotationGroup else None
        scaffoldPackage = self._scaffoldPackages[-1]
        if self._region:
            self._parent_region.removeChild(self._region)
        self._resetModelCoordinatesField()
        self._region = self._parent_region.createChild(self._region_name)
        self._scene = self._region.getScene()
        fm = self._region.getFieldmodule()
        with ChangeManager(fm):
            logger = self._context.getLogger()
            scaffoldPackage.generate(self._region, applyTransformation=False)
            annotationGroups = scaffoldPackage.getAnnotationGroups()
            loggerMessageCount = logger.getNumberOfMessages()
            if loggerMessageCount > 0:
                for i in range(1, loggerMessageCount + 1):
                    print(logger.getMessageTypeAtIndex(i), logger.getMessageTextAtIndex(i))
                logger.removeAllMessages()
            self._deleteElementsInRanges()
            self.setCurrentAnnotationGroupByName(currentAnnotationGroupName)
        # Zinc won't create cmiss_number and xi fields until endChange called
        # Hence must create graphics outside of ChangeManager lifetime:
        self._discoverModelCoordinatesField()
        self._createGraphics()
        if self._sceneChangeCallback:
            self._sceneChangeCallback()

    def _getAxesScale(self):
        """
        Get sizing for axes, taking into account transformation.
        """
        scale = self._scaffoldPackages[-1].getScale()
        fm = self._region.getFieldmodule()
        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        coordinates = fm.findFieldByName('coordinates').castFiniteElement()
        componentsCount = coordinates.getNumberOfComponents()
        minX, maxX = evaluateFieldNodesetRange(coordinates, nodes)
        if componentsCount == 1:
            maxRange = (maxX - minX) * scale[0]
        else:
            maxRange = max((maxX[c] - minX[c]) * scale[c] for c in range(componentsCount))
        axesScale = 1.0
        if maxRange > 0.0:
            while axesScale * 10.0 < maxRange:
                axesScale *= 10.0
            while axesScale > maxRange:
                axesScale *= 0.1
        return axesScale

    def _setGraphicsTransformation(self):
        """
        Establish 4x4 graphics transformation for current scaffold package.
        """
        transformationMatrix = None
        for scaffoldPackage in reversed(self._scaffoldPackages):
            mat = scaffoldPackage.getTransformationMatrix()
            if mat:
                transformationMatrix = matrix_mult(mat, transformationMatrix) if transformationMatrix else mat
        scene = self._region.getScene()
        if transformationMatrix:
            # flatten to list of 16 components for passing to Zinc
            scene.setTransformationMatrix(transformationMatrix[0] + transformationMatrix[1] + transformationMatrix[2] + transformationMatrix[3])
        else:
            scene.clearTransformation()
        # rescale axes for new scale
        axesScale = self._getAxesScale()
        scene = self._region.getScene()
        with ChangeManager(scene):
            axes = scene.findGraphicsByName('displayAxes')
            pointattr = axes.getGraphicspointattributes()
            pointattr.setBaseSize([axesScale])
            pointattr.setLabelText(1, '  {:2g}'.format(axesScale))

    def _createGraphics(self):
        fm = self._region.getFieldmodule()
        with ChangeManager(fm):
            meshDimension = self.getMeshDimension()
            coordinates = self.getModelCoordinatesField()
            componentsCount = coordinates.getNumberOfComponents()
            nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
            fieldcache = fm.createFieldcache()

            # determine field derivatives for all versions in use: fairly expensive
            # fields in same order as self._nodeDerivativeLabels
            nodeDerivatives = [Node.VALUE_LABEL_D_DS1, Node.VALUE_LABEL_D_DS2, Node.VALUE_LABEL_D_DS3,
                               Node.VALUE_LABEL_D2_DS1DS2, Node.VALUE_LABEL_D2_DS1DS3, Node.VALUE_LABEL_D2_DS2DS3, Node.VALUE_LABEL_D3_DS1DS2DS3]
            nodeDerivativeFields = [[fm.createFieldNodeValue(coordinates, nodeDerivative, 1)] for nodeDerivative in nodeDerivatives]
            derivativesCount = len(nodeDerivatives)
            maxVersions = [1 for nodeDerivative in nodeDerivatives]
            lastVersion = 1
            version = 2
            while True:
                nodeIter = nodes.createNodeiterator()
                node = nodeIter.next()
                foundCount = sum((1 if (v < lastVersion) else 0) for v in maxVersions)
                while (node.isValid()) and (foundCount < derivativesCount):
                    fieldcache.setNode(node)
                    for d in range(derivativesCount):
                        if maxVersions[d] == lastVersion:  # only look one higher than last version found
                            result, values = coordinates.getNodeParameters(fieldcache, -1, nodeDerivatives[d], version, componentsCount)
                            if (result == RESULT_OK) or (result == RESULT_WARNING_PART_DONE):
                                maxVersions[d] = version
                                nodeDerivativeFields[d].append(fm.createFieldNodeValue(coordinates, nodeDerivatives[d], version))
                                foundCount += 1
                    node = nodeIter.next()
                if foundCount >= derivativesCount:
                    break
                lastVersion = version
                version += 1
            elementDerivativeFields = []
            for d in range(meshDimension):
                elementDerivativeFields.append(fm.createFieldDerivative(coordinates, d + 1))
            elementDerivativesField = fm.createFieldConcatenate(elementDerivativeFields)
            cmiss_number = fm.findFieldByName('cmiss_number')
            markerGroup = fm.findFieldByName('marker').castGroup()
            if not markerGroup.isValid():
                markerGroup = fm.createFieldConstant([0.0])  # show nothing to avoid warnings
            markerName = findOrCreateFieldStoredString(fm, 'marker_name')
            radius = fm.findFieldByName('radius')
            markerLocation = findOrCreateFieldStoredMeshLocation(fm, self._getMesh(), name='marker_location')
            markerHostCoordinates = fm.createFieldEmbedded(coordinates, markerLocation)

            # fixed width glyph size is based on average element size in all dimensions
            mesh1d = fm.findMeshByDimension(1)
            meanLineLength = 0.0
            lineCount = mesh1d.getSize()
            if lineCount > 0:
                one = fm.createFieldConstant(1.0)
                sumLineLength = fm.createFieldMeshIntegral(one, coordinates, mesh1d)
                result, totalLineLength = sumLineLength.evaluateReal(fieldcache, 1)
                glyphWidth = 0.1 * totalLineLength / lineCount
                del sumLineLength
                del one
            if (lineCount == 0) or (glyphWidth == 0.0):
                # fallback if no lines: use graphics range
                minX, maxX = evaluateFieldNodesetRange(coordinates, nodes)
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
                glyphWidth = 0.01 * maxScale
            del fieldcache

        # make graphics
        scene = self._region.getScene()
        with ChangeManager(scene):
            scene.removeAllGraphics()
            self._setGraphicsTransformation()

            axes = scene.createGraphicsPoints()
            axes.setScenecoordinatesystem(SCENECOORDINATESYSTEM_WORLD)
            pointattr = axes.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_AXES_XYZ)
            axesScale = self._getAxesScale()
            pointattr.setBaseSize([axesScale])
            pointattr.setLabelText(1, '  {:2g}'.format(axesScale))
            axes.setMaterial(self._materialmodule.findMaterialByName('grey50'))
            axes.setName('displayAxes')
            axes.setVisibilityFlag(self.isDisplayAxes())

            lines = scene.createGraphicsLines()
            lines.setCoordinateField(coordinates)
            lines.setExterior(self.isDisplayLinesExterior())
            lineattr = lines.getGraphicslineattributes()
            if self.isDisplayModelRadius() and radius.isValid():
                lineattr.setShapeType(lineattr.SHAPE_TYPE_CIRCLE_EXTRUSION)
                lineattr.setBaseSize([0.0])
                lineattr.setScaleFactors([2.0])
                lineattr.setOrientationScaleField(radius)
            isTranslucentLines = self.isDisplaySurfacesTranslucent() and (lineattr.getShapeType() == lineattr.SHAPE_TYPE_CIRCLE_EXTRUSION)
            linesMaterial = self._materialmodule.findMaterialByName('trans_blue' if isTranslucentLines else 'default')
            lines.setMaterial(linesMaterial)
            lines.setName('displayLines')
            lines.setVisibilityFlag(self.isDisplayLines())

            nodePoints = scene.createGraphicsPoints()
            nodePoints.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
            nodePoints.setCoordinateField(coordinates)
            pointattr = nodePoints.getGraphicspointattributes()
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
            if self.isDisplayModelRadius() and radius.isValid():
                pointattr.setBaseSize([0.0])
                pointattr.setScaleFactors([2.0])
                pointattr.setOrientationScaleField(radius)
            else:
                pointattr.setBaseSize([glyphWidth])
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
            nodeDerivativeMaterialNames = ['gold', 'silver', 'green', 'cyan', 'magenta', 'yellow', 'blue']
            derivativeScales = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
            for i in range(len(self._nodeDerivativeLabels)):
                nodeDerivativeLabel = self._nodeDerivativeLabels[i]
                maxVersions = len(nodeDerivativeFields[i])
                for v in range(maxVersions):
                    nodeDerivatives = scene.createGraphicsPoints()
                    nodeDerivatives.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
                    nodeDerivatives.setCoordinateField(coordinates)
                    pointattr = nodeDerivatives.getGraphicspointattributes()
                    pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_ARROW_SOLID)
                    pointattr.setOrientationScaleField(nodeDerivativeFields[i][v])
                    pointattr.setBaseSize([0.0, glyphWidth, glyphWidth])
                    pointattr.setScaleFactors([derivativeScales[i], 0.0, 0.0])
                    if maxVersions > 1:
                        pointattr.setLabelOffset([1.05, 0.0, 0.0])
                        pointattr.setLabelText(1, str(v + 1))
                    material = self._materialmodule.findMaterialByName(nodeDerivativeMaterialNames[i])
                    nodeDerivatives.setMaterial(material)
                    nodeDerivatives.setSelectedMaterial(material)
                    nodeDerivatives.setName('displayNodeDerivatives' + nodeDerivativeLabel)
                    displayNodeDerivatives = self.getDisplayNodeDerivatives()  # tri-state: 0=show none, 1=show selected, 2=show all
                    nodeDerivatives.setSelectMode(Graphics.SELECT_MODE_DRAW_SELECTED if (displayNodeDerivatives == 1) else Graphics.SELECT_MODE_ON)
                    nodeDerivatives.setVisibilityFlag(bool(displayNodeDerivatives) and self.isDisplayNodeDerivativeLabels(nodeDerivativeLabel))

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
                pointattr.setBaseSize([0.0, 2 * glyphWidth, 2 * glyphWidth])
                pointattr.setScaleFactors([0.25, 0.0, 0.0])
            elif meshDimension == 2:
                pointattr.setBaseSize([0.0, 0.0, 2 * glyphWidth])
                pointattr.setScaleFactors([0.25, 0.25, 0.0])
            else:
                pointattr.setBaseSize([0.0, 0.0, 0.0])
                pointattr.setScaleFactors([0.25, 0.25, 0.25])
            elementAxes.setMaterial(self._materialmodule.findMaterialByName('yellow'))
            elementAxes.setName('displayElementAxes')
            elementAxes.setVisibilityFlag(self.isDisplayElementAxes())

            # marker points
            markerPoints = scene.createGraphicsPoints()
            markerPoints.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
            markerPoints.setSubgroupField(markerGroup)
            markerPoints.setCoordinateField(markerHostCoordinates)
            pointattr = markerPoints.getGraphicspointattributes()
            pointattr.setLabelText(1, '  ')
            pointattr.setLabelField(markerName)
            pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_CROSS)
            pointattr.setBaseSize(2 * glyphWidth)
            markerPoints.setMaterial(self._materialmodule.findMaterialByName('yellow'))
            markerPoints.setName('displayMarkerPoints')
            markerPoints.setVisibilityFlag(self.isDisplayMarkerPoints())
        logger = self._context.getLogger()
        loggerMessageCount = logger.getNumberOfMessages()
        if loggerMessageCount > 0:
            for i in range(1, loggerMessageCount + 1):
                print(logger.getMessageTypeAtIndex(i), logger.getMessageTextAtIndex(i))
            logger.removeAllMessages()

    def updateSettingsBeforeWrite(self):
        self._updateScaffoldEdits()

    def done(self):
        """
        Finish generating mesh by applying transformation.
        """
        assert 1 == len(self._scaffoldPackages)
        self._scaffoldPackages[0].applyTransformation()

    def writeModel(self, file_name):
        self._region.writeFile(file_name)

    def writeAnnotations(self, filenameStem):
        annotationFilename = filenameStem + '_annotations.csv'
        with open(annotationFilename, 'w') as outstream:
            outstream.write('Term ID,Group name\n')
            annotationGroups = self.getAnnotationGroups()
            termNameIds = []
            for annotationGroup in annotationGroups:
                termNameIds.append((annotationGroup.getName(), annotationGroup.getId()))
            termNameIds.sort()
            for termNameId in termNameIds:
                outstream.write(termNameId[1] + ',' + termNameId[0] + '\n')

    def exportToVtk(self, filenameStem):
        base_name = os.path.basename(filenameStem)
        description = 'Scaffold ' + self._scaffoldPackages[0].getScaffoldType().getName() + ': ' + base_name
        exportvtk = ExportVtk(self._region, description, self.getAnnotationGroups())
        exportvtk.writeFile(filenameStem + '.vtk')


def exnodeStringFromGroup(region, groupName, fieldNames):
    """
    Serialise field within group of groupName to a string.
    :param fieldNames: List of fieldNames to output.
    :param groupName: Name of group to output.
    :return: The string.
    """
    sir = region.createStreaminformationRegion()
    srm = sir.createStreamresourceMemory()
    sir.setResourceGroupName(srm, groupName)
    sir.setResourceFieldNames(srm, fieldNames)
    region.write(sir)
    result, exString = srm.getBuffer()
    return exString


def get_scene_selection_group(scene: Scene, subelementHandlingMode=FieldGroup.SUBELEMENT_HANDLING_MODE_FULL):
    """
    Get existing scene selection group of standard name.
    :param subelementHandlingMode: Mode controlling how faces, lines and nodes are
    automatically added or removed with higher dimensional elements.
    :return: Existing selection group, or None.
    """
    selection_group = scene.getSelectionField().castGroup()
    if selection_group.isValid():
        selection_group.setSubelementHandlingMode(subelementHandlingMode)
        return selection_group
    return None


selection_group_name = 'cmiss_selection'


def create_scene_selection_group(scene: Scene, subelementHandlingMode=FieldGroup.SUBELEMENT_HANDLING_MODE_FULL):
    """
    Create empty, unmanaged scene selection group of standard name.
    Should have already called get_selection_group with None returned.
    Can discover orphaned group of that name.
    New group has subelement handling on.
    :param scene: Zinc Scene to create selection for.
    :param subelementHandlingMode: Mode controlling how faces, lines and nodes are
    automatically added or removed with higher dimensional elements.
    :return: Selection group for scene.
    """
    region = scene.getRegion()
    fieldmodule = region.getFieldmodule()
    with ChangeManager(fieldmodule):
        selection_group = fieldmodule.findFieldByName(selection_group_name)
        if selection_group.isValid():
            selection_group = selection_group.castGroup()
            if selection_group.isValid():
                selection_group.clear()
                selection_group.setManaged(False)
        if not selection_group.isValid():
            selection_group = fieldmodule.createFieldGroup()
            selection_group.setName(selection_group_name)
        selection_group.setSubelementHandlingMode(subelementHandlingMode)
    scene.setSelectionField(selection_group)
    return selection_group
