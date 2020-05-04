'''
Derived SceneviewerWidget capable of editing node coordinate positions and derivatives.
'''

from enum import Enum
import math
from PySide import QtCore
from opencmiss.utils.maths.vectorops import add, cross, div, magnitude, mult, sub
from opencmiss.utils.zinc.general import ChangeManager
from opencmiss.zincwidgets.sceneviewerwidget import SceneviewerWidget, SelectionMode
from opencmiss.zinc.field import Field
from opencmiss.zinc.graphics import Graphics
from opencmiss.zinc.scenecoordinatesystem import SCENECOORDINATESYSTEM_LOCAL, SCENECOORDINATESYSTEM_WINDOW_PIXEL_TOP_LEFT
from opencmiss.zinc.result import RESULT_OK

class NodeEditorSceneviewerWidget(SceneviewerWidget):
    '''
    classdocs
    '''

    class AlignMode(Enum):
        NONE = 0
        ROTATION = 1
        SCALE = 2
        TRANSLATION = 3

    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(NodeEditorSceneviewerWidget, self).__init__(parent)
        self._model = None
        self._alignKeyPressed = False
        self._alignMode = self.AlignMode.NONE
        self._editNode = None
        self._editGraphics = None
        self._lastMousePos = None

    def projectLocal(self, x, y, z, localScene):
        """
        Project the given point in local coordinates into window pixel coordinates
        with the origin at the window's top left pixel.
        Note the z pixel coordinate is a depth which is mapped so that -1 is
        on the far clipping plane, and +1 is on the near clipping plane.
        :param localScene: Scene within hierarchy of sceneviewer scene to project local transformation to.
        """
        in_coords = [x, y, z]
        result, out_coords = self._sceneviewer.transformCoordinates(SCENECOORDINATESYSTEM_LOCAL, SCENECOORDINATESYSTEM_WINDOW_PIXEL_TOP_LEFT, localScene, in_coords)
        if result == RESULT_OK:
            return out_coords  # [out_coords[0] / out_coords[3], out_coords[1] / out_coords[3], out_coords[2] / out_coords[3]]

        return None

    def unprojectLocal(self, x, y, z, localScene):
        """
        Unproject the given point in window pixel coordinates where the origin is
        at the window's top left pixel into local coordinates.
        Note the z pixel coordinate is a depth which is mapped so that -1 is
        on the far clipping plane, and +1 is on the near clipping plane.
        :param localScene: Scene within hierarchy of sceneviewer scene to project local transformation to.
        """
        in_coords = [x, y, z]
        result, out_coords = self._sceneviewer.transformCoordinates(SCENECOORDINATESYSTEM_WINDOW_PIXEL_TOP_LEFT, SCENECOORDINATESYSTEM_LOCAL, localScene, in_coords)
        if result == RESULT_OK:
            return out_coords  # [out_coords[0] / out_coords[3], out_coords[1] / out_coords[3], out_coords[2] / out_coords[3]]

        return None

    def setGeneratorModel(self, model):
        self._model = model

    def getNearestNodeAndGraphics(self, x, y):
        '''
        :return: Node, Graphics OR None, None if none found.
        '''
        scenefiltermodule = self._context.getScenefiltermodule()
        with ChangeManager(scenefiltermodule):
            oldSelectionfilter = self.getSelectionfilter()
            self.setSelectionfilter(scenefiltermodule.createScenefilterFieldDomainType(Field.DOMAIN_TYPE_NODES))
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
            self.setSelectionfilter(oldSelectionfilter)
        return node, graphics

    def selectNode(self, node):
        nodeset = node.getNodeset()
        fieldmodule = nodeset.getFieldmodule()
        with ChangeManager(fieldmodule):
            selectionGroup = self.getOrCreateSelectionGroup()
            selectionGroup.clear()
            nodegroup = selectionGroup.getFieldNodeGroup(nodeset)
            if not nodegroup.isValid():
                nodegroup = selectionGroup.createFieldNodeGroup(nodeset)
            nodesetGroup = nodegroup.getNodesetGroup()
            result = nodesetGroup.addNode(node)

    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_A) and (event.isAutoRepeat() == False):
            self._alignKeyPressed = True
            event.setAccepted(True)
        else:
            super(NodeEditorSceneviewerWidget, self).keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if (event.key() == QtCore.Qt.Key_A) and (event.isAutoRepeat() == False):
            self._alignKeyPressed = False
            event.setAccepted(True)
        else:
            super(NodeEditorSceneviewerWidget, self).keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if (self._alignMode == self.AlignMode.NONE) and not self._editNode:
            button = event.button()
            if self._selectionKeyPressed:
                if button == QtCore.Qt.LeftButton:
                    node, graphics = self.getNearestNodeAndGraphics(event.x(), event.y())
                    if node and (graphics.getType() == Graphics.TYPE_POINTS) and (graphics.getFieldDomainType() == Field.DOMAIN_TYPE_NODES):
                        #print('NodeEditorSceneviewerWidget.mousePressEvent node:', node.getIdentifier())
                        self.selectNode(node)
                        self._editNode = node
                        self._editGraphics = graphics
                        self._lastMousePos = [ event.x(), event.y() ]
                        event.accept()
                        return
            if self._model and self._alignKeyPressed:
                # shift-Left button becomes middle button, to support Mac
                if (button == QtCore.Qt.MiddleButton) or ((button == QtCore.Qt.LeftButton) and (event.modifiers() & QtCore.Qt.SHIFT)):
                    self._alignMode = self.AlignMode.TRANSLATION
                elif button == QtCore.Qt.LeftButton:
                    self._alignMode = self.AlignMode.ROTATION
                elif button == QtCore.Qt.RightButton:
                    self._alignMode = self.AlignMode.SCALE
                if self._alignMode != self.AlignMode.NONE:
                    self._editNode = None
                    self._editGraphics = None
                    self._lastMousePos = [ event.x(), event.y() ]
                    event.accept()
                    return
        self._lastMousePos = None
        super(NodeEditorSceneviewerWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._editNode:
            mousePos = [ event.x(), event.y() ]
            nodeset = self._editNode.getNodeset()
            fieldmodule = nodeset.getFieldmodule()
            with ChangeManager(fieldmodule):
                meshEditsNodeset = self._model.getOrCreateMeshEditsNodesetGroup(nodeset)
                meshEditsNodeset.addNode(self._editNode)
                editCoordinateField = coordinateField = self._editGraphics.getCoordinateField()
                localScene = self._editGraphics.getScene()  # need set local scene to get correct transformation
                if coordinateField.getCoordinateSystemType() != Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN:
                    editCoordinateField = fieldmodule.createFieldCoordinateTransformation(coordinateField)
                    editCoordinateField.setCoordinateSystemType(Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN)
                fieldcache = fieldmodule.createFieldcache()
                fieldcache.setNode(self._editNode)
                componentsCount = coordinateField.getNumberOfComponents()
                result, initialCoordinates = editCoordinateField.evaluateReal(fieldcache, componentsCount)
                if result == RESULT_OK:
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
                        result, initialVector = editVectorField.evaluateReal(fieldcache, componentsCount)
                        for c in range(componentsCount, 3):
                            initialVector.append(0.0)
                        initialTipCoordinates = [ (initialCoordinates[c] + initialVector[c]*pointScaleFactor) for c in range(3) ]
                        windowCoordinates = self.projectLocal(initialTipCoordinates[0], initialTipCoordinates[1], initialTipCoordinates[2], localScene)
                        finalTipCoordinates = self.unprojectLocal(mousePos[0], -mousePos[1], windowCoordinates[2], localScene)
                        finalVector = [ (finalTipCoordinates[c] - initialCoordinates[c])/pointScaleFactor for c in range(3) ]
                        result = editVectorField.assignReal(fieldcache, finalVector)
                    else:
                        windowCoordinates = self.projectLocal(initialCoordinates[0], initialCoordinates[1], initialCoordinates[2], localScene)
                        xa = self.unprojectLocal(self._lastMousePos[0], -self._lastMousePos[1], windowCoordinates[2], localScene)
                        xb = self.unprojectLocal(mousePos[0], -mousePos[1], windowCoordinates[2], localScene)
                        finalCoordinates = [ (initialCoordinates[c] + xb[c] - xa[c]) for c in range(3)]
                        result = editCoordinateField.assignReal(fieldcache, finalCoordinates)
                    del editVectorField
                del editCoordinateField
                del fieldcache
            self._lastMousePos = mousePos
            event.accept()
            return
        if self._alignMode != self.AlignMode.NONE:
            mousePos = [ event.x(), event.y() ]
            delta = [ mousePos[0] - self._lastMousePos[0], mousePos[1] - self._lastMousePos[1] ]
            result, eye = self._sceneviewer.getEyePosition()
            result, lookat = self._sceneviewer.getLookatPosition()
            result, up = self._sceneviewer.getUpVector()
            lookatToEye = sub(eye, lookat)
            eyeDistance = magnitude(lookatToEye)
            front = div(lookatToEye, eyeDistance)
            right = cross(up, front)
            if self._alignMode == self.AlignMode.ROTATION:
                mag = magnitude(delta)
                prop = div(delta, mag)
                axis = add(mult(up, prop[0]), mult(right, prop[1]))
                angle = mag*0.002
                #print('delta', delta, 'axis', axis, 'angle', angle)
                self._model.interactionRotate(axis, angle)
            elif self._alignMode == self.AlignMode.SCALE:
                factor = 1.0 + delta[1]*0.0005
                if factor < 0.9:
                    factor = 0.9
                self._model.interactionScale(factor)
            elif self._alignMode == self.AlignMode.TRANSLATION:
                result, l, r, b, t, near, far = self._sceneviewer.getViewingVolume()
                viewportWidth = self.width()
                viewportHeight = self.height()
                if viewportWidth > viewportHeight:
                    eyeScale = (t - b) / viewportHeight
                else:
                    eyeScale = (r - l) / viewportWidth
                offset = add(mult(right, eyeScale*delta[0]), mult(up, -eyeScale*delta[1]))
                self._model.interactionTranslate(offset)
            self._lastMousePos = mousePos
            event.accept()
            return
        else:
            super(NodeEditorSceneviewerWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._lastMousePos = None
        if self._editNode:
            if event.button() == QtCore.Qt.LeftButton:
                self._editNode = None
                self._editCoordinateField = None
                self._editVectorField = None
            event.accept()
            return
        elif self._alignMode != self.AlignMode.NONE:
            self._model.interactionEnd()
            self._alignMode = self.AlignMode.NONE
            event.accept()
            return
        super(NodeEditorSceneviewerWidget, self).mouseReleaseEvent(event)
