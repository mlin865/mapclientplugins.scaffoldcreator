
import json

from opencmiss.utils.maths import vectorops


class MeshAlignmentModel(object):

    def __init__(self, name):
        self._name = name
        self._clear()

    def isStateAlign(self):
        return self._isStateAlign

    def setStateAlign(self):
        self._isStateAlign = True

    def scaleModel(self, factor):
        self._alignSettings['scale'] *= factor
        self._applyAlignSettings()

    def rotateModel(self, axis, angle):
        quat = vectorops.axisAngleToQuaternion(axis, angle)
        mat1 = vectorops.rotmx(quat)
        mat2 = vectorops.eulerToRotationMatrix3(self._alignSettings['euler_angles'])
        newmat = vectorops.mxmult(mat1, mat2)
        self._alignSettings['euler_angles'] = vectorops.rotationMatrix3ToEuler(newmat)
        self._applyAlignSettings()

    def offsetModel(self, relativeOffset):
        self._alignSettings['offset'] = vectorops.add(self._alignSettings['offset'], relativeOffset)
        self._applyAlignSettings()

    def resetModel(self, region):
        self._clear()
        self._initialise(region)
        self._applyAlignSettings()

    def _initialise(self, region):
        self._region = region.createChild(self._name)

    def _clear(self):
        """
        Ensure scene for this region is not in use before calling!
        """
        self._scene = None
        self._mesh = None
        self._modelCoordinateField = None
        self._modelReferenceCoordinateField = None
        self._modelOffsetField = None # 3 vector
        self._modelRotationScaleField = None # 3x3 matrix
        self._modelTransformedCoordinateField = None
        self._alignSettingsChangeCallback = None
        self._resetAlignSettings()
        self._isStateAlign = True

    def _resetAlignSettings(self):
        self._alignSettings = dict(euler_angles=[0.0, 0.0, 0.0], scale=1.0, offset=[0.0, 0.0, 0.0])

    def setAlignSettingsChangeCallback(self, alignSettingsChangeCallback):
        self._alignSettingsChangeCallback = alignSettingsChangeCallback

    def getAlignEulerAngles(self):
        return self._alignSettings['euler_angles']

    def setAlignEulerAngles(self, eulerAngles):
        if len(eulerAngles) == 3:
            self._alignSettings['euler_angles'] = eulerAngles
            self._applyAlignSettings()

    def getAlignOffset(self):
        return self._alignSettings['offset']

    def setAlignOffset(self, offset):
        if len(offset) == 3:
            self._alignSettings['offset'] = offset
            self._applyAlignSettings()

    def getAlignScale(self):
        return self._alignSettings['scale']

    def setAlignScale(self, scale):
        self._alignSettings['scale'] = scale
        self._applyAlignSettings()

    def _applyAlignSettings(self):
        rot = vectorops.eulerToRotationMatrix3(self._alignSettings['euler_angles'])
        scale = self._alignSettings['scale']
        xScale = scale
        # if self.isAlignMirror():
        #     xScale = -scale
        rotationScale = [
            rot[0][0]*xScale, rot[0][1]*xScale, rot[0][2]*xScale,
            rot[1][0]*scale,  rot[1][1]*scale,  rot[1][2]*scale,
            rot[2][0]*scale,  rot[2][1]*scale,  rot[2][2]*scale]
        fm = self._region.getFieldmodule()
        fm.beginChange()
        if self._modelTransformedCoordinateField is None:
            self._modelRotationScaleField = fm.createFieldConstant(rotationScale)
            # following works in 3-D only
            temp1 = fm.createFieldMatrixMultiply(3, self._modelRotationScaleField, self._modelCoordinateField)
            self._modelOffsetField = fm.createFieldConstant(self._alignSettings['offset'])
            self._modelTransformedCoordinateField = fm.createFieldAdd(temp1, self._modelOffsetField)
        else:
            cache = fm.createFieldcache()
            self._modelRotationScaleField.assignReal(cache, rotationScale)
            self._modelOffsetField.assignReal(cache, self._alignSettings['offset'])
        fm.endChange()
        if not self._modelTransformedCoordinateField.isValid():
            print("Can't create transformed model coordinate field. Is problem 2-D?")
        if self._alignSettingsChangeCallback is not None:
            self._alignSettingsChangeCallback()

    def loadAlignSettings(self):
        with open(self._location + '-align-settings.json', 'r') as f:
            self._alignSettings.update(json.loads(f.read()))
        self._applyAlignSettings()

    def saveAlignSettings(self):
        with open(self._location + '-align-settings.json', 'w') as f:
            f.write(json.dumps(self._alignSettings, default=lambda o: o.__dict__, sort_keys=True, indent=4))

    def resetAlignment(self):
        self._resetAlignSettings()
        self._applyAlignSettings()
