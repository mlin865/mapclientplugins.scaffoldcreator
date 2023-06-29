"""
Dialog/UI for interacting with scaffoldcreatormodel.
"""
import webbrowser

from PySide6 import QtCore, QtWidgets
from functools import partial

from mapclientplugins.scaffoldcreator.view.ui_scaffoldcreatorwidget import Ui_ScaffoldCreatorWidget
from mapclientplugins.scaffoldcreator.view.functionoptionsdialog import FunctionOptionsDialog
from cmlibs.maths.vectorops import dot, magnitude, mult, normalize, sub
from cmlibs.widgets.groupmanagerwidget import GroupManagerWidget
from cmlibs.utils.zinc.field import fieldIsManagedCoordinates
from scaffoldmaker.scaffoldpackage import ScaffoldPackage


def QLineEdit_parseInt(lineedit):
    """
    Return integer from line edit text, or None if invalid.
    """
    try:
        text = lineedit.text()
        return int(text)
    except ValueError:
        pass
    return None


def QLineEdit_parseVector(lineedit):
    """
    Return one or more component real vector as list from comma separated text in QLineEdit widget
    or None if invalid.
    """
    try:
        text = lineedit.text()
        values = [float(value) for value in text.split(",")]
        return values
    except ValueError:
        pass
    return None


def get_zinc_groups(annotation_groups):
    """
    Convert a list of AnnotationGroups into a list of Zinc FieldGroups.
    """
    zinc_groups = []
    for annotation_group in annotation_groups:
        zinc_group = annotation_group.getGroup()
        zinc_groups.append(zinc_group)
    return zinc_groups


