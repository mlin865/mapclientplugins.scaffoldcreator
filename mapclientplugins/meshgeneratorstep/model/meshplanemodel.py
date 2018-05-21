import imghdr
import os
import re
import get_image_size

from opencmiss.utils.maths import vectorops
from opencmiss.utils.zinc import createFiniteElementField, createSquare2DFiniteElement, \
    createMaterialUsingImageField, createVolumeImageField
from opencmiss.zinc.scenecoordinatesystem import SCENECOORDINATESYSTEM_LOCAL, \
    SCENECOORDINATESYSTEM_NORMALISED_WINDOW_FIT_CENTRE

from mapclientplugins.meshgeneratorstep.model.meshalignmentmodel import MeshAlignmentModel


class MeshPlaneModel(MeshAlignmentModel):

    def __init__(self, region):
        super(MeshPlaneModel, self).__init__()
        self._region_name = "plane_mesh"
        self._timekeeper = None
        self._image_plane_fixed = False
        self._fixed_coordinate_field = None
        self._fixed_projection_field = None
        self._stationary_projection_field = None
        self._frame_count = 0
        self._parent_region = region
        self._region = None
        self._settings = {
            'display-image-plane': True,
            'image-plane-fixed': False,
            'alignment': {},
        }

    def getPlaneInfo(self):
        original_up = [0.0, 1.0, 0.0]
        original_normal = [0.0, 0.0, 1.0]
        euler_angles = self.getAlignEulerAngles()
        offset = self.getAlignOffset()
        rot = vectorops.eulerToRotationMatrix3(euler_angles)
        normal = vectorops.mxvectormult(rot, original_normal)
        up = vectorops.mxvectormult(rot, original_up)
        return normal, up, offset

    def setImageInfo(self, image_info):
        images = []
        if image_info is not None:
            location = image_info.location()
            if os.path.isdir(location):
                for item in sorted(os.listdir(location), key=alphanum_key):
                    image_candidate = os.path.join(location, item)
                    if imghdr.what(image_candidate):
                        images.append(image_candidate)
            elif os.path.exists(location):
                if imghdr.what(location):
                    images.append(location)

            self._reset()
            self._load_images(images)

    def isImagePlaneFixed(self):
        return self._settings['image-plane-fixed']

    def setImagePlaneFixed(self, state):
        self._settings['image-plane-fixed'] = state
        if self._scene is None:
            return
        fieldmodule = self._region.getFieldmodule()
        surface_graphics = self._scene.findGraphicsByName("plane-surfaces")
        line_graphics = self._scene.findGraphicsByName("plane-lines")
        if surface_graphics.isValid() and state:
            fieldmodule.beginChange()
            cache = fieldmodule.createFieldcache()
            result, projection = self._ndc_projection_field.evaluateReal(cache, 16)
            self._fixed_projection_field.assignReal(cache, projection)
            fieldmodule.endChange()
            surface_graphics.setCoordinateField(self._fixed_coordinate_field)
            line_graphics.setCoordinateField(self._fixed_coordinate_field)
        elif surface_graphics.isValid() and not state:
            cache = fieldmodule.createFieldcache()
            _, t_matrix = self._scene.getTransformationMatrix()
            t_matrix = vectorops.reshape(t_matrix, (4, 4))
            _, projection = self._stationary_projection_field.evaluateReal(cache, 16)
            projection = vectorops.reshape(projection, (4,4))
            projection = vectorops.matrixmult(t_matrix, projection)
            projection = vectorops.reshape(projection, -1)
            rotation_matrix = [[projection[0], projection[1], projection[2]],
                               [projection[4], projection[5], projection[6]],
                               [projection[8], projection[9], projection[10]]]
            euler_angles = vectorops.rotationMatrix3ToEuler(rotation_matrix)
            offset_vector = [projection[3], projection[7], projection[11]]
            self.setAlignOffset(offset_vector)
            self.setAlignEulerAngles(euler_angles)
            surface_graphics.setCoordinateField(self._scaledCoordinateField)
            line_graphics.setCoordinateField(self._scaledCoordinateField)

    def isDisplayImagePlane(self):
        return self._settings['display-image-plane']

    def setImagePlaneVisible(self, state):
        self._settings['display-image-plane'] = state
        if self._scene is not None:
            self._scene.setVisibilityFlag(state)

    def setSceneviewer(self, sceneviewer):
        fieldmodule = self._region.getFieldmodule()
        fieldmodule.beginChange()
        self._ndc_projection_field = \
            fieldmodule.createFieldSceneviewerProjection(sceneviewer, SCENECOORDINATESYSTEM_LOCAL,
                                                         SCENECOORDINATESYSTEM_NORMALISED_WINDOW_FIT_CENTRE)
        p2 = fieldmodule.createFieldSceneviewerProjection(sceneviewer, SCENECOORDINATESYSTEM_NORMALISED_WINDOW_FIT_CENTRE,
                                                          SCENECOORDINATESYSTEM_LOCAL)
        self._stationary_projection_field = fieldmodule.createFieldMatrixMultiply(4, p2, self._fixed_projection_field)
        self._fixed_coordinate_field = fieldmodule.createFieldProjection(self._scaledCoordinateField,
                                                                         self._stationary_projection_field)
        fieldmodule.endChange()

    def getFrameCount(self):
        return self._frame_count

    def getTimeForFrameIndex(self, index, frames_per_second):
        duration = self._frame_count / frames_per_second
        frame_separation = 1 / self._frame_count
        initial_offset = frame_separation / 2

        return (index * frame_separation + initial_offset) * duration

    def getFrameIndexForTime(self, time, frames_per_second):
        duration = self._frame_count / frames_per_second
        frame_separation = 1 / self._frame_count
        initial_offset = frame_separation / 2
        return int((time / duration - initial_offset) / frame_separation + 0.5)

    def getSettings(self):
        self._settings['alignment'].update(self.getAlignSettings())
        return self._settings

    def setSettings(self, settings):
        self._settings.update(settings)
        self.setImagePlaneVisible(settings['display-image-plane'])
        self.setImagePlaneFixed(settings['image-plane-fixed'])
        if 'alignment' in settings:
            self.setAlignSettings(settings['alignment'])

    def _load_images(self, images):
        fieldmodule = self._region.getFieldmodule()
        self._frame_count = len(images)
        if self._frame_count > 0:
            # Assume all images have the same dimensions.
            width, height = get_image_size.get_image_size(images[0])
            if width != -1 or height != -1:
                cache = fieldmodule.createFieldcache()
                self._modelScaleField.assignReal(cache, [width/1000.0, height/1000.0, 1.0])
            image_field = createVolumeImageField(fieldmodule, images)
            material = createMaterialUsingImageField(self._region, image_field)
            surface = self._scene.findGraphicsByName('plane-surfaces')
            surface.setMaterial(material)

    def _reset(self):
        if self._region:
            self._parent_region.removeChild(self._region)
        self._region = self._parent_region.createChild(self._region_name)
        self._scene = self._region.getScene()
        self._createModel()
        self._createGraphics()
        self.resetAlignment()

    def _createModel(self):
        self._modelCoordinateField = createFiniteElementField(self._region)
        fieldmodule = self._region.getFieldmodule()
        self._modelScaleField = fieldmodule.createFieldConstant([2, 3, 1])
        self._scaledCoordinateField = fieldmodule.createFieldMultiply(self._modelScaleField, self._modelCoordinateField)
        self._fixed_projection_field = fieldmodule.createFieldConstant([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1])
        createSquare2DFiniteElement(fieldmodule, self._modelCoordinateField,
                                    [[-0.5, -0.5, 0.0], [0.5, -0.5, 0.0], [-0.5, 0.5, 0.0], [0.5, 0.5, 0.0]])

    def _createGraphics(self):
        scene = self._scene
        scene.beginChange()
        scene.removeAllGraphics()
        timekeepermodule = scene.getTimekeepermodule()
        self._timekeeper = timekeepermodule.getDefaultTimekeeper()
        fieldmodule = self._region.getFieldmodule()
        xi = fieldmodule.findFieldByName('xi')
        materialmodule = scene.getMaterialmodule()
        lines = scene.createGraphicsLines()
        lines.setExterior(True)
        lines.setName('plane-lines')
        lines.setCoordinateField(self._scaledCoordinateField)
        surfaces = scene.createGraphicsSurfaces()
        surfaces.setName('plane-surfaces')
        surfaces.setCoordinateField(self._scaledCoordinateField)
        temp1 = fieldmodule.createFieldComponent(xi, [1, 2])
        temp2 = fieldmodule.createFieldTimeValue(self._timekeeper)
        texture_field = fieldmodule.createFieldConcatenate([temp1, temp2])
        surfaces.setTextureCoordinateField(texture_field)
        surfaces.setMaterial(materialmodule.findMaterialByName('silver'))
        scene.setVisibilityFlag(self.isDisplayImagePlane())
        scene.endChange()


def tryint(s):
    try:
        return int(s)
    except:
        return s


def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [tryint(c) for c in re.split('([0-9]+)', s)]
