"""
Scaffold Creator Model class. Generates Zinc meshes using scaffoldmaker.
"""

import copy
import os
import math
import sys

from cmlibs.maths.vectorops import axis_angle_to_rotation_matrix, euler_to_rotation_matrix, matrix_mult, \
    rotation_matrix_to_euler
from cmlibs.utils.zinc.field import fieldIsManagedCoordinates, determine_node_field_derivatives
from cmlibs.utils.zinc.finiteelement import evaluateFieldNodesetRange
from cmlibs.utils.zinc.general import ChangeManager, HierarchicalChangeManager
from cmlibs.utils.zinc.group import group_add_group_elements, group_get_highest_dimension, \
    identifier_ranges_fix, identifier_ranges_from_string, identifier_ranges_to_string, mesh_group_to_identifier_ranges
from cmlibs.utils.zinc.region import determine_appropriate_glyph_size
from cmlibs.utils.zinc.scene import scene_create_selection_group, scene_get_selection_group, scene_create_node_derivative_graphics

from cmlibs.zinc.field import Field, FieldGroup
from cmlibs.zinc.glyph import Glyph
from cmlibs.zinc.graphics import Graphics
from cmlibs.zinc.node import Node
from cmlibs.zinc.result import RESULT_OK, RESULT_WARNING_PART_DONE
from cmlibs.zinc.scenecoordinatesystem import SCENECOORDINATESYSTEM_WORLD
from scaffoldmaker.annotation.annotationgroup import findAnnotationGroupByName, getAnnotationMarkerGroup, \
    getAnnotationMarkerLocationField, getAnnotationMarkerNameField
from scaffoldmaker.scaffolds import Scaffolds
from scaffoldmaker.scaffoldpackage import ScaffoldPackage
from scaffoldmaker.utils.exportvtk import ExportVtk

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
        except ValueError:
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
        except ValueError:
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
        except ValueError:
            vector.append(defaultValue)
    if len(vector) > 3:
        vector = vector[:3]
    else:
        for i in range(3 - len(vector)):
            vector.append(vector[-1])
    return vector


