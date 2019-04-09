'''
Derived SceneviewerWidget capable of editing node coordinate positions and derivatives.
'''

import math
from PySide import QtCore
from opencmiss.zincwidgets.sceneviewerwidget import SceneviewerWidget, SelectionMode
from opencmiss.zinc.field import Field
from opencmiss.zinc.graphics import Graphics
from opencmiss.zinc.scenecoordinatesystem import SCENECOORDINATESYSTEM_WINDOW_PIXEL_TOP_LEFT
from opencmiss.zinc.result import RESULT_OK as ZINC_RESULT_OK

class NodeEditorSceneviewerWidget(SceneviewerWidget):
    '''
    classdocs
    '''

    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(NodeEditorSceneviewerWidget, self).__init__(parent)
        self._model = None
        self._editNode = None
        self._editGraphics = None
        self._lastMousePos = None

    def setGeneratorModel(self, model):
        self._model = model

    def getNearestNodeAndGraphics(self, x, y):
        '''
        :return: Node, Graphics OR None, None if none found.
        '''
        oldNodeSelectMode = self._nodeSelectMode
        oldDataSelectMode = self._dataSelectMode
        oldElemSelectMode = self._elemSelectMode
        self.setSelectModeNode()
        #print('pick',x,y,self._selectTol, 'DpiX', self.physicalDpiX(), self.logicalDpiX(), 'DpiY', self.physicalDpiY(), self.logicalDpiY())
        #print('  width', self.width(), 'widthMM',self.widthMM(),'dpi',25.4*self.width()/self.widthMM(),
        #      'height', self.height(), 'heightMM',self.heightMM(),'dpi',25.4*self.height()/self.heightMM())
        #app = QtCore.QCoreApplication.instance()
        #desktop = app.desktop()
        #dpmm = self.width()/self.widthMM()
        #print('dpmm',dpmm,'physicalDpiX',desktop.physicalDpiX(),'screenGeometry',desktop.screenGeometry(self))
        tol = self._selectTol  # *0.1*dpmm
        #print('tol',tol)
        self._scenepicker.setSceneviewerRectangle(self._sceneviewer, SCENECOORDINATESYSTEM_WINDOW_PIXEL_TOP_LEFT,
            x - tol, y - tol, x + tol, y + tol)
        node = self._scenepicker.getNearestNode()
        if node.isValid():
            graphics = self._scenepicker.getNearestNodeGraphics()
        else:
            node = None
            graphics = None
        self._nodeSelectMode = oldNodeSelectMode
        self._dataSelectMode = oldDataSelectMode
        self._elemSelectMode = oldElemSelectMode
        return node, graphics

    def selectNode(self, node):
        nodeset = node.getNodeset()
        fieldmodule = nodeset.getFieldmodule()
        fieldmodule.beginChange()
        selectionGroup = self.getOrCreateSelectionGroup()
        selectionGroup.clear()
        nodegroup = selectionGroup.getFieldNodeGroup(nodeset)
        if not nodegroup.isValid():
            nodegroup = selectionGroup.createFieldNodeGroup(nodeset)
        nodesetGroup = nodegroup.getNodesetGroup()
        result = nodesetGroup.addNode(node)
        fieldmodule.endChange()

    def mousePressEvent(self, event):
        if (event.button() == QtCore.Qt.LeftButton) and self._selectionKeyPressed:
            node, graphics = self.getNearestNodeAndGraphics(event.x(), event.y())
            if node and (graphics.getType() == Graphics.TYPE_POINTS) and (graphics.getFieldDomainType() == Field.DOMAIN_TYPE_NODES):
                #print('NodeEditorSceneviewerWidget.mousePressEvent node:', node.getIdentifier())
                self.selectNode(node)
                self._editNode = node
                self._editGraphics = graphics
                self._lastMousePos = [ event.x(), event.y() ]
                return
        self._editNode = None
        self._lastMousePos = None
        super(NodeEditorSceneviewerWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._editNode:
            mousePos = [ event.x(), event.y() ]
            nodeset = self._editNode.getNodeset()
            fieldmodule = nodeset.getFieldmodule()
            fieldmodule.beginChange()
            meshEditsNodeset = self._model.getOrCreateMeshEditsNodesetGroup(nodeset)
            meshEditsNodeset.addNode(self._editNode)
            editCoordinateField = coordinateField = self._editGraphics.getCoordinateField()
            if coordinateField.getCoordinateSystemType() != Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN:
                editCoordinateField = fieldmodule.createFieldCoordinateTransformation(coordinateField)
                editCoordinateField.setCoordinateSystemType(Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN)
            fieldcache = fieldmodule.createFieldcache()
            fieldcache.setNode(self._editNode)
            componentsCount = coordinateField.getNumberOfComponents()
            result, initialCoordinates = editCoordinateField.evaluateReal(fieldcache, 3)
            if result == ZINC_RESULT_OK:
                for c in range(componentsCount, 3):
                    initialCoordinates.append(0.0)
                pointattr = self._editGraphics.getGraphicspointattributes()
                editVectorField = vectorField = pointattr.getOrientationScaleField()
                pointBaseSize = pointattr.getBaseSize(3)[1][0]
                pointScaleFactor = pointattr.getScaleFactors(3)[1][0]
                if editVectorField.isValid() and (vectorField.getNumberOfComponents() == componentsCount) \
                        and (pointBaseSize == 0.0) and (pointScaleFactor != 0.0):
                    if vectorField.getCoordinateSystemType() != Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN:
                        editVectorField = fieldmodule.createFieldCoordinateTransformation(vectorField, coordinateField)
                        editVectorField.setCoordinateSystemType(Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN)
                    result, initialVector = editVectorField.evaluateReal(fieldcache, 3)
                    for c in range(componentsCount, 3):
                        initialVector.append(0.0)
                    initialTipCoordinates = [ (initialCoordinates[c] + initialVector[c]*pointScaleFactor) for c in range(3) ]
                    windowCoordinates = self.project(initialTipCoordinates[0], initialTipCoordinates[1], initialTipCoordinates[2])
                    finalTipCoordinates = self.unproject(mousePos[0], -mousePos[1], windowCoordinates[2])
                    finalVector = [ (finalTipCoordinates[c] - initialCoordinates[c])/pointScaleFactor for c in range(3) ]
                    result = editVectorField.assignReal(fieldcache, finalVector)
                else:
                    windowCoordinates = self.project(initialCoordinates[0], initialCoordinates[1], initialCoordinates[2])
                    xa = self.unproject(self._lastMousePos[0], -self._lastMousePos[1], windowCoordinates[2])
                    xb = self.unproject(mousePos[0], -mousePos[1], windowCoordinates[2])
                    finalCoordinates = [ (initialCoordinates[c] + xb[c] - xa[c]) for c in range(3)]
                    result = editCoordinateField.assignReal(fieldcache, finalCoordinates)
            del editCoordinateField
            del editVectorField
            del fieldcache
            fieldmodule.endChange()
            self._lastMousePos = mousePos
        else:
            super(NodeEditorSceneviewerWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._editNode:
            self._editNode = None
            self._lastMousePos = None
            self._editCoordinateField = None
            self._editVectorField = None
        else:
            super(NodeEditorSceneviewerWidget, self).mouseReleaseEvent(event)