class ScaffoldCreatorWidget(QtWidgets.QWidget):

    def __init__(self, model, parent=None):
        super(ScaffoldCreatorWidget, self).__init__(parent)
        self._ui = Ui_ScaffoldCreatorWidget()
        self._ui.setupUi(self)
        self._model = model
        self._scaffold_model = model.getCreatorModel()
        self._annotation_model = model.getMeshAnnotationModel()
        self._segmentation_data_model = model.getSegmentationDataModel()
        self._ui.sceneviewer_widget.setContext(model.getContext())
        self._ui.sceneviewer_widget.setGeneratorModel(model.getCreatorModel())
        self._model.getCreatorModel().registerCustomParametersCallback(self._customParametersChange)
        self._model.registerSceneChangeCallback(self._sceneChanged)
        self._scaffold_model.registerTransformationChangeCallback(self._transformationChanged)
        self._doneCallback = None
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
        self._refreshAnnotationGroups()
        self._makeConnections()

    def _graphicsInitialized(self):
        """
        Callback for when SceneviewerWidget is initialised
        Set custom scene from model
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            self._model.loadSettings()
            self._refreshOptions()
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            # self._ui.sceneviewer_widget.setSelectModeAll()
            sceneviewer.setLookatParametersNonSkew([2.0, -2.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0])
            sceneviewer.setTransparencyMode(sceneviewer.TRANSPARENCY_MODE_SLOW)
            self._autoPerturbLines()
            self._viewAllButtonClicked()

    def _customParametersChange(self):
        """
        Callback when scaffold options or mesh edits are made, so custom parameter set now in use.
        """
        self._refreshParameterSetNames()

    def _sceneChanged(self):
        # new region for choosing coordinate field from
        self._ui.displayModelCoordinates_fieldChooser.setRegion(self._scaffold_model.getRegion())
        self._ui.displayModelCoordinates_fieldChooser.setField(self._scaffold_model.getModelCoordinatesField())
        self._ui.markerMaterialCoordinatesField_fieldChooser.setRegion(self._scaffold_model.getRegion())
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            self._autoPerturbLines()

    def _transformationChanged(self):
        self._ui.rotation_lineEdit.setText(self._scaffold_model.getRotationText())
        self._ui.scale_lineEdit.setText(self._scaffold_model.getScaleText())
        self._ui.translation_lineEdit.setText(self._scaffold_model.getTranslationText())

    def _autoPerturbLines(self):
        """
        Enable scene viewer perturb lines iff solid surfaces are drawn with lines.
        Call whenever lines, surfaces or translucency changes
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            sceneviewer.setPerturbLinesFlag(self._scaffold_model.needPerturbLines())

    def _makeConnections(self):
        self._ui.sceneviewer_widget.graphicsInitialized.connect(self._graphicsInitialized)
        self._ui.pushButtonDocumentation.clicked.connect(self._documentationButtonClicked)
        self._ui.done_pushButton.clicked.connect(self._doneButtonClicked)
        self._ui.stdViews_pushButton.clicked.connect(self._stdViewsButtonClicked)
        self._ui.viewAll_pushButton.clicked.connect(self._viewAllButtonClicked)
        self._ui.subscaffoldBack_pushButton.clicked.connect(self._subscaffoldBackButtonPressed)
        self._ui.meshType_comboBox.currentIndexChanged.connect(self._scaffoldTypeChanged)
        self._ui.parameterSet_comboBox.currentIndexChanged.connect(self._parameterSetChanged)
        self._ui.deleteElementsRanges_lineEdit.editingFinished.connect(self._deleteElementRangesLineEditChanged)
        self._ui.deleteElementsSelection_pushButton.clicked.connect(self._deleteElementsSelectionButtonPressed)
        self._ui.rotation_lineEdit.editingFinished.connect(self._rotationLineEditChanged)
        self._ui.scale_lineEdit.editingFinished.connect(self._scaleLineEditChanged)
        self._ui.translation_lineEdit.editingFinished.connect(self._translationLineEditChanged)
        self._ui.applyTransformation_pushButton.clicked.connect(self._applyTransformationButtonPressed)
        self._ui.displayDataPoints_checkBox.clicked.connect(self._displayDataPointsClicked)
        self._ui.displayDataContours_checkBox.clicked.connect(self._displayDataContoursClicked)
        self._ui.displayDataRadius_checkBox.clicked.connect(self._displayDataRadiusClicked)
        self._ui.displayDataMarkerPoints_checkBox.clicked.connect(self._displayDataMarkerPointsClicked)
        self._ui.displayDataMarkerNames_checkBox.clicked.connect(self._displayDataMarkerNamesClicked)
        self._ui.displayMarkerPoints_checkBox.clicked.connect(self._displayMarkerPointsClicked)
        self._ui.displayModelCoordinates_fieldChooser.setRegion(self._scaffold_model.getRegion())
        self._ui.displayModelCoordinates_fieldChooser.setConditional(fieldIsManagedCoordinates)
        self._ui.displayModelCoordinates_fieldChooser.currentIndexChanged.connect(
            self._displayModelCoordinatesFieldChanged)
        self._ui.displayAxes_checkBox.clicked.connect(self._displayAxesClicked)
        self._ui.displayElementAxes_checkBox.clicked.connect(self._displayElementAxesClicked)
        self._ui.displayElementNumbers_checkBox.clicked.connect(self._displayElementNumbersClicked)
        self._ui.displayLines_checkBox.clicked.connect(self._displayLinesClicked)
        self._ui.displayLinesExterior_checkBox.clicked.connect(self._displayLinesExteriorClicked)
        self._ui.displayModelRadius_checkBox.clicked.connect(self._displayModelRadiusClicked)
        self._ui.displayNodeDerivativeLabelsD1_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD1Clicked)
        self._ui.displayNodeDerivativeLabelsD2_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD2Clicked)
        self._ui.displayNodeDerivativeLabelsD3_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD3Clicked)
        self._ui.displayNodeDerivativeLabelsD12_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD12Clicked)
        self._ui.displayNodeDerivativeLabelsD13_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD13Clicked)
        self._ui.displayNodeDerivativeLabelsD23_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD23Clicked)
        self._ui.displayNodeDerivativeLabelsD123_checkBox.clicked.connect(self._displayNodeDerivativeLabelsD123Clicked)
        self._ui.displayNodeDerivatives_checkBox.clicked.connect(self._displayNodeDerivativesClicked)
        self._ui.displayNodeNumbers_checkBox.clicked.connect(self._displayNodeNumbersClicked)
        self._ui.displayNodePoints_checkBox.clicked.connect(self._displayNodePointsClicked)
        self._ui.displaySurfaces_checkBox.clicked.connect(self._displaySurfacesClicked)
        self._ui.displaySurfacesExterior_checkBox.clicked.connect(self._displaySurfacesExteriorClicked)
        self._ui.displaySurfacesTranslucent_checkBox.clicked.connect(self._displaySurfacesTranslucentClicked)
        self._ui.displaySurfacesWireframe_checkBox.clicked.connect(self._displaySurfacesWireframeClicked)
        self._ui.annotationGroup_comboBox.currentIndexChanged.connect(self._annotationGroupChanged)
        self._ui.annotationGroupNew_pushButton.clicked.connect(self._annotationGroupNewButtonClicked)
        self._ui.annotationGroupNewMarker_pushButton.clicked.connect(self._annotationGroupNewMarkerButtonClicked)
        self._ui.annotationGroupRedefine_pushButton.clicked.connect(self._annotationGroupRedefineButtonClicked)
        self._ui.annotationGroupEdit_pushButton.clicked.connect(self._annotationGroupEditButtonClicked)
        self._ui.annotationGroupDelete_pushButton.clicked.connect(self._annotationGroupDeleteButtonClicked)
        self._ui.annotationGroupOntId_lineEdit.editingFinished.connect(self._annotationGroupOntIdLineEditChanged)
        self._ui.markerMaterialCoordinatesField_fieldChooser.setRegion(self._scaffold_model.getRegion())
        self._ui.markerMaterialCoordinatesField_fieldChooser.setNullObjectName("-")
        self._ui.markerMaterialCoordinatesField_fieldChooser.setConditional(fieldIsManagedCoordinates)
        self._ui.markerMaterialCoordinatesField_fieldChooser.currentIndexChanged.connect(
            self._markerMaterialCoordinatesFieldChanged)
        self._ui.markerMaterialCoordinates_lineEdit.editingFinished.connect(
            self._markerMaterialCoordinatesLineEditChanged)
        self._ui.markerElement_lineEdit.editingFinished.connect(self._markerElementLineEditChanged)
        self._ui.markerXiCoordinates_lineEdit.editingFinished.connect(self._markerXiCoordinatesLineEditChanged)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_S) and (not event.isAutoRepeat()):
            self._ui.sceneviewer_widget._selectionKeyPressed = True
            event.setAccepted(True)
        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_S) and (not event.isAutoRepeat()):
            self._ui.sceneviewer_widget._selectionKeyPressed = False
            event.setAccepted(True)
        else:
            event.ignore()

    @staticmethod
    def _refreshComboBoxNames(comboBox, names, currentName):
        comboBox.blockSignals(True)
        comboBox.clear()
        currentIndex = 0
        index = 0
        for name in names:
            comboBox.addItem(name)
            if name == currentName:
                currentIndex = index
            index += 1
        comboBox.setCurrentIndex(currentIndex)
        comboBox.blockSignals(False)

    def _refreshScaffoldTypeNames(self):
        self._refreshComboBoxNames(
            self._ui.meshType_comboBox,
            self._scaffold_model.getAvailableScaffoldTypeNames(),
            self._scaffold_model.getEditScaffoldTypeName())

    def _refreshParameterSetNames(self):
        self._refreshComboBoxNames(
            self._ui.parameterSet_comboBox,
            self._scaffold_model.getAvailableParameterSetNames(),
            self._scaffold_model.getParameterSetName())

    def _refreshAnnotationGroups(self):
        annotationGroups = self._scaffold_model.getAnnotationGroups()
        currentAnnotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        self._refreshComboBoxNames(
            self._ui.annotationGroup_comboBox,
            ['-'] + [annotationGroup.getName() for annotationGroup in annotationGroups],
            currentAnnotationGroup.getName() if currentAnnotationGroup else '-')

    def getModel(self):
        return self._model

    def _documentationButtonClicked(self):
        webbrowser.open("https://abi-mapping-tools.readthedocs.io/en/latest/mapclientplugins.argonviewerstep/docs/index.html")

    def registerDoneExecution(self, doneCallback):
        self._doneCallback = doneCallback

    def _doneButtonClicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._doneCallback()
        QtWidgets.QApplication.restoreOverrideCursor()

    def _stdViewsButtonClicked(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            result, eyePosition, lookatPosition, upVector = sceneviewer.getLookatParameters()
            upVector = normalize(upVector)
            viewVector = sub(lookatPosition, eyePosition)
            viewDistance = magnitude(viewVector)
            viewVector = normalize(viewVector)
            # viewX = dot(viewVector, [1.0, 0.0, 0.0])
            viewY = dot(viewVector, [0.0, 1.0, 0.0])
            viewZ = dot(viewVector, [0.0, 0.0, 1.0])
            # upX = dot(upVector, [1.0, 0.0, 0.0])
            upY = dot(upVector, [0.0, 1.0, 0.0])
            upZ = dot(upVector, [0.0, 0.0, 1.0])
            if (viewZ < -0.999) and (upY > 0.999):
                # XY -> XZ
                viewVector = [0.0, 1.0, 0.0]
                upVector = [0.0, 0.0, 1.0]
            elif (viewY > 0.999) and (upZ > 0.999):
                # XZ -> YZ
                viewVector = [-1.0, 0.0, 0.0]
                upVector = [0.0, 0.0, 1.0]
            else:
                # XY
                viewVector = [0.0, 0.0, -1.0]
                upVector = [0.0, 1.0, 0.0]
            eyePosition = sub(lookatPosition, mult(viewVector, viewDistance))
            sceneviewer.setLookatParametersNonSkew(eyePosition, lookatPosition, upVector)

    def _viewAllButtonClicked(self):
        if self._ui.sceneviewer_widget.getSceneviewer() is not None:
            self._ui.sceneviewer_widget.viewAll()

    def _annotationGroupChanged(self, index):
        annotationGroupName = self._ui.annotationGroup_comboBox.itemText(index)
        self._scaffold_model.setCurrentAnnotationGroupByName(annotationGroupName)
        self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupNewButtonClicked(self):
        self._scaffold_model.createUserAnnotationGroup()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupNewMarkerButtonClicked(self):
        self._scaffold_model.createUserMarkerAnnotationGroup()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupRedefineButtonClicked(self):
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        if annotationGroup:
            reply = QtWidgets.QMessageBox.question(
                self, 'Confirm action',
                'Redefine annotation group \'' + annotationGroup.getName() + '\' from selection?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                if self._scaffold_model.redefineCurrentAnnotationGroupFromSelection():
                    self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupEditButtonClicked(self):
        annotationGroups = self._scaffold_model.getAnnotationGroups()
        zinc_groups = get_zinc_groups(annotationGroups)
        currentAnnotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        current_zinc_group = currentAnnotationGroup.getGroup()

        group_manager = GroupManagerWidget(current_zinc_group, zinc_groups)
        group_manager.group_updated.connect(self._refresh)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(group_manager)
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowFlags(dlg.windowFlags() | QtCore.Qt.WindowContextHelpButtonHint)
        dlg.setLayout(layout)
        dlg.resize(600, 400)
        dlg.show()

    def _refresh(self):
        self._annotationGroupChanged(self._ui.annotationGroup_comboBox.currentIndex())

    def _annotationGroupDeleteButtonClicked(self):
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        if annotationGroup:
            reply = QtWidgets.QMessageBox.question(
                self, 'Confirm action',
                'Delete annotation group \'' + annotationGroup.getName() + '\'?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                if self._scaffold_model.deleteAnnotationGroup(annotationGroup):
                    self._refreshAnnotationGroups()
                    self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupNameLineEditChanged(self):
        newName = self._ui.annotationGroup_comboBox.currentText()
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        if annotationGroup and (annotationGroup.getName() != newName):
            if self._scaffold_model.setCurrentAnnotationGroupName(newName):
                self._refreshAnnotationGroups()
            else:
                self._refreshCurrentAnnotationGroupSettings()

    def _annotationGroupOntIdLineEditChanged(self):
        newOntId = self._ui.annotationGroupOntId_lineEdit.text()
        if not self._scaffold_model.setCurrentAnnotationGroupOntId(newOntId):
            self._refreshCurrentAnnotationGroupSettings()

    def _markerMaterialCoordinatesFieldChanged(self, index):
        """
        Callback for change in marker material coordinates field.
        """
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        isUser = self._scaffold_model.isUserAnnotationGroup(annotationGroup)
        if isUser:
            markerMaterialCoordinatesField = self._ui.markerMaterialCoordinatesField_fieldChooser.getField()
            annotationGroup.setMarkerMaterialCoordinates(markerMaterialCoordinatesField)
            self._ui.markerMaterialCoordinates_lineEdit.setEnabled(markerMaterialCoordinatesField is not None)
        self._refreshCurrentAnnotationGroupSettings()


    def _markerMaterialCoordinatesLineEditChanged(self):
        """
        Callback for change in marker material coordinates.
        """
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        isUser = self._scaffold_model.isUserAnnotationGroup(annotationGroup)
        if isUser and annotationGroup.isMarker():
            markerMaterialCoordinatesField = self._ui.markerMaterialCoordinatesField_fieldChooser.getField()
            values = QLineEdit_parseVector(self._ui.markerMaterialCoordinates_lineEdit)
            if isinstance(values, list) and markerMaterialCoordinatesField:
                componentsCount = markerMaterialCoordinatesField.getNumberOfComponents()
                if len(values) < componentsCount:
                    values = values + [0.0]*(componentsCount - len(values))
                annotationGroup.setMarkerMaterialCoordinates(markerMaterialCoordinatesField, values)
        self._refreshCurrentAnnotationGroupSettings()

    def _markerElementLineEditChanged(self):
        """
        Callback for change in marker location element.
        """
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        isUser = self._scaffold_model.isUserAnnotationGroup(annotationGroup)
        if isUser and annotationGroup.isMarker():
            xi = annotationGroup.getMarkerLocation()[1]
            identifier = QLineEdit_parseInt(self._ui.markerElement_lineEdit)
            mesh = self._scaffold_model.getMesh()
            if isinstance(identifier, int) and isinstance(xi, list):
                element = mesh.findElementByIdentifier(identifier)
                if element.isValid():
                    annotationGroup.setMarkerLocation(element, xi)
        self._refreshCurrentAnnotationGroupSettings()

    def _markerXiCoordinatesLineEditChanged(self):
        """
        Callback for change in marker location xi coordinates.
        """
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        isUser = self._scaffold_model.isUserAnnotationGroup(annotationGroup)
        if isUser and annotationGroup.isMarker():
            element, oldXi = annotationGroup.getMarkerLocation()
            xi = QLineEdit_parseVector(self._ui.markerXiCoordinates_lineEdit)
            if element.isValid() and isinstance(xi, list):
                dimension = element.getDimension()
                if len(xi) < dimension:
                    xi = xi + [0.0]*(dimension - len(xi))
                annotationGroup.setMarkerLocation(element, xi)
        self._refreshCurrentAnnotationGroupSettings()

    def _refreshCurrentAnnotationGroupSettings(self):
        """
        Display current annotation group settings.
        """
        annotationGroup = self._scaffold_model.getCurrentAnnotationGroup()
        isUser = (annotationGroup is not None) and self._scaffold_model.isUserAnnotationGroup(annotationGroup)
        self._ui.annotationGroup_comboBox.setEditable(isUser)
        if isUser:
            self._ui.annotationGroup_comboBox.lineEdit().editingFinished.connect(
                self._annotationGroupNameLineEditChanged)
            self._ui.annotationGroup_comboBox.setInsertPolicy(QtWidgets.QComboBox.InsertAtCurrent)
        self._ui.annotationGroupOntId_lineEdit.setText(annotationGroup.getId() if annotationGroup else '-')
        self._ui.annotationGroupOntId_lineEdit.setEnabled(isUser)
        self._ui.annotationGroupDimension_spinBox.setValue(annotationGroup.getDimension() if annotationGroup else 0)
        self._ui.annotationGroupDimension_spinBox.setEnabled(False)
        self._ui.annotationGroupRedefine_pushButton.setEnabled(isUser and not annotationGroup.isMarker())
        self._ui.annotationGroupEdit_pushButton.setEnabled(isUser and not annotationGroup.isMarker())
        self._ui.annotationGroupDelete_pushButton.setEnabled(isUser)
        markerMaterialCoordinatesField = None
        markerMaterialCoordinatesText = ""
        markerElementText = ""
        markerXiText = ""
        if (annotationGroup is not None) and annotationGroup.isMarker():
            markerMaterialCoordinatesField, markerMaterialCoordinates = annotationGroup.getMarkerMaterialCoordinates()
            self._ui.markerMaterialCoordinatesField_fieldChooser.setField(markerMaterialCoordinatesField)
            realFormat = "{:.6g}"
            if markerMaterialCoordinates:
                markerMaterialCoordinatesText = ", ".join(realFormat.format(e) for e in markerMaterialCoordinates)
            element, xi = annotationGroup.getMarkerLocation()
            if element.isValid():
                markerElementText = str(element.getIdentifier())
                markerXiText = ", ".join(realFormat.format(e) for e in xi)
            self._ui.markerMaterialCoordinates_lineEdit.setEnabled(markerMaterialCoordinatesField is not None)
        self._ui.markerMaterialCoordinatesField_fieldChooser.setField(markerMaterialCoordinatesField)
        self._ui.markerMaterialCoordinates_lineEdit.setText(markerMaterialCoordinatesText)
        self._ui.markerElement_lineEdit.setText(markerElementText)
        self._ui.markerXiCoordinates_lineEdit.setText(markerXiText)
        self._ui.marker_groupBox.setEnabled(isUser and (annotationGroup is not None) and annotationGroup.isMarker())

    def _scaffoldTypeChanged(self, index):
        scaffoldTypeName = self._ui.meshType_comboBox.itemText(index)
        self._scaffold_model.setScaffoldTypeByName(scaffoldTypeName)
        self._annotation_model.setScaffoldTypeByName(scaffoldTypeName)
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _parameterSetChanged(self, index):
        parameterSetName = self._ui.parameterSet_comboBox.itemText(index)
        self._scaffold_model.setParameterSetName(parameterSetName)
        self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _meshTypeOptionCheckBoxClicked(self, checkBox):
        dependentChanges = self._scaffold_model.setScaffoldOption(checkBox.objectName(), checkBox.isChecked())
        if dependentChanges:
            self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _subscaffoldBackButtonPressed(self):
        self._scaffold_model.endEditScaffoldPackageOption()
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _meshTypeOptionScaffoldPackageButtonPressed(self, pushButton):
        optionName = pushButton.objectName()
        self._scaffold_model.editScaffoldPackageOption(optionName)
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _meshTypeInteractiveFunctionButtonPressed(self, pushButton):
        functionName = pushButton.objectName()
        functionOptions = self._scaffold_model.getInteractiveFunctionOptions(functionName)
        functionOptionsDialog = FunctionOptionsDialog(functionName, functionOptions, self)
        if functionOptionsDialog.exec():
            optionsChanged = self._scaffold_model.performInteractiveFunction(functionName, functionOptions)
            if optionsChanged:
                self._refreshScaffoldOptions()

    def _meshTypeOptionLineEditChanged(self, lineEdit):
        dependentChanges = self._scaffold_model.setScaffoldOption(lineEdit.objectName(), lineEdit.text())
        if dependentChanges:
            self._refreshScaffoldOptions()
        else:
            lineEdit.setText(self._scaffold_model.getEditScaffoldOptionStr(lineEdit.objectName()))
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()

    def _refreshScaffoldOptions(self):
        layout = self._ui.meshTypeOptions_frame.layout()
        # remove all current mesh type widgets
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        optionNames = self._scaffold_model.getEditScaffoldOrderedOptionNames()
        for key in optionNames:
            value = self._scaffold_model.getEditScaffoldOption(key)
            # print('key ', key, ' value ', value)
            if type(value) is bool:
                checkBox = QtWidgets.QCheckBox(self._ui.meshTypeOptions_frame)
                checkBox.setObjectName(key)
                checkBox.setText(key)
                checkBox.setChecked(value)
                callback = partial(self._meshTypeOptionCheckBoxClicked, checkBox)
                checkBox.clicked.connect(callback)
                layout.addWidget(checkBox)
            else:
                label = QtWidgets.QLabel(self._ui.meshTypeOptions_frame)
                label.setObjectName(key)
                label.setText(key)
                layout.addWidget(label)
                if isinstance(value, ScaffoldPackage):
                    pushButton = QtWidgets.QPushButton()
                    pushButton.setObjectName(key)
                    pushButton.setText('Edit >>')
                    callback = partial(self._meshTypeOptionScaffoldPackageButtonPressed, pushButton)
                    pushButton.clicked.connect(callback)
                    layout.addWidget(pushButton)
                else:
                    lineEdit = QtWidgets.QLineEdit(self._ui.meshTypeOptions_frame)
                    lineEdit.setObjectName(key)
                    lineEdit.setText(self._scaffold_model.getEditScaffoldOptionStr(key))
                    callback = partial(self._meshTypeOptionLineEditChanged, lineEdit)
                    lineEdit.editingFinished.connect(callback)
                    layout.addWidget(lineEdit)
        interativeFunctions = self._scaffold_model.getInteractiveFunctions()
        for interactiveFunction in interativeFunctions:
            pushButton = QtWidgets.QPushButton()
            pushButton.setObjectName(interactiveFunction[0])
            pushButton.setText(interactiveFunction[0])
            callback = partial(self._meshTypeInteractiveFunctionButtonPressed, pushButton)
            pushButton.clicked.connect(callback)
            layout.addWidget(pushButton)
        # refresh or show/hide standard scaffold options for transformation and deleting element ranges
        editingRootScaffold = self._scaffold_model.editingRootScaffoldPackage()
        self._ui.done_pushButton.setEnabled(editingRootScaffold)
        self._ui.subscaffold_frame.setVisible(not editingRootScaffold)
        if editingRootScaffold:
            self._ui.deleteElementsRanges_lineEdit.setText(self._scaffold_model.getDeleteElementsRangesText())
        else:
            self._ui.subscaffold_label.setText(self._scaffold_model.getEditScaffoldOptionDisplayName())
        self._ui.deleteElementsRanges_frame.setVisible(editingRootScaffold)
        self._ui.rotation_lineEdit.setText(self._scaffold_model.getRotationText())
        self._ui.scale_lineEdit.setText(self._scaffold_model.getScaleText())
        self._ui.translation_lineEdit.setText(self._scaffold_model.getTranslationText())

    def _refreshOptions(self):
        self._ui.identifier_label.setText('Identifier:  ' + self._model.getIdentifier())
        self._ui.displayDataPoints_checkBox.setChecked(self._segmentation_data_model.isDisplayDataPoints())
        self._ui.displayDataContours_checkBox.setChecked(self._segmentation_data_model.isDisplayDataContours())
        self._ui.displayDataRadius_checkBox.setChecked(self._segmentation_data_model.isDisplayDataRadius())
        self._ui.displayDataMarkerPoints_checkBox.setChecked(self._segmentation_data_model.isDisplayDataMarkerPoints())
        self._ui.displayDataMarkerNames_checkBox.setChecked(self._segmentation_data_model.isDisplayDataMarkerNames())
        self._ui.displayData_frame.setVisible(self._segmentation_data_model.hasData())
        self._ui.displayMarkerPoints_checkBox.setChecked(self._scaffold_model.isDisplayMarkerPoints())
        self._ui.displayAxes_checkBox.setChecked(self._scaffold_model.isDisplayAxes())
        self._ui.displayElementNumbers_checkBox.setChecked(self._scaffold_model.isDisplayElementNumbers())
        self._ui.displayElementAxes_checkBox.setChecked(self._scaffold_model.isDisplayElementAxes())
        self._ui.displayLines_checkBox.setChecked(self._scaffold_model.isDisplayLines())
        self._ui.displayLinesExterior_checkBox.setChecked(self._scaffold_model.isDisplayLinesExterior())
        self._ui.displayModelRadius_checkBox.setChecked(self._scaffold_model.isDisplayModelRadius())
        self._ui.displayNodeDerivativeLabelsD1_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D1'))
        self._ui.displayNodeDerivativeLabelsD2_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D2'))
        self._ui.displayNodeDerivativeLabelsD3_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D3'))
        self._ui.displayNodeDerivativeLabelsD12_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D12'))
        self._ui.displayNodeDerivativeLabelsD13_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D13'))
        self._ui.displayNodeDerivativeLabelsD23_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D23'))
        self._ui.displayNodeDerivativeLabelsD123_checkBox.setChecked(
            self._scaffold_model.isDisplayNodeDerivativeLabels('D123'))
        displayNodeDerivatives = self._scaffold_model.getDisplayNodeDerivatives()
        self._ui.displayNodeDerivatives_checkBox.setCheckState(
            QtCore.Qt.Unchecked if not displayNodeDerivatives else
            QtCore.Qt.PartiallyChecked if (displayNodeDerivatives == 1) else
            QtCore.Qt.Checked)
        self._ui.displayNodeNumbers_checkBox.setChecked(self._scaffold_model.isDisplayNodeNumbers())
        self._ui.displayNodePoints_checkBox.setChecked(self._scaffold_model.isDisplayNodePoints())
        self._ui.displaySurfaces_checkBox.setChecked(self._scaffold_model.isDisplaySurfaces())
        self._ui.displaySurfacesExterior_checkBox.setChecked(self._scaffold_model.isDisplaySurfacesExterior())
        self._ui.displaySurfacesTranslucent_checkBox.setChecked(self._scaffold_model.isDisplaySurfacesTranslucent())
        self._ui.displaySurfacesWireframe_checkBox.setChecked(self._scaffold_model.isDisplaySurfacesWireframe())
        index = self._ui.meshType_comboBox.findText(self._scaffold_model.getEditScaffoldTypeName())
        self._ui.meshType_comboBox.blockSignals(True)
        self._ui.meshType_comboBox.setCurrentIndex(index)
        self._ui.meshType_comboBox.blockSignals(False)
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()
        self._refreshAnnotationGroups()
        self._refreshCurrentAnnotationGroupSettings()
        self._ui.done_pushButton.setEnabled(True)
        self._ui.subscaffold_frame.setVisible(False)

    def _deleteElementRangesLineEditChanged(self):
        self._scaffold_model.setDeleteElementsRangesText(self._ui.deleteElementsRanges_lineEdit.text())
        self._ui.deleteElementsRanges_lineEdit.setText(self._scaffold_model.getDeleteElementsRangesText())

    def _deleteElementsSelectionButtonPressed(self):
        self._scaffold_model.deleteElementsSelection()
        self._ui.deleteElementsRanges_lineEdit.setText(self._scaffold_model.getDeleteElementsRangesText())

    def _rotationLineEditChanged(self):
        self._scaffold_model.setRotationText(self._ui.rotation_lineEdit.text())
        self._ui.rotation_lineEdit.setText(self._scaffold_model.getRotationText())

    def _scaleLineEditChanged(self):
        self._scaffold_model.setScaleText(self._ui.scale_lineEdit.text())
        self._ui.scale_lineEdit.setText(self._scaffold_model.getScaleText())

    def _translationLineEditChanged(self):
        self._scaffold_model.setTranslationText(self._ui.translation_lineEdit.text())
        self._ui.translation_lineEdit.setText(self._scaffold_model.getTranslationText())

    def _applyTransformationButtonPressed(self):
        self._scaffold_model.applyTransformation()
        self._transformationChanged()

    def _displayDataPointsClicked(self):
        self._segmentation_data_model.setDisplayDataPoints(self._ui.displayDataPoints_checkBox.isChecked())

    def _displayDataContoursClicked(self):
        self._segmentation_data_model.setDisplayDataContours(self._ui.displayDataContours_checkBox.isChecked())

    def _displayDataRadiusClicked(self):
        self._segmentation_data_model.setDisplayDataRadius(self._ui.displayDataRadius_checkBox.isChecked())

    def _displayDataMarkerPointsClicked(self):
        self._segmentation_data_model.setDisplayDataMarkerPoints(self._ui.displayDataMarkerPoints_checkBox.isChecked())

    def _displayDataMarkerNamesClicked(self):
        self._segmentation_data_model.setDisplayDataMarkerNames(self._ui.displayDataMarkerNames_checkBox.isChecked())

    def _displayMarkerPointsClicked(self):
        self._scaffold_model.setDisplayMarkerPoints(self._ui.displayMarkerPoints_checkBox.isChecked())

    def _displayModelCoordinatesFieldChanged(self, index):
        """
        Callback for change in model coordinates field chooser widget.
        """
        field = self._ui.displayModelCoordinates_fieldChooser.getField()
        if field:
            self._scaffold_model.setModelCoordinatesField(field)  # will re-create graphics

    def _displayAxesClicked(self):
        self._scaffold_model.setDisplayAxes(self._ui.displayAxes_checkBox.isChecked())

    def _displayElementAxesClicked(self):
        self._scaffold_model.setDisplayElementAxes(self._ui.displayElementAxes_checkBox.isChecked())

    def _displayElementNumbersClicked(self):
        self._scaffold_model.setDisplayElementNumbers(self._ui.displayElementNumbers_checkBox.isChecked())

    def _displayLinesClicked(self):
        self._scaffold_model.setDisplayLines(self._ui.displayLines_checkBox.isChecked())
        self._autoPerturbLines()

    def _displayLinesExteriorClicked(self):
        self._scaffold_model.setDisplayLinesExterior(self._ui.displayLinesExterior_checkBox.isChecked())

    def _displayModelRadiusClicked(self):
        self._scaffold_model.setDisplayModelRadius(self._ui.displayModelRadius_checkBox.isChecked())

    def _displayNodeDerivativesClicked(self):
        checkState = self._ui.displayNodeDerivatives_checkBox.checkState()
        triState = 0 if (checkState == QtCore.Qt.Unchecked) else 1 if (checkState == QtCore.Qt.PartiallyChecked) else 2
        self._scaffold_model.setDisplayNodeDerivatives(triState)

    def _displayNodeDerivativeLabelsD1Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D1', self._ui.displayNodeDerivativeLabelsD1_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD2Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D2', self._ui.displayNodeDerivativeLabelsD2_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD3Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D3', self._ui.displayNodeDerivativeLabelsD3_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD12Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D12', self._ui.displayNodeDerivativeLabelsD12_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD13Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D13', self._ui.displayNodeDerivativeLabelsD13_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD23Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D23', self._ui.displayNodeDerivativeLabelsD23_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD123Clicked(self):
        self._scaffold_model.setDisplayNodeDerivativeLabels(
            'D123', self._ui.displayNodeDerivativeLabelsD123_checkBox.isChecked())

    def _displayNodeNumbersClicked(self):
        self._scaffold_model.setDisplayNodeNumbers(self._ui.displayNodeNumbers_checkBox.isChecked())

    def _displayNodePointsClicked(self):
        self._scaffold_model.setDisplayNodePoints(self._ui.displayNodePoints_checkBox.isChecked())

    def _displaySurfacesClicked(self):
        self._scaffold_model.setDisplaySurfaces(self._ui.displaySurfaces_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesExteriorClicked(self):
        self._scaffold_model.setDisplaySurfacesExterior(self._ui.displaySurfacesExterior_checkBox.isChecked())

    def _displaySurfacesTranslucentClicked(self):
        self._scaffold_model.setDisplaySurfacesTranslucent(self._ui.displaySurfacesTranslucent_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesWireframeClicked(self):
        self._scaffold_model.setDisplaySurfacesWireframe(self._ui.displaySurfacesWireframe_checkBox.isChecked())
