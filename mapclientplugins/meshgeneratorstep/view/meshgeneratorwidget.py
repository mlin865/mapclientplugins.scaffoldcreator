"""
Dialog/UI for interacting with meshgeneratormodel.
"""

from PySide import QtGui, QtCore
from functools import partial

from mapclientplugins.meshgeneratorstep.view.ui_meshgeneratorwidget import Ui_MeshGeneratorWidget
from scaffoldmaker.scaffoldpackage import ScaffoldPackage


class MeshGeneratorWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(MeshGeneratorWidget, self).__init__(parent)
        self._ui = Ui_MeshGeneratorWidget()
        self._ui.setupUi(self)
        self._model = model
        self._generator_model = model.getGeneratorModel()
        self._annotation_model = model.getMeshAnnotationModel()
        self._segmentation_data_model = model.getSegmentationDataModel()
        self._ui.sceneviewer_widget.setContext(model.getContext())
        self._ui.sceneviewer_widget.setGeneratorModel(model.getGeneratorModel())
        self._model.getGeneratorModel().registerCustomParametersCallback(self._customParametersChange)
        self._model.registerSceneChangeCallback(self._sceneChanged)
        self._generator_model.registerTransformationChangeCallback(self._transformationChanged)
        self._doneCallback = None
        # self._populateAnnotationTree()
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
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
            self._viewAll()

    def _customParametersChange(self):
        """
        Callback when scaffold options or mesh edits are made, so custom parameter set now in use.
        """
        self._refreshParameterSetNames()

    def _sceneChanged(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            self._autoPerturbLines()

    def _transformationChanged(self):
        self._ui.rotation_lineEdit.setText(self._generator_model.getRotationText())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())
        self._ui.translation_lineEdit.setText(self._generator_model.getTranslationText())

    def _autoPerturbLines(self):
        """
        Enable scene viewer perturb lines iff solid surfaces are drawn with lines.
        Call whenever lines, surfaces or translucency changes
        """
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            sceneviewer.setPerturbLinesFlag(self._generator_model.needPerturbLines())

    def _makeConnections(self):
        self._ui.sceneviewer_widget.graphicsInitialized.connect(self._graphicsInitialized)
        self._ui.done_button.clicked.connect(self._doneButtonClicked)
        self._ui.viewAll_button.clicked.connect(self._viewAll)
        self._ui.subscaffoldBack_pushButton.clicked.connect(self._subscaffoldBackButtonPressed)
        self._ui.meshType_comboBox.currentIndexChanged.connect(self._scaffoldTypeChanged)
        self._ui.parameterSet_comboBox.currentIndexChanged.connect(self._parameterSetChanged)
        self._ui.deleteElementsRanges_lineEdit.returnPressed.connect(self._deleteElementRangesLineEditChanged)
        self._ui.deleteElementsRanges_lineEdit.editingFinished.connect(self._deleteElementRangesLineEditChanged)
        self._ui.deleteElementsSelection_pushButton.clicked.connect(self._deleteElementsSelectionButtonPressed)
        self._ui.rotation_lineEdit.returnPressed.connect(self._rotationLineEditChanged)
        self._ui.rotation_lineEdit.editingFinished.connect(self._rotationLineEditChanged)
        self._ui.scale_lineEdit.returnPressed.connect(self._scaleLineEditChanged)
        self._ui.scale_lineEdit.editingFinished.connect(self._scaleLineEditChanged)
        self._ui.translation_lineEdit.returnPressed.connect(self._translationLineEditChanged)
        self._ui.translation_lineEdit.editingFinished.connect(self._translationLineEditChanged)
        self._ui.displayDataContours_checkBox.clicked.connect(self._displayDataContoursClicked)
        self._ui.displayDataMarkerPoints_checkBox.clicked.connect(self._displayDataMarkerPointsClicked)
        self._ui.displayDataMarkerNames_checkBox.clicked.connect(self._displayDataMarkerNamesClicked)
        self._ui.displayMarkerPoints_checkBox.clicked.connect(self._displayMarkerPointsClicked)
        self._ui.displayAxes_checkBox.clicked.connect(self._displayAxesClicked)
        self._ui.displayElementAxes_checkBox.clicked.connect(self._displayElementAxesClicked)
        self._ui.displayElementNumbers_checkBox.clicked.connect(self._displayElementNumbersClicked)
        self._ui.displayLines_checkBox.clicked.connect(self._displayLinesClicked)
        self._ui.displayLinesExterior_checkBox.clicked.connect(self._displayLinesExteriorClicked)
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

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_S) and (event.isAutoRepeat() == False):
            self._ui.sceneviewer_widget._selectionKeyPressed = True
            event.setAccepted(True)
        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_S) and (event.isAutoRepeat() == False):
            self._ui.sceneviewer_widget._selectionKeyPressed = False
            event.setAccepted(True)
        else:
            event.ignore()

    def _refreshComboBoxNames(self, comboBox, names, currentName):
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
        self._refreshComboBoxNames(self._ui.meshType_comboBox,
            self._generator_model.getAvailableScaffoldTypeNames(),
            self._generator_model.getEditScaffoldTypeName())

    def _refreshParameterSetNames(self):
        self._refreshComboBoxNames(self._ui.parameterSet_comboBox,
            self._generator_model.getAvailableParameterSetNames(),
            self._generator_model.getParameterSetName())

    def _createFMAItem(self, parent, text, fma_id):
        item = QtGui.QTreeWidgetItem(parent)
        item.setText(0, text)
        item.setData(0, QtCore.Qt.UserRole + 1, fma_id)
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsTristate)

        return item

    def _populateAnnotationTree(self):
        tree = self._ui.treeWidgetAnnotation
        tree.clear()
        rsh_item = self._createFMAItem(tree, 'right side of heart', 'FMA_7165')
        self._createFMAItem(rsh_item, 'ventricle', 'FMA_7098')
        self._createFMAItem(rsh_item, 'atrium', 'FMA_7096')
        self._createFMAItem(rsh_item, 'auricle', 'FMA_7218')
        lsh_item = self._createFMAItem(tree, 'left side of heart', 'FMA_7166')
        self._createFMAItem(lsh_item, 'ventricle', 'FMA_7101')
        self._createFMAItem(lsh_item, 'atrium', 'FMA_7097')
        self._createFMAItem(lsh_item, 'auricle', 'FMA_7219')
        apex_item = self._createFMAItem(tree, 'apex of heart', 'FMA_7164')
        vortex_item = self._createFMAItem(tree, 'vortex of heart', 'FMA_84628')

        self._ui.treeWidgetAnnotation.addTopLevelItem(rsh_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(lsh_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(apex_item)
        self._ui.treeWidgetAnnotation.addTopLevelItem(vortex_item)

    def getModel(self):
        return self._model

    def registerDoneExecution(self, doneCallback):
        self._doneCallback = doneCallback

    def _updateUi(self):
        pass

    def _doneButtonClicked(self):
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._doneCallback()

    def _scaffoldTypeChanged(self, index):
        scaffoldTypeName = self._ui.meshType_comboBox.itemText(index)
        self._generator_model.setScaffoldTypeByName(scaffoldTypeName)
        self._annotation_model.setScaffoldTypeByName(scaffoldTypeName)
        self._refreshScaffoldOptions()
        self._refreshParameterSetNames()

    def _parameterSetChanged(self, index):
        parameterSetName = self._ui.parameterSet_comboBox.itemText(index)
        self._generator_model.setParameterSetName(parameterSetName)
        self._refreshScaffoldOptions()

    def _meshTypeOptionCheckBoxClicked(self, checkBox):
        dependentChanges = self._generator_model.setScaffoldOption(checkBox.objectName(), checkBox.isChecked())
        if dependentChanges:
            self._refreshScaffoldOptions()

    def _subscaffoldBackButtonPressed(self):
        self._generator_model.endEditScaffoldPackageOption()
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()

    def _meshTypeOptionScaffoldPackageButtonPressed(self, pushButton):
        optionName = pushButton.objectName()
        self._generator_model.editScaffoldPackageOption(optionName)
        self._refreshScaffoldTypeNames()
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()

    def _meshTypeOptionLineEditChanged(self, lineEdit):
        dependentChanges = self._generator_model.setScaffoldOption(lineEdit.objectName(), lineEdit.text())
        if dependentChanges:
            self._refreshScaffoldOptions()
        else:
            finalValue = self._generator_model.getEditScaffoldOption(lineEdit.objectName())
            lineEdit.setText(str(finalValue))

    def _refreshScaffoldOptions(self):
        layout = self._ui.meshTypeOptions_frame.layout()
        # remove all current mesh type widgets
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
              child.widget().deleteLater()
        optionNames = self._generator_model.getEditScaffoldOrderedOptionNames()
        for key in optionNames:
            value = self._generator_model.getEditScaffoldOption(key)
            # print('key ', key, ' value ', value)
            if type(value) is bool:
                checkBox = QtGui.QCheckBox(self._ui.meshTypeOptions_frame)
                checkBox.setObjectName(key)
                checkBox.setText(key)
                checkBox.setChecked(value)
                callback = partial(self._meshTypeOptionCheckBoxClicked, checkBox)
                checkBox.clicked.connect(callback)
                layout.addWidget(checkBox)
            else:
                label = QtGui.QLabel(self._ui.meshTypeOptions_frame)
                label.setObjectName(key)
                label.setText(key)
                layout.addWidget(label)
                if isinstance(value, ScaffoldPackage):
                    pushButton = QtGui.QPushButton()
                    pushButton.setObjectName(key)
                    pushButton.setText('Edit >>')
                    callback = partial(self._meshTypeOptionScaffoldPackageButtonPressed, pushButton)
                    pushButton.clicked.connect(callback)
                    layout.addWidget(pushButton)
                else:
                    lineEdit = QtGui.QLineEdit(self._ui.meshTypeOptions_frame)
                    lineEdit.setObjectName(key)
                    lineEdit.setText(str(value))
                    callback = partial(self._meshTypeOptionLineEditChanged, lineEdit)
                    #lineEdit.returnPressed.connect(callback)
                    lineEdit.editingFinished.connect(callback)
                    layout.addWidget(lineEdit)
        # refresh or show/hide standard scaffold options for transformation and deleting element ranges
        editingRootScaffold = self._generator_model.editingRootScaffoldPackage()
        self._ui.done_button.setEnabled(editingRootScaffold)
        self._ui.subscaffold_frame.setVisible(not editingRootScaffold)
        if editingRootScaffold:
            self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())
        else:
            self._ui.subscaffold_label.setText(self._generator_model.getEditScaffoldOptionDisplayName())
        self._ui.deleteElementsRanges_frame.setVisible(editingRootScaffold)
        self._ui.rotation_lineEdit.setText(self._generator_model.getRotationText())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())
        self._ui.translation_lineEdit.setText(self._generator_model.getTranslationText())

    def _refreshOptions(self):
        self._ui.identifier_label.setText('Identifier:  ' + self._model.getIdentifier())
        self._ui.displayDataContours_checkBox.setChecked(self._segmentation_data_model.isDisplayDataContours())
        self._ui.displayDataMarkerPoints_checkBox.setChecked(self._segmentation_data_model.isDisplayDataMarkerPoints())
        self._ui.displayDataMarkerNames_checkBox.setChecked(self._segmentation_data_model.isDisplayDataMarkerNames())
        self._ui.displayData_frame.setVisible(self._segmentation_data_model.hasData())
        self._ui.displayMarkerPoints_checkBox.setChecked(self._generator_model.isDisplayMarkerPoints())
        self._ui.displayAxes_checkBox.setChecked(self._generator_model.isDisplayAxes())
        self._ui.displayElementNumbers_checkBox.setChecked(self._generator_model.isDisplayElementNumbers())
        self._ui.displayElementAxes_checkBox.setChecked(self._generator_model.isDisplayElementAxes())
        self._ui.displayLines_checkBox.setChecked(self._generator_model.isDisplayLines())
        self._ui.displayLinesExterior_checkBox.setChecked(self._generator_model.isDisplayLinesExterior())
        self._ui.displayNodeDerivativeLabelsD1_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D1'))
        self._ui.displayNodeDerivativeLabelsD2_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D2'))
        self._ui.displayNodeDerivativeLabelsD3_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D3'))
        self._ui.displayNodeDerivativeLabelsD12_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D12'))
        self._ui.displayNodeDerivativeLabelsD13_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D13'))
        self._ui.displayNodeDerivativeLabelsD23_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D23'))
        self._ui.displayNodeDerivativeLabelsD123_checkBox.setChecked(self._generator_model.isDisplayNodeDerivativeLabels('D123'))
        self._ui.displayNodeDerivatives_checkBox.setChecked(self._generator_model.isDisplayNodeDerivatives())
        self._ui.displayNodeNumbers_checkBox.setChecked(self._generator_model.isDisplayNodeNumbers())
        self._ui.displayNodePoints_checkBox.setChecked(self._generator_model.isDisplayNodePoints())
        self._ui.displaySurfaces_checkBox.setChecked(self._generator_model.isDisplaySurfaces())
        self._ui.displaySurfacesExterior_checkBox.setChecked(self._generator_model.isDisplaySurfacesExterior())
        self._ui.displaySurfacesTranslucent_checkBox.setChecked(self._generator_model.isDisplaySurfacesTranslucent())
        self._ui.displaySurfacesWireframe_checkBox.setChecked(self._generator_model.isDisplaySurfacesWireframe())
        index = self._ui.meshType_comboBox.findText(self._generator_model.getEditScaffoldTypeName())
        self._ui.meshType_comboBox.blockSignals(True)
        self._ui.meshType_comboBox.setCurrentIndex(index)
        self._ui.meshType_comboBox.blockSignals(False)
        self._refreshParameterSetNames()
        self._refreshScaffoldOptions()
        self._ui.done_button.setEnabled(True)
        self._ui.subscaffold_frame.setVisible(False)

    def _deleteElementRangesLineEditChanged(self):
        self._generator_model.setDeleteElementsRangesText(self._ui.deleteElementsRanges_lineEdit.text())
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())

    def _deleteElementsSelectionButtonPressed(self):
        self._generator_model.deleteElementsSelection()
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())

    def _rotationLineEditChanged(self):
        self._generator_model.setRotationText(self._ui.rotation_lineEdit.text())
        self._ui.rotation_lineEdit.setText(self._generator_model.getRotationText())

    def _scaleLineEditChanged(self):
        self._generator_model.setScaleText(self._ui.scale_lineEdit.text())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())

    def _translationLineEditChanged(self):
        self._generator_model.setTranslationText(self._ui.translation_lineEdit.text())
        self._ui.translation_lineEdit.setText(self._generator_model.getTranslationText())

    def _displayDataContoursClicked(self):
        self._segmentation_data_model.setDisplayDataContours(self._ui.displayDataContours_checkBox.isChecked())

    def _displayDataMarkerPointsClicked(self):
        self._segmentation_data_model.setDisplayDataMarkerPoints(self._ui.displayDataMarkerPoints_checkBox.isChecked())

    def _displayDataMarkerNamesClicked(self):
        self._segmentation_data_model.setDisplayDataMarkerNames(self._ui.displayDataMarkerNames_checkBox.isChecked())

    def _displayMarkerPointsClicked(self):
        self._generator_model.setDisplayMarkerPoints(self._ui.displayMarkerPoints_checkBox.isChecked())

    def _displayAxesClicked(self):
        self._generator_model.setDisplayAxes(self._ui.displayAxes_checkBox.isChecked())

    def _displayElementAxesClicked(self):
        self._generator_model.setDisplayElementAxes(self._ui.displayElementAxes_checkBox.isChecked())

    def _displayElementNumbersClicked(self):
        self._generator_model.setDisplayElementNumbers(self._ui.displayElementNumbers_checkBox.isChecked())

    def _displayLinesClicked(self):
        self._generator_model.setDisplayLines(self._ui.displayLines_checkBox.isChecked())
        self._autoPerturbLines()

    def _displayLinesExteriorClicked(self):
        self._generator_model.setDisplayLinesExterior(self._ui.displayLinesExterior_checkBox.isChecked())

    def _displayNodeDerivativesClicked(self):
        self._generator_model.setDisplayNodeDerivatives(self._ui.displayNodeDerivatives_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD1Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D1', self._ui.displayNodeDerivativeLabelsD1_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD2Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D2', self._ui.displayNodeDerivativeLabelsD2_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD3Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D3', self._ui.displayNodeDerivativeLabelsD3_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD12Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D12', self._ui.displayNodeDerivativeLabelsD12_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD13Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D13', self._ui.displayNodeDerivativeLabelsD13_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD23Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D23', self._ui.displayNodeDerivativeLabelsD23_checkBox.isChecked())

    def _displayNodeDerivativeLabelsD123Clicked(self):
        self._generator_model.setDisplayNodeDerivativeLabels('D123', self._ui.displayNodeDerivativeLabelsD123_checkBox.isChecked())

    def _displayNodeNumbersClicked(self):
        self._generator_model.setDisplayNodeNumbers(self._ui.displayNodeNumbers_checkBox.isChecked())

    def _displayNodePointsClicked(self):
        self._generator_model.setDisplayNodePoints(self._ui.displayNodePoints_checkBox.isChecked())

    def _displaySurfacesClicked(self):
        self._generator_model.setDisplaySurfaces(self._ui.displaySurfaces_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesExteriorClicked(self):
        self._generator_model.setDisplaySurfacesExterior(self._ui.displaySurfacesExterior_checkBox.isChecked())

    def _displaySurfacesTranslucentClicked(self):
        self._generator_model.setDisplaySurfacesTranslucent(self._ui.displaySurfacesTranslucent_checkBox.isChecked())
        self._autoPerturbLines()

    def _displaySurfacesWireframeClicked(self):
        self._generator_model.setDisplaySurfacesWireframe(self._ui.displaySurfacesWireframe_checkBox.isChecked())

    def _annotationItemChanged(self, item):
        print(item.text(0))
        print(item.data(0, QtCore.Qt.UserRole + 1))

    def _viewAll(self):
        """
        Ask sceneviewer to show all of scene.
        """
        if self._ui.sceneviewer_widget.getSceneviewer() is not None:
            self._ui.sceneviewer_widget.viewAll()
