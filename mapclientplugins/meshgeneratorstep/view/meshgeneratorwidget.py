"""
Created on Aug 29, 2017

@author: Richard Christie
"""
from PySide import QtGui, QtCore
from functools import partial

from mapclientplugins.meshgeneratorstep.view.ui_meshgeneratorwidget import Ui_MeshGeneratorWidget
from opencmiss.utils.maths import vectorops


class MeshGeneratorWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(MeshGeneratorWidget, self).__init__(parent)
        self._ui = Ui_MeshGeneratorWidget()
        self._ui.setupUi(self)
        self._model = model
        self._generator_model = model.getGeneratorModel()
        self._plane_model = model.getPlaneModel()
        self._ui.sceneviewer_widget.setContext(model.getContext())
        self._ui.sceneviewer_widget.setModel(self._plane_model)
        self._model.registerSceneChangeCallback(self._sceneChanged)
        self._doneCallback = None
        # self._populateAnnotationTree()
        meshTypeNames = self._generator_model.getAllMeshTypeNames()
        for meshTypeName in meshTypeNames:
            self._ui.meshType_comboBox.addItem(meshTypeName)
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

    def _sceneChanged(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        if sceneviewer is not None:
            scene = self._model.getScene()
            self._ui.sceneviewer_widget.setScene(scene)
            self._autoPerturbLines()

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
        self._ui.meshType_comboBox.currentIndexChanged.connect(self._meshTypeChanged)
        self._ui.deleteElementsRanges_lineEdit.returnPressed.connect(self._deleteElementRangesLineEditChanged)
        self._ui.deleteElementsRanges_lineEdit.editingFinished.connect(self._deleteElementRangesLineEditChanged)
        self._ui.scale_lineEdit.returnPressed.connect(self._scaleLineEditChanged)
        self._ui.scale_lineEdit.editingFinished.connect(self._scaleLineEditChanged)
        self._ui.displayAxes_checkBox.clicked.connect(self._displayAxesClicked)
        self._ui.displayElementNumbers_checkBox.clicked.connect(self._displayElementNumbersClicked)
        self._ui.displayLines_checkBox.clicked.connect(self._displayLinesClicked)
        self._ui.displayNodeDerivatives_checkBox.clicked.connect(self._displayNodeDerivativesClicked)
        self._ui.displayNodeNumbers_checkBox.clicked.connect(self._displayNodeNumbersClicked)
        self._ui.displaySurfaces_checkBox.clicked.connect(self._displaySurfacesClicked)
        self._ui.displaySurfacesExterior_checkBox.clicked.connect(self._displaySurfacesExteriorClicked)
        self._ui.displaySurfacesTranslucent_checkBox.clicked.connect(self._displaySurfacesTranslucentClicked)
        self._ui.displaySurfacesWireframe_checkBox.clicked.connect(self._displaySurfacesWireframeClicked)
        self._ui.displayXiAxes_checkBox.clicked.connect(self._displayXiAxesClicked)
        self._ui.activeModel_comboBox.currentIndexChanged.connect(self._activeModelChanged)
        self._ui.toImage_pushButton.clicked.connect(self._imageButtonClicked)
        self._ui.displayImagePlane_checkBox.clicked.connect(self._displayImagePlaneClicked)
        self._ui.fixImagePlane_checkBox.clicked.connect(self._fixImagePlaneClicked)
        # self._ui.treeWidgetAnnotation.itemSelectionChanged.connect(self._annotationSelectionChanged)
        # self._ui.treeWidgetAnnotation.itemChanged.connect(self._annotationItemChanged)

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

    def setImageInfo(self, image_info):
        self._plane_model.setImageInfo(image_info)
        if image_info is None:
            self._generator_model.disableAlignment()
            self._plane_model.disableAlignment()
            self._ui.alignment_groupBox.setVisible(False)
            self._ui.fixImagePlane_checkBox.setVisible(False)
            self._ui.displayImagePlane_checkBox.setVisible(False)

    def _doneButtonClicked(self):
        self._ui.dockWidget.setFloating(False)
        self._model.done()
        self._model = None
        self._doneCallback()

    def _imageButtonClicked(self):
        sceneviewer = self._ui.sceneviewer_widget.getSceneviewer()
        normal, up, offset = self._plane_model.getPlaneInfo()
        _, current_lookat_pos = sceneviewer.getLookatPosition()
        _, current_eye_pos = sceneviewer.getEyePosition()
        view_distance = vectorops.magnitude(vectorops.sub(current_eye_pos, current_lookat_pos))
        eye_pos = vectorops.add(vectorops.mult(normal, view_distance), offset)
        lookat_pos = offset
        sceneviewer.setLookatParametersNonSkew(eye_pos, lookat_pos, up)

    def _fixImagePlaneClicked(self):
        self._plane_model.setImagePlaneFixed(self._ui.fixImagePlane_checkBox.isChecked())

    def _displayImagePlaneClicked(self):
        self._plane_model.setImagePlaneVisible(self._ui.displayImagePlane_checkBox.isChecked())

    def _activeModelChanged(self, index):
        if index == 0:
            self._ui.sceneviewer_widget.setModel(self._plane_model)
        else:
            self._ui.sceneviewer_widget.setModel(self._generator_model)

    def _meshTypeChanged(self, index):
        meshTypeName = self._ui.meshType_comboBox.itemText(index)
        self._generator_model.setMeshTypeByName(meshTypeName)
        self._refreshMeshTypeOptions()

    def _meshTypeOptionCheckBoxClicked(self, checkBox):
        self._generator_model.setMeshTypeOption(checkBox.objectName(), checkBox.isChecked())

    def _meshTypeOptionLineEditChanged(self, lineEdit):
        self._generator_model.setMeshTypeOption(lineEdit.objectName(), lineEdit.text())
        finalValue = self._generator_model.getMeshTypeOption(lineEdit.objectName())
        lineEdit.setText(str(finalValue))

    def _refreshMeshTypeOptions(self):
        layout = self._ui.meshTypeOptions_frame.layout()
        # remove all current mesh type widgets
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
              child.widget().deleteLater()
        optionNames = self._generator_model.getMeshTypeOrderedOptionNames()
        for key in optionNames:
            value = self._generator_model.getMeshTypeOption(key)
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
                lineEdit = QtGui.QLineEdit(self._ui.meshTypeOptions_frame)
                lineEdit.setObjectName(key)
                lineEdit.setText(str(value))
                callback = partial(self._meshTypeOptionLineEditChanged, lineEdit)
                lineEdit.returnPressed.connect(callback)
                lineEdit.editingFinished.connect(callback)
                layout.addWidget(lineEdit)

    def _refreshOptions(self):
        self._ui.identifier_label.setText('Identifier:  ' + self._model.getIdentifier())
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())
        self._ui.displayAxes_checkBox.setChecked(self._generator_model.isDisplayAxes())
        self._ui.displayElementNumbers_checkBox.setChecked(self._generator_model.isDisplayElementNumbers())
        self._ui.displayLines_checkBox.setChecked(self._generator_model.isDisplayLines())
        self._ui.displayNodeDerivatives_checkBox.setChecked(self._generator_model.isDisplayNodeDerivatives())
        self._ui.displayNodeNumbers_checkBox.setChecked(self._generator_model.isDisplayNodeNumbers())
        self._ui.displaySurfaces_checkBox.setChecked(self._generator_model.isDisplaySurfaces())
        self._ui.displaySurfacesExterior_checkBox.setChecked(self._generator_model.isDisplaySurfacesExterior())
        self._ui.displaySurfacesTranslucent_checkBox.setChecked(self._generator_model.isDisplaySurfacesTranslucent())
        self._ui.displaySurfacesWireframe_checkBox.setChecked(self._generator_model.isDisplaySurfacesWireframe())
        self._ui.displayXiAxes_checkBox.setChecked(self._generator_model.isDisplayXiAxes())
        self._ui.displayImagePlane_checkBox.setChecked(self._plane_model.isDisplayImagePlane())
        self._ui.fixImagePlane_checkBox.setChecked(self._plane_model.isImagePlaneFixed())
        index = self._ui.meshType_comboBox.findText(self._generator_model.getMeshTypeName())
        self._ui.meshType_comboBox.blockSignals(True)
        self._ui.meshType_comboBox.setCurrentIndex(index)
        self._ui.meshType_comboBox.blockSignals(False)
        self._refreshMeshTypeOptions()

    def _deleteElementRangesLineEditChanged(self):
        self._generator_model.setDeleteElementsRangesText(self._ui.deleteElementsRanges_lineEdit.text())
        self._ui.deleteElementsRanges_lineEdit.setText(self._generator_model.getDeleteElementsRangesText())

    def _scaleLineEditChanged(self):
        self._generator_model.setScaleText(self._ui.scale_lineEdit.text())
        self._ui.scale_lineEdit.setText(self._generator_model.getScaleText())

    def _displayAxesClicked(self):
        self._generator_model.setDisplayAxes(self._ui.displayAxes_checkBox.isChecked())

    def _displayElementNumbersClicked(self):
        self._generator_model.setDisplayElementNumbers(self._ui.displayElementNumbers_checkBox.isChecked())

    def _displayLinesClicked(self):
        self._generator_model.setDisplayLines(self._ui.displayLines_checkBox.isChecked())
        self._autoPerturbLines()

    def _displayNodeDerivativesClicked(self):
        self._generator_model.setDisplayNodeDerivatives(self._ui.displayNodeDerivatives_checkBox.isChecked())

    def _displayNodeNumbersClicked(self):
        self._generator_model.setDisplayNodeNumbers(self._ui.displayNodeNumbers_checkBox.isChecked())

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

    def _displayXiAxesClicked(self):
        self._generator_model.setDisplayXiAxes(self._ui.displayXiAxes_checkBox.isChecked())

    def _annotationItemChanged(self, item):
        print(item.text(0))
        print(item.data(0, QtCore.Qt.UserRole + 1))

    def _viewAll(self):
        """
        Ask sceneviewer to show all of scene.
        """
        if self._ui.sceneviewer_widget.getSceneviewer() is not None:
            self._ui.sceneviewer_widget.viewAll()
