# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'scaffoldcreatorwidget.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from mapclientplugins.scaffoldcreator.view.nodeeditorsceneviewerwidget import NodeEditorSceneviewerWidget
from opencmiss.zincwidgets.fieldchooserwidget import FieldChooserWidget

from mapclientplugins.scaffoldcreator import resources_rc


class Ui_ScaffoldCreatorWidget(object):
    def setupUi(self, ScaffoldCreatorWidget):
        if not ScaffoldCreatorWidget.objectName():
            ScaffoldCreatorWidget.setObjectName(u"ScaffoldCreatorWidget")
        ScaffoldCreatorWidget.resize(1672, 1223)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ScaffoldCreatorWidget.sizePolicy().hasHeightForWidth())
        ScaffoldCreatorWidget.setSizePolicy(sizePolicy)
        ScaffoldCreatorWidget.setMinimumSize(QSize(0, 0))
        self.horizontalLayout = QHBoxLayout(ScaffoldCreatorWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.dockWidget = QDockWidget(ScaffoldCreatorWidget)
        self.dockWidget.setObjectName(u"dockWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dockWidget.sizePolicy().hasHeightForWidth())
        self.dockWidget.setSizePolicy(sizePolicy1)
        self.dockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidget.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        sizePolicy1.setHeightForWidth(self.dockWidgetContents.sizePolicy().hasHeightForWidth())
        self.dockWidgetContents.setSizePolicy(sizePolicy1)
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.identifier_frame = QFrame(self.dockWidgetContents)
        self.identifier_frame.setObjectName(u"identifier_frame")
        self.identifier_frame.setMinimumSize(QSize(0, 0))
        self.identifier_frame.setFrameShape(QFrame.StyledPanel)
        self.identifier_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.identifier_frame)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 5, 0, 3)
        self.identifier_label = QLabel(self.identifier_frame)
        self.identifier_label.setObjectName(u"identifier_label")

        self.verticalLayout_4.addWidget(self.identifier_label)


        self.verticalLayout.addWidget(self.identifier_frame)

        self.scrollArea = QScrollArea(self.dockWidgetContents)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy1.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy1)
        self.scrollArea.setMinimumSize(QSize(0, 0))
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 446, 726))
        sizePolicy1.setHeightForWidth(self.scrollAreaWidgetContents_2.sizePolicy().hasHeightForWidth())
        self.scrollAreaWidgetContents_2.setSizePolicy(sizePolicy1)
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scaffoldFrame = QFrame(self.scrollAreaWidgetContents_2)
        self.scaffoldFrame.setObjectName(u"scaffoldFrame")
        sizePolicy.setHeightForWidth(self.scaffoldFrame.sizePolicy().hasHeightForWidth())
        self.scaffoldFrame.setSizePolicy(sizePolicy)
        self.scaffoldFrame.setMinimumSize(QSize(0, 0))
        self.scaffoldFrame.setFrameShape(QFrame.StyledPanel)
        self.scaffoldFrame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_8 = QVBoxLayout(self.scaffoldFrame)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.subscaffold_frame = QFrame(self.scaffoldFrame)
        self.subscaffold_frame.setObjectName(u"subscaffold_frame")
        sizePolicy.setHeightForWidth(self.subscaffold_frame.sizePolicy().hasHeightForWidth())
        self.subscaffold_frame.setSizePolicy(sizePolicy)
        self.subscaffold_frame.setMinimumSize(QSize(0, 0))
        self.subscaffold_frame.setFrameShape(QFrame.StyledPanel)
        self.subscaffold_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.subscaffold_frame)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.subscaffold_label = QLabel(self.subscaffold_frame)
        self.subscaffold_label.setObjectName(u"subscaffold_label")

        self.verticalLayout_5.addWidget(self.subscaffold_label)

        self.subscaffoldBack_pushButton = QPushButton(self.subscaffold_frame)
        self.subscaffoldBack_pushButton.setObjectName(u"subscaffoldBack_pushButton")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.subscaffoldBack_pushButton.sizePolicy().hasHeightForWidth())
        self.subscaffoldBack_pushButton.setSizePolicy(sizePolicy2)

        self.verticalLayout_5.addWidget(self.subscaffoldBack_pushButton)


        self.verticalLayout_8.addWidget(self.subscaffold_frame)

        self.meshType_frame = QFrame(self.scaffoldFrame)
        self.meshType_frame.setObjectName(u"meshType_frame")
        self.meshType_frame.setFrameShape(QFrame.StyledPanel)
        self.meshType_frame.setFrameShadow(QFrame.Raised)
        self.formLayout = QFormLayout(self.meshType_frame)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, -1, 0, -1)
        self.meshType_label = QLabel(self.meshType_frame)
        self.meshType_label.setObjectName(u"meshType_label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.meshType_label)

        self.meshType_comboBox = QComboBox(self.meshType_frame)
        self.meshType_comboBox.setObjectName(u"meshType_comboBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.meshType_comboBox)

        self.parameterSet_label = QLabel(self.meshType_frame)
        self.parameterSet_label.setObjectName(u"parameterSet_label")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.parameterSet_label)

        self.parameterSet_comboBox = QComboBox(self.meshType_frame)
        self.parameterSet_comboBox.setObjectName(u"parameterSet_comboBox")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.parameterSet_comboBox)


        self.verticalLayout_8.addWidget(self.meshType_frame)

        self.meshTypeOptions_frame = QFrame(self.scaffoldFrame)
        self.meshTypeOptions_frame.setObjectName(u"meshTypeOptions_frame")
        self.meshTypeOptions_frame.setFrameShape(QFrame.StyledPanel)
        self.meshTypeOptions_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_9 = QVBoxLayout(self.meshTypeOptions_frame)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, -1, 0, -1)

        self.verticalLayout_8.addWidget(self.meshTypeOptions_frame)

        self.scaffoldFrame_line_1 = QFrame(self.scaffoldFrame)
        self.scaffoldFrame_line_1.setObjectName(u"scaffoldFrame_line_1")
        self.scaffoldFrame_line_1.setFrameShape(QFrame.HLine)
        self.scaffoldFrame_line_1.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_8.addWidget(self.scaffoldFrame_line_1)

        self.modifyOptions_frame = QFrame(self.scaffoldFrame)
        self.modifyOptions_frame.setObjectName(u"modifyOptions_frame")
        self.modifyOptions_frame.setFrameShape(QFrame.StyledPanel)
        self.modifyOptions_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.modifyOptions_frame)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, -1, 0, -1)
        self.deleteElementsRanges_frame = QFrame(self.modifyOptions_frame)
        self.deleteElementsRanges_frame.setObjectName(u"deleteElementsRanges_frame")
        self.deleteElementsRanges_frame.setFrameShape(QFrame.StyledPanel)
        self.deleteElementsRanges_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_10 = QVBoxLayout(self.deleteElementsRanges_frame)
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.deleteElementsRanges_label = QLabel(self.deleteElementsRanges_frame)
        self.deleteElementsRanges_label.setObjectName(u"deleteElementsRanges_label")

        self.verticalLayout_10.addWidget(self.deleteElementsRanges_label)

        self.deleteElementsRanges_lineEdit = QLineEdit(self.deleteElementsRanges_frame)
        self.deleteElementsRanges_lineEdit.setObjectName(u"deleteElementsRanges_lineEdit")

        self.verticalLayout_10.addWidget(self.deleteElementsRanges_lineEdit)

        self.deleteElementsSelection_pushButton = QPushButton(self.deleteElementsRanges_frame)
        self.deleteElementsSelection_pushButton.setObjectName(u"deleteElementsSelection_pushButton")

        self.verticalLayout_10.addWidget(self.deleteElementsSelection_pushButton)


        self.verticalLayout_6.addWidget(self.deleteElementsRanges_frame)

        self.rotation_label = QLabel(self.modifyOptions_frame)
        self.rotation_label.setObjectName(u"rotation_label")

        self.verticalLayout_6.addWidget(self.rotation_label)

        self.rotation_lineEdit = QLineEdit(self.modifyOptions_frame)
        self.rotation_lineEdit.setObjectName(u"rotation_lineEdit")

        self.verticalLayout_6.addWidget(self.rotation_lineEdit)

        self.scale_label = QLabel(self.modifyOptions_frame)
        self.scale_label.setObjectName(u"scale_label")

        self.verticalLayout_6.addWidget(self.scale_label)

        self.scale_lineEdit = QLineEdit(self.modifyOptions_frame)
        self.scale_lineEdit.setObjectName(u"scale_lineEdit")

        self.verticalLayout_6.addWidget(self.scale_lineEdit)

        self.translation_label = QLabel(self.modifyOptions_frame)
        self.translation_label.setObjectName(u"translation_label")

        self.verticalLayout_6.addWidget(self.translation_label)

        self.translation_lineEdit = QLineEdit(self.modifyOptions_frame)
        self.translation_lineEdit.setObjectName(u"translation_lineEdit")

        self.verticalLayout_6.addWidget(self.translation_lineEdit)

        self.applyTransformation_pushButton = QPushButton(self.modifyOptions_frame)
        self.applyTransformation_pushButton.setObjectName(u"applyTransformation_pushButton")

        self.verticalLayout_6.addWidget(self.applyTransformation_pushButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.verticalLayout_8.addWidget(self.modifyOptions_frame)


        self.verticalLayout_3.addWidget(self.scaffoldFrame)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout.addWidget(self.scrollArea)

        self.controls_tabWidget = QTabWidget(self.dockWidgetContents)
        self.controls_tabWidget.setObjectName(u"controls_tabWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.controls_tabWidget.sizePolicy().hasHeightForWidth())
        self.controls_tabWidget.setSizePolicy(sizePolicy3)
        self.display_tab = QWidget()
        self.display_tab.setObjectName(u"display_tab")
        self.verticalLayout_13 = QVBoxLayout(self.display_tab)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.displayData_frame = QFrame(self.display_tab)
        self.displayData_frame.setObjectName(u"displayData_frame")
        self.displayData_frame.setFrameShape(QFrame.StyledPanel)
        self.displayData_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_11 = QVBoxLayout(self.displayData_frame)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.displayDataPoints_frame = QFrame(self.displayData_frame)
        self.displayDataPoints_frame.setObjectName(u"displayDataPoints_frame")
        self.displayDataPoints_frame.setFrameShape(QFrame.StyledPanel)
        self.displayDataPoints_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.displayDataPoints_frame)
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.displayDataPoints_checkBox = QCheckBox(self.displayDataPoints_frame)
        self.displayDataPoints_checkBox.setObjectName(u"displayDataPoints_checkBox")

        self.horizontalLayout_9.addWidget(self.displayDataPoints_checkBox)

        self.displayDataContours_checkBox = QCheckBox(self.displayDataPoints_frame)
        self.displayDataContours_checkBox.setObjectName(u"displayDataContours_checkBox")

        self.horizontalLayout_9.addWidget(self.displayDataContours_checkBox)

        self.displayDataRadius_checkBox = QCheckBox(self.displayDataPoints_frame)
        self.displayDataRadius_checkBox.setObjectName(u"displayDataRadius_checkBox")

        self.horizontalLayout_9.addWidget(self.displayDataRadius_checkBox)

        self.displayDataPoints_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_9.addItem(self.displayDataPoints_horizontalSpacer)


        self.verticalLayout_11.addWidget(self.displayDataPoints_frame)

        self.displayDataMarkers_frame = QFrame(self.displayData_frame)
        self.displayDataMarkers_frame.setObjectName(u"displayDataMarkers_frame")
        self.displayDataMarkers_frame.setFrameShape(QFrame.StyledPanel)
        self.displayDataMarkers_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.displayDataMarkers_frame)
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.displayDataMarkerPoints_checkBox = QCheckBox(self.displayDataMarkers_frame)
        self.displayDataMarkerPoints_checkBox.setObjectName(u"displayDataMarkerPoints_checkBox")

        self.horizontalLayout_10.addWidget(self.displayDataMarkerPoints_checkBox)

        self.displayDataMarkerNames_checkBox = QCheckBox(self.displayDataMarkers_frame)
        self.displayDataMarkerNames_checkBox.setObjectName(u"displayDataMarkerNames_checkBox")

        self.horizontalLayout_10.addWidget(self.displayDataMarkerNames_checkBox)

        self.displayDataMarkers_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_10.addItem(self.displayDataMarkers_horizontalSpacer)


        self.verticalLayout_11.addWidget(self.displayDataMarkers_frame)


        self.verticalLayout_13.addWidget(self.displayData_frame)

        self.displayModelCoordinates_frame = QFrame(self.display_tab)
        self.displayModelCoordinates_frame.setObjectName(u"displayModelCoordinates_frame")
        self.displayModelCoordinates_frame.setFrameShape(QFrame.StyledPanel)
        self.displayModelCoordinates_frame.setFrameShadow(QFrame.Raised)
        self.formLayout_3 = QFormLayout(self.displayModelCoordinates_frame)
        self.formLayout_3.setContentsMargins(0, 0, 0, 0)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.displayModelCoordinates_label = QLabel(self.displayModelCoordinates_frame)
        self.displayModelCoordinates_label.setObjectName(u"displayModelCoordinates_label")

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.displayModelCoordinates_label)

        self.displayModelCoordinates_fieldChooser = FieldChooserWidget(self.displayModelCoordinates_frame)
        self.displayModelCoordinates_fieldChooser.setObjectName(u"displayModelCoordinates_fieldChooser")

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.displayModelCoordinates_fieldChooser)


        self.verticalLayout_13.addWidget(self.displayModelCoordinates_frame)

        self.displayNodes_frame = QFrame(self.display_tab)
        self.displayNodes_frame.setObjectName(u"displayNodes_frame")
        self.displayNodes_frame.setFrameShape(QFrame.StyledPanel)
        self.displayNodes_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.displayNodes_frame)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.displayNodePoints_checkBox = QCheckBox(self.displayNodes_frame)
        self.displayNodePoints_checkBox.setObjectName(u"displayNodePoints_checkBox")

        self.horizontalLayout_6.addWidget(self.displayNodePoints_checkBox)

        self.displayNodeNumbers_checkBox = QCheckBox(self.displayNodes_frame)
        self.displayNodeNumbers_checkBox.setObjectName(u"displayNodeNumbers_checkBox")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.displayNodeNumbers_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeNumbers_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_6.addWidget(self.displayNodeNumbers_checkBox)

        self.displayNodeDerivatives_checkBox = QCheckBox(self.displayNodes_frame)
        self.displayNodeDerivatives_checkBox.setObjectName(u"displayNodeDerivatives_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivatives_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivatives_checkBox.setSizePolicy(sizePolicy4)
        self.displayNodeDerivatives_checkBox.setTristate(True)

        self.horizontalLayout_6.addWidget(self.displayNodeDerivatives_checkBox)

        self.displayNodes_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_6.addItem(self.displayNodes_horizontalSpacer)


        self.verticalLayout_13.addWidget(self.displayNodes_frame)

        self.displayNodeDerivativeLabels_frame = QFrame(self.display_tab)
        self.displayNodeDerivativeLabels_frame.setObjectName(u"displayNodeDerivativeLabels_frame")
        self.displayNodeDerivativeLabels_frame.setFrameShape(QFrame.StyledPanel)
        self.displayNodeDerivativeLabels_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.displayNodeDerivativeLabels_frame)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.displayNodeDerivativeLabels_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.displayNodeDerivativeLabels_horizontalSpacer)

        self.displayNodeDerivativeLabelsD1_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD1_checkBox.setObjectName(u"displayNodeDerivativeLabelsD1_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD1_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD1_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD1_checkBox)

        self.displayNodeDerivativeLabelsD2_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD2_checkBox.setObjectName(u"displayNodeDerivativeLabelsD2_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD2_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD2_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD2_checkBox)

        self.displayNodeDerivativeLabelsD3_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD3_checkBox.setObjectName(u"displayNodeDerivativeLabelsD3_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD3_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD3_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD3_checkBox)

        self.displayNodeDerivativeLabelsD12_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD12_checkBox.setObjectName(u"displayNodeDerivativeLabelsD12_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD12_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD12_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD12_checkBox)

        self.displayNodeDerivativeLabelsD13_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD13_checkBox.setObjectName(u"displayNodeDerivativeLabelsD13_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD13_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD13_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD13_checkBox)

        self.displayNodeDerivativeLabelsD23_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD23_checkBox.setObjectName(u"displayNodeDerivativeLabelsD23_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD23_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD23_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD23_checkBox)

        self.displayNodeDerivativeLabelsD123_checkBox = QCheckBox(self.displayNodeDerivativeLabels_frame)
        self.displayNodeDerivativeLabelsD123_checkBox.setObjectName(u"displayNodeDerivativeLabelsD123_checkBox")
        sizePolicy4.setHeightForWidth(self.displayNodeDerivativeLabelsD123_checkBox.sizePolicy().hasHeightForWidth())
        self.displayNodeDerivativeLabelsD123_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_7.addWidget(self.displayNodeDerivativeLabelsD123_checkBox)


        self.verticalLayout_13.addWidget(self.displayNodeDerivativeLabels_frame)

        self.displayLines_frame = QFrame(self.display_tab)
        self.displayLines_frame.setObjectName(u"displayLines_frame")
        self.displayLines_frame.setFrameShape(QFrame.StyledPanel)
        self.displayLines_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.displayLines_frame)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.displayLines_checkBox = QCheckBox(self.displayLines_frame)
        self.displayLines_checkBox.setObjectName(u"displayLines_checkBox")

        self.horizontalLayout_5.addWidget(self.displayLines_checkBox)

        self.displayLinesExterior_checkBox = QCheckBox(self.displayLines_frame)
        self.displayLinesExterior_checkBox.setObjectName(u"displayLinesExterior_checkBox")
        sizePolicy4.setHeightForWidth(self.displayLinesExterior_checkBox.sizePolicy().hasHeightForWidth())
        self.displayLinesExterior_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_5.addWidget(self.displayLinesExterior_checkBox)

        self.displayModelRadius_checkBox = QCheckBox(self.displayLines_frame)
        self.displayModelRadius_checkBox.setObjectName(u"displayModelRadius_checkBox")

        self.horizontalLayout_5.addWidget(self.displayModelRadius_checkBox)

        self.displayLines_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.displayLines_horizontalSpacer)


        self.verticalLayout_13.addWidget(self.displayLines_frame)

        self.displaySurfaces_frame = QFrame(self.display_tab)
        self.displaySurfaces_frame.setObjectName(u"displaySurfaces_frame")
        self.displaySurfaces_frame.setFrameShape(QFrame.StyledPanel)
        self.displaySurfaces_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.displaySurfaces_frame)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.displaySurfaces_checkBox = QCheckBox(self.displaySurfaces_frame)
        self.displaySurfaces_checkBox.setObjectName(u"displaySurfaces_checkBox")

        self.horizontalLayout_3.addWidget(self.displaySurfaces_checkBox)

        self.displaySurfacesExterior_checkBox = QCheckBox(self.displaySurfaces_frame)
        self.displaySurfacesExterior_checkBox.setObjectName(u"displaySurfacesExterior_checkBox")
        sizePolicy4.setHeightForWidth(self.displaySurfacesExterior_checkBox.sizePolicy().hasHeightForWidth())
        self.displaySurfacesExterior_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_3.addWidget(self.displaySurfacesExterior_checkBox)

        self.displaySurfacesTranslucent_checkBox = QCheckBox(self.displaySurfaces_frame)
        self.displaySurfacesTranslucent_checkBox.setObjectName(u"displaySurfacesTranslucent_checkBox")
        sizePolicy4.setHeightForWidth(self.displaySurfacesTranslucent_checkBox.sizePolicy().hasHeightForWidth())
        self.displaySurfacesTranslucent_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_3.addWidget(self.displaySurfacesTranslucent_checkBox)

        self.displaySurfacesWireframe_checkBox = QCheckBox(self.displaySurfaces_frame)
        self.displaySurfacesWireframe_checkBox.setObjectName(u"displaySurfacesWireframe_checkBox")
        sizePolicy4.setHeightForWidth(self.displaySurfacesWireframe_checkBox.sizePolicy().hasHeightForWidth())
        self.displaySurfacesWireframe_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_3.addWidget(self.displaySurfacesWireframe_checkBox)

        self.displaySurfaces_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.displaySurfaces_horizontalSpacer)


        self.verticalLayout_13.addWidget(self.displaySurfaces_frame)

        self.displayElements_frame = QFrame(self.display_tab)
        self.displayElements_frame.setObjectName(u"displayElements_frame")
        self.displayElements_frame.setFrameShape(QFrame.StyledPanel)
        self.displayElements_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.displayElements_frame)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.displayElementNumbers_checkBox = QCheckBox(self.displayElements_frame)
        self.displayElementNumbers_checkBox.setObjectName(u"displayElementNumbers_checkBox")

        self.horizontalLayout_4.addWidget(self.displayElementNumbers_checkBox)

        self.displayElementAxes_checkBox = QCheckBox(self.displayElements_frame)
        self.displayElementAxes_checkBox.setObjectName(u"displayElementAxes_checkBox")
        sizePolicy4.setHeightForWidth(self.displayElementAxes_checkBox.sizePolicy().hasHeightForWidth())
        self.displayElementAxes_checkBox.setSizePolicy(sizePolicy4)

        self.horizontalLayout_4.addWidget(self.displayElementAxes_checkBox)

        self.displayElements_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.displayElements_horizontalSpacer)


        self.verticalLayout_13.addWidget(self.displayElements_frame)

        self.displayMisc_frame = QFrame(self.display_tab)
        self.displayMisc_frame.setObjectName(u"displayMisc_frame")
        self.displayMisc_frame.setFrameShape(QFrame.StyledPanel)
        self.displayMisc_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.displayMisc_frame)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.displayAxes_checkBox = QCheckBox(self.displayMisc_frame)
        self.displayAxes_checkBox.setObjectName(u"displayAxes_checkBox")

        self.horizontalLayout_8.addWidget(self.displayAxes_checkBox)

        self.displayMarkerPoints_checkBox = QCheckBox(self.displayMisc_frame)
        self.displayMarkerPoints_checkBox.setObjectName(u"displayMarkerPoints_checkBox")

        self.horizontalLayout_8.addWidget(self.displayMarkerPoints_checkBox)

        self.displaytMisc_horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_8.addItem(self.displaytMisc_horizontalSpacer)


        self.verticalLayout_13.addWidget(self.displayMisc_frame)

        self.controls_tabWidget.addTab(self.display_tab, "")
        self.annotation_tab = QWidget()
        self.annotation_tab.setObjectName(u"annotation_tab")
        self.verticalLayout_12 = QVBoxLayout(self.annotation_tab)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.annoptationModify_frame = QFrame(self.annotation_tab)
        self.annoptationModify_frame.setObjectName(u"annoptationModify_frame")
        self.annoptationModify_frame.setFrameShape(QFrame.StyledPanel)
        self.annoptationModify_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.annoptationModify_frame)
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.annotationGroupNew_pushButton = QPushButton(self.annoptationModify_frame)
        self.annotationGroupNew_pushButton.setObjectName(u"annotationGroupNew_pushButton")

        self.horizontalLayout_11.addWidget(self.annotationGroupNew_pushButton)

        self.annotationGroupNewMarker_pushButton = QPushButton(self.annoptationModify_frame)
        self.annotationGroupNewMarker_pushButton.setObjectName(u"annotationGroupNewMarker_pushButton")

        self.horizontalLayout_11.addWidget(self.annotationGroupNewMarker_pushButton)

        self.annotationGroupRedefine_pushButton = QPushButton(self.annoptationModify_frame)
        self.annotationGroupRedefine_pushButton.setObjectName(u"annotationGroupRedefine_pushButton")

        self.horizontalLayout_11.addWidget(self.annotationGroupRedefine_pushButton)

        self.annotationGroupDelete_pushButton = QPushButton(self.annoptationModify_frame)
        self.annotationGroupDelete_pushButton.setObjectName(u"annotationGroupDelete_pushButton")

        self.horizontalLayout_11.addWidget(self.annotationGroupDelete_pushButton)


        self.verticalLayout_12.addWidget(self.annoptationModify_frame)

        self.annotationGroup_frame = QFrame(self.annotation_tab)
        self.annotationGroup_frame.setObjectName(u"annotationGroup_frame")
        self.annotationGroup_frame.setFrameShape(QFrame.StyledPanel)
        self.annotationGroup_frame.setFrameShadow(QFrame.Raised)
        self.formLayout_2 = QFormLayout(self.annotationGroup_frame)
        self.formLayout_2.setContentsMargins(0, 0, 0, 0)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.annotationGroup_label = QLabel(self.annotationGroup_frame)
        self.annotationGroup_label.setObjectName(u"annotationGroup_label")

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.annotationGroup_label)

        self.annotationGroup_comboBox = QComboBox(self.annotationGroup_frame)
        self.annotationGroup_comboBox.setObjectName(u"annotationGroup_comboBox")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.annotationGroup_comboBox)

        self.annotationGroupOntId_label = QLabel(self.annotationGroup_frame)
        self.annotationGroupOntId_label.setObjectName(u"annotationGroupOntId_label")

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.annotationGroupOntId_label)

        self.annotationGroupOntId_lineEdit = QLineEdit(self.annotationGroup_frame)
        self.annotationGroupOntId_lineEdit.setObjectName(u"annotationGroupOntId_lineEdit")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.annotationGroupOntId_lineEdit)

        self.annotationGroupDimension_label = QLabel(self.annotationGroup_frame)
        self.annotationGroupDimension_label.setObjectName(u"annotationGroupDimension_label")

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.annotationGroupDimension_label)

        self.annotationGroupDimension_spinBox = QSpinBox(self.annotationGroup_frame)
        self.annotationGroupDimension_spinBox.setObjectName(u"annotationGroupDimension_spinBox")
        self.annotationGroupDimension_spinBox.setMinimum(0)
        self.annotationGroupDimension_spinBox.setMaximum(3)
        self.annotationGroupDimension_spinBox.setValue(0)

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.annotationGroupDimension_spinBox)

        self.marker_groupBox = QGroupBox(self.annotationGroup_frame)
        self.marker_groupBox.setObjectName(u"marker_groupBox")
        self.marker_groupBox.setEnabled(True)
        self.formLayout_5 = QFormLayout(self.marker_groupBox)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.formLayout_5.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_5.setHorizontalSpacing(7)
        self.formLayout_5.setVerticalSpacing(7)
        self.formLayout_5.setContentsMargins(-1, 3, -1, 11)
        self.marker_frame = QFrame(self.marker_groupBox)
        self.marker_frame.setObjectName(u"marker_frame")
        self.marker_frame.setFrameShape(QFrame.StyledPanel)
        self.marker_frame.setFrameShadow(QFrame.Raised)
        self.formLayout_4 = QFormLayout(self.marker_frame)
        self.formLayout_4.setContentsMargins(0, 0, 0, 0)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.markerMaterialCoordinates_label = QLabel(self.marker_frame)
        self.markerMaterialCoordinates_label.setObjectName(u"markerMaterialCoordinates_label")

        self.formLayout_4.setWidget(3, QFormLayout.LabelRole, self.markerMaterialCoordinates_label)

        self.markerMaterialCoordinates_lineEdit = QLineEdit(self.marker_frame)
        self.markerMaterialCoordinates_lineEdit.setObjectName(u"markerMaterialCoordinates_lineEdit")

        self.formLayout_4.setWidget(3, QFormLayout.FieldRole, self.markerMaterialCoordinates_lineEdit)

        self.markerElement_label = QLabel(self.marker_frame)
        self.markerElement_label.setObjectName(u"markerElement_label")

        self.formLayout_4.setWidget(4, QFormLayout.LabelRole, self.markerElement_label)

        self.markerElement_lineEdit = QLineEdit(self.marker_frame)
        self.markerElement_lineEdit.setObjectName(u"markerElement_lineEdit")

        self.formLayout_4.setWidget(4, QFormLayout.FieldRole, self.markerElement_lineEdit)

        self.markerXiCoordinates_label = QLabel(self.marker_frame)
        self.markerXiCoordinates_label.setObjectName(u"markerXiCoordinates_label")

        self.formLayout_4.setWidget(5, QFormLayout.LabelRole, self.markerXiCoordinates_label)

        self.markerXiCoordinates_lineEdit = QLineEdit(self.marker_frame)
        self.markerXiCoordinates_lineEdit.setObjectName(u"markerXiCoordinates_lineEdit")

        self.formLayout_4.setWidget(5, QFormLayout.FieldRole, self.markerXiCoordinates_lineEdit)

        self.markerMaterialCoordinatesField_label = QLabel(self.marker_frame)
        self.markerMaterialCoordinatesField_label.setObjectName(u"markerMaterialCoordinatesField_label")

        self.formLayout_4.setWidget(2, QFormLayout.LabelRole, self.markerMaterialCoordinatesField_label)

        self.markerMaterialCoordinatesField_fieldChooser = FieldChooserWidget(self.marker_frame)
        self.markerMaterialCoordinatesField_fieldChooser.setObjectName(u"markerMaterialCoordinatesField_fieldChooser")

        self.formLayout_4.setWidget(2, QFormLayout.FieldRole, self.markerMaterialCoordinatesField_fieldChooser)


        self.formLayout_5.setWidget(0, QFormLayout.SpanningRole, self.marker_frame)


        self.formLayout_2.setWidget(4, QFormLayout.SpanningRole, self.marker_groupBox)


        self.verticalLayout_12.addWidget(self.annotationGroup_frame)

        self.controls_tabWidget.addTab(self.annotation_tab, "")

        self.verticalLayout.addWidget(self.controls_tabWidget)

        self.bottom_frame = QFrame(self.dockWidgetContents)
        self.bottom_frame.setObjectName(u"bottom_frame")
        self.bottom_frame.setFrameShape(QFrame.StyledPanel)
        self.bottom_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.bottom_frame)
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.viewAll_pushButton = QPushButton(self.bottom_frame)
        self.viewAll_pushButton.setObjectName(u"viewAll_pushButton")

        self.horizontalLayout_2.addWidget(self.viewAll_pushButton)

        self.stdViews_pushButton = QPushButton(self.bottom_frame)
        self.stdViews_pushButton.setObjectName(u"stdViews_pushButton")

        self.horizontalLayout_2.addWidget(self.stdViews_pushButton)

        self.done_pushButton = QPushButton(self.bottom_frame)
        self.done_pushButton.setObjectName(u"done_pushButton")
        sizePolicy4.setHeightForWidth(self.done_pushButton.sizePolicy().hasHeightForWidth())
        self.done_pushButton.setSizePolicy(sizePolicy4)

        self.horizontalLayout_2.addWidget(self.done_pushButton)


        self.verticalLayout.addWidget(self.bottom_frame)

        self.dockWidget.setWidget(self.dockWidgetContents)

        self.horizontalLayout.addWidget(self.dockWidget)

        self.sceneviewer_widget = NodeEditorSceneviewerWidget(ScaffoldCreatorWidget)
        self.sceneviewer_widget.setObjectName(u"sceneviewer_widget")
        sizePolicy5 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy5.setHorizontalStretch(4)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.sceneviewer_widget.sizePolicy().hasHeightForWidth())
        self.sceneviewer_widget.setSizePolicy(sizePolicy5)

        self.horizontalLayout.addWidget(self.sceneviewer_widget)


        self.retranslateUi(ScaffoldCreatorWidget)

        self.controls_tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ScaffoldCreatorWidget)
    # setupUi

    def retranslateUi(self, ScaffoldCreatorWidget):
        ScaffoldCreatorWidget.setWindowTitle(QCoreApplication.translate("ScaffoldCreatorWidget", u"Scaffold Creator", None))
        self.dockWidget.setWindowTitle(QCoreApplication.translate("ScaffoldCreatorWidget", u"Control Panel", None))
        self.identifier_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Identifier", None))
        self.subscaffold_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Subscaffold", None))
        self.subscaffoldBack_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"<< Back", None))
        self.meshType_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Mesh type:", None))
        self.parameterSet_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Parameter set:", None))
        self.deleteElementsRanges_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Delete element ID ranges (e.g. 1,2-5,13):", None))
        self.deleteElementsSelection_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Delete selected elements", None))
        self.rotation_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Rotation in degrees about z, y, x", None))
        self.scale_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Scale x, y, z:", None))
        self.translation_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Translation x, y, z", None))
        self.applyTransformation_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Apply transformation", None))
        self.displayDataPoints_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Data points", None))
        self.displayDataContours_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Data contours", None))
        self.displayDataRadius_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Data radius", None))
        self.displayDataMarkerPoints_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Data marker points", None))
        self.displayDataMarkerNames_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Data marker names", None))
        self.displayModelCoordinates_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Model coordinates:", None))
        self.displayNodePoints_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Node points", None))
        self.displayNodeNumbers_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Node numbers", None))
        self.displayNodeDerivatives_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Node derivatives", None))
        self.displayNodeDerivativeLabelsD1_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D1", None))
        self.displayNodeDerivativeLabelsD2_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D2", None))
        self.displayNodeDerivativeLabelsD3_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D3", None))
        self.displayNodeDerivativeLabelsD12_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D12", None))
        self.displayNodeDerivativeLabelsD13_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D13", None))
        self.displayNodeDerivativeLabelsD23_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D23", None))
        self.displayNodeDerivativeLabelsD123_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"D123", None))
        self.displayLines_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Lines", None))
        self.displayLinesExterior_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Exterior", None))
        self.displayModelRadius_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Model radius", None))
        self.displaySurfaces_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Surfaces", None))
        self.displaySurfacesExterior_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Exterior", None))
        self.displaySurfacesTranslucent_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Transluc.", None))
        self.displaySurfacesWireframe_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Wireframe", None))
        self.displayElementNumbers_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Element numbers", None))
        self.displayElementAxes_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Element axes", None))
        self.displayAxes_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Axes", None))
        self.displayMarkerPoints_checkBox.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Marker points", None))
        self.controls_tabWidget.setTabText(self.controls_tabWidget.indexOf(self.display_tab), QCoreApplication.translate("ScaffoldCreatorWidget", u"Display", None))
        self.annotationGroupNew_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"New", None))
        self.annotationGroupNewMarker_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"New Marker", None))
        self.annotationGroupRedefine_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Redefine", None))
        self.annotationGroupDelete_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Delete", None))
        self.annotationGroup_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Group:", None))
        self.annotationGroupOntId_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"ONT:ID:", None))
        self.annotationGroupDimension_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Dimension:", None))
        self.marker_groupBox.setTitle(QCoreApplication.translate("ScaffoldCreatorWidget", u"Marker", None))
        self.markerMaterialCoordinates_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Material coordinates:", None))
        self.markerElement_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Element:", None))
        self.markerXiCoordinates_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Element xi coordinates:", None))
        self.markerMaterialCoordinatesField_label.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Material coordinates field:", None))
        self.controls_tabWidget.setTabText(self.controls_tabWidget.indexOf(self.annotation_tab), QCoreApplication.translate("ScaffoldCreatorWidget", u"Annotation", None))
        self.viewAll_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"View All", None))
        self.stdViews_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Std. Views", None))
        self.done_pushButton.setText(QCoreApplication.translate("ScaffoldCreatorWidget", u"Done", None))
    # retranslateUi

