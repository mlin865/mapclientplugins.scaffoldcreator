import os
import json

from opencmiss.zinc.context import Context
from opencmiss.zinc.material import Material

from mapclientplugins.meshgeneratorstep.model.meshgeneratormodel import MeshGeneratorModel
from mapclientplugins.meshgeneratorstep.model.meshplanemodel import MeshPlaneModel


class MasterModel(object):

    def __init__(self, location, identifier):
        self._location = location
        self._identifier = identifier
        self._filenameStem = os.path.join(self._location, self._identifier)
        self._context = Context("MeshGenerator")
        self._initialise()
        self._region = self._context.createRegion()
        self._generator_model = MeshGeneratorModel(self._region, self._materialmodule)
        self._plane_model = MeshPlaneModel(self._region)
        self._loadSettings()

    def _initialise(self):
        self._filenameStem = os.path.join(self._location, self._identifier)
        tess = self._context.getTessellationmodule().getDefaultTessellation()
        tess.setRefinementFactors(12)
        # set up standard materials and glyphs so we can use them elsewhere
        self._materialmodule = self._context.getMaterialmodule()
        self._materialmodule.defineStandardMaterials()
        solid_blue = self._materialmodule.createMaterial()
        solid_blue.setName('solid_blue')
        solid_blue.setManaged(True)
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [ 0.0, 0.2, 0.6 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [ 0.0, 0.7, 1.0 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [ 0.0, 0.0, 0.0 ])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [ 0.1, 0.1, 0.1 ])
        solid_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS , 0.2)
        trans_blue = self._materialmodule.createMaterial()
        trans_blue.setName('trans_blue')
        trans_blue.setManaged(True)
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [ 0.0, 0.2, 0.6 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [ 0.0, 0.7, 1.0 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [ 0.0, 0.0, 0.0 ])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [ 0.1, 0.1, 0.1 ])
        trans_blue.setAttributeReal(Material.ATTRIBUTE_ALPHA , 0.3)
        trans_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS , 0.2)
        glyphmodule = self._context.getGlyphmodule()
        glyphmodule.defineStandardGlyphs()

    def getIdentifier(self):
        return self._identifier

    def getOutputModelFilename(self):
        return self._filenameStem + '.ex2'

    def getGeneratorModel(self):
        return self._generator_model

    def getPlaneModel(self):
        return self._plane_model

    def getScene(self):
        return self._region.getScene()

    def getContext(self):
        return self._context

    def registerSceneChangeCallback(self, sceneChangeCallback):
        self._generator_model.registerSceneChangeCallback(sceneChangeCallback)

    def done(self):
        self._saveSettings()
        self._generator_model.writeModel(self.getOutputModelFilename())

    def _getSettings(self):
        generator_settings = self._generator_model.getSettings()
        return {'generator_settings': generator_settings}

    def _loadSettings(self):
        try:
            settings = {}
            with open(self._filenameStem + '-settings.json', 'r') as f:
                settings.update(json.loads(f.read()))
            if not 'generator_settings' in settings:
                # migrate from old settings before named generator_settings
                settings = {'generator_settings': settings}
        except:
            # no settings saved yet, following gets defaults
            settings = self._getSettings()
        self._generator_model.setSettings(settings['generator_settings'])

    def _saveSettings(self):
        settings = self._getSettings()
        with open(self._filenameStem + '-settings.json', 'w') as f:
            f.write(json.dumps(settings, default=lambda o: o.__dict__, sort_keys=True, indent=4))