class ScaffoldCreatorModel(object):
    """
    Framework for generating meshes of a number of types, with mesh type specific options
    """

    def __init__(self, context, parent_region, material_module):
        super(ScaffoldCreatorModel, self).__init__()
        self._region_name = "generated_mesh"
        self._context = context
        self._parentRegion = parent_region
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
            'displayNodeDerivativeVersion': 0,  # 0 = all or version number
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
            fieldmodule = self._region.getFieldmodule()
            editFieldNames = []
            for editFieldName in ['coordinates', 'inner coordinates']:
                if fieldmodule.findFieldByName(editFieldName).isValid():
                    editFieldNames.append(editFieldName)
            self._scaffoldPackages[-1].setMeshEdits(exnodeStringFromGroup(self._region, 'meshEdits', editFieldNames))
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
            # self._useCustomScaffoldPackage()
            nodesetGroup = group.getOrCreateNodesetGroup(nodeset)
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

    def createUserMarkerAnnotationGroup(self):
        """
        Create a new marker annotation group with automatic name.
        :return: New annotation group.
        """
        self._currentAnnotationGroup = self._scaffoldPackages[-1].createUserAnnotationGroup()
        try:
            self._currentAnnotationGroup.createMarkerNode(self._scaffoldPackages[-1].getNextNodeIdentifier())
        except AssertionError:
            pass
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
        # can only redefine user annotation groups which are not markers
        assert self.isUserAnnotationGroup(self._currentAnnotationGroup)
        assert not self._currentAnnotationGroup.isMarker()
        parentScene = self._parentRegion.getScene()
        scene = self._region.getScene()
        with ChangeManager(parentScene), ChangeManager(scene), HierarchicalChangeManager(self._parentRegion):
            self._currentAnnotationGroup.clear()
            selectionGroup = scene_get_selection_group(parentScene)
            if selectionGroup:
                selectionGroup.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
                subregionGroup = selectionGroup.getSubregionFieldGroup(self._region)
                if subregionGroup.isValid():
                    group = self._currentAnnotationGroup.getGroup()
                    group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
                    highest_dimension = group_get_highest_dimension(subregionGroup)
                    group_add_group_elements(group, subregionGroup, highest_dimension)
                    # redefine selection to match group, removes orphaned lower dimensional elements.
                    selectionGroup.clear()
                    group_add_group_elements(selectionGroup, group, highest_dimension)
        return True

    def setCurrentAnnotationGroupName(self, newName: str):
        """
        Rename current annotation group, but ensure it is a user group and name is not already in use.
        :return: True on success, otherwise False
        """
        if not self._currentAnnotationGroup:
            print("No current annotation group to set name of", file=sys.stderr)
            return False
        if self._currentAnnotationGroup.getName() == newName:
            return True  # don't want to be warned about this
        if not self.isUserAnnotationGroup(self._currentAnnotationGroup):
            print("Can only rename user-defined annotation groups", file=sys.stderr)
            return False
        if findAnnotationGroupByName(self.getAnnotationGroups(), newName):
            print("Name " + newName + " is in use by another annotation group", file=sys.stderr)
            return False
        return self._currentAnnotationGroup.setName(newName)

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

    def setCurrentAnnotationGroup(self, annotationGroup):
        """
        Set annotationGroup as current and replace the selection with its objects.
        :param annotationGroup: AnnotationGroup to select, or None to clear selection.
        """
        # print('setCurrentAnnotationGroup', annotationGroup.getName() if annotationGroup else None)
        self._currentAnnotationGroup = annotationGroup
        parentScene = self._parentRegion.getScene()
        scene = self._region.getScene()
        with ChangeManager(parentScene), ChangeManager(scene), HierarchicalChangeManager(self._parentRegion):
            selectionGroup = scene_get_selection_group(parentScene)
            if annotationGroup:
                if selectionGroup:
                    selectionGroup.clear()
                    selectionGroup.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
                else:
                    selectionGroup = scene_create_selection_group(parentScene)
                if annotationGroup.isMarker():
                    markerNode = annotationGroup.getMarkerNode()
                    nodes = markerNode.getNodeset()
                    selectionNodesetGroup = selectionGroup.getOrCreateNodesetGroup(nodes)
                    selectionNodesetGroup.addNode(markerNode)
                else:
                    group = annotationGroup.getGroup()
                    group_add_group_elements(selectionGroup, group, group_get_highest_dimension(group))
            else:
                if selectionGroup:
                    selectionGroup.clear()
                    parentScene.setSelectionField(Field())

    def setCurrentAnnotationGroupByName(self, annotationGroupName):
        annotationGroup = findAnnotationGroupByName(self.getAnnotationGroups(), annotationGroupName)
        self.setCurrentAnnotationGroup(annotationGroup)

    def _setScaffoldType(self, scaffoldType):
        if len(self._scaffoldPackages) == 1:
            # root scaffoldPackage
            self._settings['scaffoldPackage'] = self._scaffoldPackages[0] = ScaffoldPackage(scaffoldType)
        else:
            # nested ScaffoldPackage
            self._scaffoldPackages[-1] = self.getParentScaffoldType().getOptionScaffoldPackage(
                self._scaffoldPackageOptionNames[-1], scaffoldType)
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
            assert (not parentScaffoldType) or (scaffoldType in parentScaffoldType.getOptionValidScaffoldTypes(
                self._scaffoldPackageOptionNames[-1])), 'Invalid scaffold type for parent scaffold'
            if scaffoldType != self.getEditScaffoldType():
                self._setScaffoldType(scaffoldType)

    def getAvailableScaffoldTypeNames(self):
        scaffoldTypeNames = []
        parentScaffoldType = self.getParentScaffoldType()
        validScaffoldTypes = parentScaffoldType.getOptionValidScaffoldTypes(
            self._scaffoldPackageOptionNames[-1]) if parentScaffoldType else None
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
        return self.getParentScaffoldType().getOptionScaffoldTypeParameterSetNames(
            self._scaffoldPackageOptionNames[-1], self._scaffoldPackages[-1].getScaffoldType())

    def getDefaultScaffoldPackageForParameterSetName(self, parameterSetName):
        """
        :return: Default ScaffoldPackage set up with named parameter set.
        """
        if self.editingRootScaffoldPackage():
            scaffoldType = self._scaffoldPackages[0].getScaffoldType()
            return ScaffoldPackage(scaffoldType, {'scaffoldSettings': scaffoldType.getDefaultOptions(parameterSetName)})
        # may need to change if scaffolds nested two deep
        return self.getParentScaffoldType().getOptionScaffoldPackage(
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
        meshEditsGroup = self.getMeshEditsGroup()
        if meshEditsGroup.isValid():
            meshEditsGroup.setManaged(False)

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
                options = interactiveFunction[1]
                # None-valued options are initialised with same-key value from settings
                settings = self._scaffoldPackages[-1].getScaffoldSettings()
                for key, value in options.items():
                    if value is None:
                        options[key] = settings[key]
                return options
        return {}

    def performInteractiveFunction(self, functionName, functionOptions):
        """
        Perform interactive function of supplied name for current scaffold.
        :param functionName: Name of the interactive function.
        :param functionOptions: User-modified options to pass to the function.
        :return: True if scaffold settings changed.
        """
        interactiveFunctions = self.getInteractiveFunctions()
        for interactiveFunction in interactiveFunctions:
            if interactiveFunction[0] == functionName:
                scaffoldPackage = self._scaffoldPackages[-1]
                settingsChanged, nodesChanged = interactiveFunction[2](
                    self._region, scaffoldPackage.getScaffoldSettings(), scaffoldPackage.getConstructionObject(),
                    functionOptions, 'meshEdits')
                if nodesChanged:
                    self._unsavedNodeEdits = True
                else:
                    # handle empty mesh edits due to model being reset
                    meshEditsGroup = self.getMeshEditsGroup()
                    if (not meshEditsGroup.isValid()) or meshEditsGroup.isEmpty():
                        self._clearMeshEdits()
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
        :param key: The exact option/parameter name.
        :param value: New option value as a string.
        :return: True if other dependent options have changed, otherwise False.
        On True return client is expected to refresh all option values in UI.
        """
        scaffoldType = self.getEditScaffoldType()
        settings = self.getEditScaffoldSettings()
        oldValue = settings[key]
        # print('setScaffoldOption: key ', key, ' value ', str(value))
        # newValue = None
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
        except ValueError:
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
            self._updateScaffoldEdits()
            self._generateMesh()

    def deleteElementsSelection(self):
        """
        Add the elements in the scene selection to the delete element ranges and delete.
        """
        parentScene = self._parentRegion.getScene()
        selectionGroup = scene_get_selection_group(parentScene)
        mesh = self.getMesh()
        meshGroup = selectionGroup.getMeshGroup(mesh)
        if meshGroup.isValid() and (meshGroup.getSize() > 0):
            # merge selection with current delete element ranges
            elementRanges = self._deleteElementRanges + mesh_group_to_identifier_ranges(meshGroup)
            identifier_ranges_fix(elementRanges)
            self._deleteElementRanges = elementRanges
            oldText = self._settings['deleteElementRanges']
            self._settings['deleteElementRanges'] = identifier_ranges_to_string(elementRanges)
            if self._settings['deleteElementRanges'] != oldText:
                self._generateMesh()

    def applyTransformation(self, editCoordinatesField):
        """
        Apply transformation to nodes and clear it, recording all modified nodes.
        :param editCoordinatesField: Coordinate field to which transformation is applied to.
        """
        scaffoldPackage = self._scaffoldPackages[-1]
        fieldmodule = self._region.getFieldmodule()
        with ChangeManager(fieldmodule):
            if scaffoldPackage.applyTransformation(editCoordinatesField):
                scaffoldPackage.setRotation([0.0, 0.0, 0.0])
                scaffoldPackage.setScale([1.0, 1.0, 1.0])
                scaffoldPackage.setTranslation([0.0, 0.0, 0.0])
                # mark all nodes as edited:
                nodes = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
                meshEditsNodeset = self.getOrCreateMeshEditsNodesetGroup(nodes)
                meshEditsNodeset.addNodesConditional(fieldmodule.createFieldIsDefined(editCoordinatesField))
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

    def _setMultipleGraphicsVisibility(self, graphicsPartName, show, selectMode=None):
        """
        Ensure visibility of all graphics starting with graphicsStemName is set to boolean show.
        :param selectMode: Optional selectMode to set at the same time.
        """
        scene = self._region.getScene()
        graphics = scene.getFirstGraphics()
        while graphics.isValid():
            graphicsName = graphics.getName()
            if graphicsPartName in graphicsName:
                graphics.setVisibilityFlag(show)
                if selectMode:
                    graphics.setSelectMode(selectMode)
            graphics = scene.getNextGraphics(graphics)

    def setDisplayNodeDerivatives(self, triState):
        """
        :param triState: From Qt::CheckState: 0=show none, 1=show selected, 2=show all
        """
        self._settings['displayNodeDerivatives'] = triState
        displayVersion = self.getDisplayNodeDerivativeVersion()
        with ChangeManager(self._scene):
            for nodeDerivativeLabel in self._nodeDerivativeLabels:
                graphicsPartName = 'displayNodeDerivatives_' + nodeDerivativeLabel
                if displayVersion > 0:
                    # hide all then display chosen version below
                    self._setMultipleGraphicsVisibility(graphicsPartName, show=False)
                    graphicsPartName += '_v' + str(displayVersion)
                self._setMultipleGraphicsVisibility(
                    graphicsPartName,
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
        :param show: True to show, False to not show.
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
        displayVersion = self.getDisplayNodeDerivativeVersion()
        graphicsPartName = 'displayNodeDerivatives_' + nodeDerivativeLabel
        if displayVersion > 0:
            graphicsPartName += '_v' + str(displayVersion)
        self._setMultipleGraphicsVisibility(graphicsPartName, show and bool(self.getDisplayNodeDerivatives()))

    def getDisplayNodeDerivativeVersion(self):
        """
        :return: 0 to show all versions, otherwise version number > 0.
        """
        return self._settings['displayNodeDerivativeVersion']

    def setDisplayNodeDerivativeVersion(self, version):
        """
        :param version: Integer >= 0; 0 to show all versions, otherwise version number.
        """
        assert isinstance(version, int) and (version >= 0)
        self._settings['displayNodeDerivativeVersion'] = version
        self.setDisplayNodeDerivatives(self.getDisplayNodeDerivatives())

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

    def getMesh(self):
        fm = self._region.getFieldmodule()
        mesh = None
        for dimension in range(3, 0, -1):
            mesh = fm.findMeshByDimension(dimension)
            if mesh.getSize() > 0:
                break
        if mesh.getSize() == 0:
            mesh = fm.findMeshByDimension(3)
        return mesh

    def getMeshDimension(self):
        return self.getMesh().getDimension()

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

    def _generateMesh(self):
        currentAnnotationGroupName = self._currentAnnotationGroup.getName() if self._currentAnnotationGroup else None
        scaffoldPackage = self._scaffoldPackages[-1]
        if self._region:
            self._parentRegion.removeChild(self._region)
        self._resetModelCoordinatesField()
        self._region = self._parentRegion.createChild(self._region_name)
        self._scene = self._region.getScene()
        fm = self._region.getFieldmodule()
        with ChangeManager(fm):
            logger = self._context.getLogger()
            scaffoldPackage.generate(self._region, applyTransformation=False)
            deleteElementRanges = self._deleteElementRanges
            scaffoldPackage.deleteElementsInRanges(self._region, deleteElementRanges)
            loggerMessageCount = logger.getNumberOfMessages()
            if loggerMessageCount > 0:
                for i in range(1, loggerMessageCount + 1):
                    print(logger.getMessageTypeAtIndex(i), logger.getMessageTextAtIndex(i))
                logger.removeAllMessages()

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
        axesScale = 1.0
        if nodes.getSize() > 0:
            minX, maxX = evaluateFieldNodesetRange(coordinates, nodes)
            if componentsCount == 1:
                maxRange = (maxX - minX) * scale[0]
            else:
                maxRange = max((maxX[c] - minX[c]) * scale[c] for c in range(componentsCount))
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
            mesh = self.getMesh()
            meshDimension = mesh.getDimension()
            coordinates = self.getModelCoordinatesField()

            elementDerivativeFields = []
            for d in range(meshDimension):
                elementDerivativeFields.append(fm.createFieldDerivative(coordinates, d + 1))
            elementDerivativesField = fm.createFieldConcatenate(elementDerivativeFields)
            cmiss_number = fm.findFieldByName('cmiss_number')
            radius = fm.findFieldByName('radius')
            markerGroup = getAnnotationMarkerGroup(fm)
            markerLocation = getAnnotationMarkerLocationField(fm, mesh)
            markerName = getAnnotationMarkerNameField(fm)
            markerHostCoordinates = fm.createFieldEmbedded(coordinates, markerLocation)

            glyphWidth = determine_appropriate_glyph_size(self._region, coordinates)

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

            nodeDerivativeFields = determine_node_field_derivatives(self._region, coordinates, True)
            scene_create_node_derivative_graphics(scene, coordinates, nodeDerivativeFields, glyphWidth, self._nodeDerivativeLabels,
                                                  self.getDisplayNodeDerivatives(), self._settings['displayNodeDerivativeLabels'], self.getDisplayNodeDerivativeVersion())

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
                # pointattr.setBaseSize([0.0, 0.0, 0.0])
                # pointattr.setScaleFactors([0.25, 0.25, 0.25])
                # workaround for zinc not transforming axes correctly: use REPEAT_MODE_AXES_3D
                pointattr.setGlyphShapeType(Glyph.SHAPE_TYPE_LINE)
                pointattr.setGlyphRepeatMode(Glyph.REPEAT_MODE_AXES_3D)
                pointattr.setBaseSize([0.0, 2 * glyphWidth, 2 * glyphWidth])
                pointattr.setScaleFactors([0.25, 0.0, 0.0])
                pointattr.setLabelText(1, "1")
                pointattr.setLabelText(2, "2")
                pointattr.setLabelText(3, "3")
                pointattr.setLabelOffset([1.1, 0.0, 0.0])
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
        fieldmodule = self._region.getFieldmodule()
        for editFieldName in ['coordinates', 'inner coordinates']:
            editCoordinates = fieldmodule.findFieldByName(editFieldName)
            if editCoordinates.isValid():
                self._scaffoldPackages[0].applyTransformation(editCoordinates)

    def writeModel(self, file_name):
        self._region.writeFile(file_name)

    @staticmethod
    def getAnnotationsFilename(filename_stem):
        return filename_stem + '_annotations.csv'

    def writeAnnotations(self, filename_stem):
        annotationFilename = self.getAnnotationsFilename(filename_stem)
        with open(annotationFilename, 'w') as outstream:
            outstream.write('Term ID,Group name\n')
            annotationGroups = self.getAnnotationGroups()
            termNameIds = []
            for annotationGroup in annotationGroups:
                termNameIds.append((annotationGroup.getName(), annotationGroup.getId()))
            termNameIds.sort()
            for termNameId in termNameIds:
                outstream.write(termNameId[1] + ',' + termNameId[0] + '\n')

    def exportToVtk(self, filename_stem):
        base_name = os.path.basename(filename_stem)
        description = 'Scaffold ' + self._scaffoldPackages[0].getScaffoldType().getName() + ': ' + base_name
        export_vtk = ExportVtk(self._region, description, self.getAnnotationGroups())
        export_vtk.writeFile(filename_stem + '.vtk')


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
