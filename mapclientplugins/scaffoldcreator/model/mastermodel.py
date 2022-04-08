import os
import json

from PySide2 import QtCore

from opencmiss.zinc.context import Context
from opencmiss.zinc.material import Material

from mapclientplugins.scaffoldcreator.model.scaffoldcreatormodel import ScaffoldCreatorModel
from mapclientplugins.scaffoldcreator.model.meshannotationmodel import MeshAnnotationModel
from mapclientplugins.scaffoldcreator.model.segmentationdatamodel import SegmentationDataModel
from scaffoldmaker.scaffolds import Scaffolds_decodeJSON, Scaffolds_JSONEncoder


class MasterModel(object):

    def __init__(self, location, identifier):
        self._location = location
        self._identifier = identifier
        self._filenameStem = os.path.join(self._location, self._identifier)
        self._context = Context("ScaffoldCreator")
        self._timekeeper = self._context.getTimekeepermodule().getDefaultTimekeeper()
        self._timer = QtCore.QTimer()
        self._current_time = 0.0
        self._timeValueUpdate = None
        self._frameIndexUpdate = None
        self._initialise()
        self._region = self._context.createRegion()
        self._creator_model = ScaffoldCreatorModel(self._context, self._region, self._materialmodule)
        self._segmentation_data_model = SegmentationDataModel(self._region, self._materialmodule)
        self._annotation_model = MeshAnnotationModel()

        self._settings = {
            'segmentation_data_settings': self._segmentation_data_model.getSettings()
        }
        self._makeConnections()
        # self._loadSettings()

    def printLog(self):
        logger = self._context.getLogger()
        for index in range(logger.getNumberOfMessages()):
            print(logger.getMessageTextAtIndex(index))

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
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [0.0, 0.2, 0.6])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [0.0, 0.7, 1.0])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [0.0, 0.0, 0.0])
        solid_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [0.1, 0.1, 0.1])
        solid_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS, 0.2)
        trans_blue = self._materialmodule.createMaterial()
        trans_blue.setName('trans_blue')
        trans_blue.setManaged(True)
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_AMBIENT, [0.0, 0.2, 0.6])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_DIFFUSE, [0.0, 0.7, 1.0])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_EMISSION, [0.0, 0.0, 0.0])
        trans_blue.setAttributeReal3(Material.ATTRIBUTE_SPECULAR, [0.1, 0.1, 0.1])
        trans_blue.setAttributeReal(Material.ATTRIBUTE_ALPHA, 0.3)
        trans_blue.setAttributeReal(Material.ATTRIBUTE_SHININESS, 0.2)
        glyphmodule = self._context.getGlyphmodule()
        glyphmodule.defineStandardGlyphs()

    def _makeConnections(self):
        pass

    def getIdentifier(self):
        return self._identifier

    def getOutputModelFilename(self):
        return self._filenameStem + '.exf'

    def getOutputAnnotationsFilename(self):
        return self._creator_model.getAnnotationsFilename(self._filenameStem)

    def getCreatorModel(self):
        return self._creator_model

    def getMeshAnnotationModel(self):
        return self._annotation_model

    def getSegmentationDataModel(self):
        return self._segmentation_data_model

    def getScene(self):
        return self._region.getScene()

    def getContext(self):
        return self._context

    def registerSceneChangeCallback(self, sceneChangeCallback):
        self._creator_model.registerSceneChangeCallback(sceneChangeCallback)

    def done(self):
        self._saveSettings()
        self._creator_model.done()
        self._creator_model.writeModel(self.getOutputModelFilename())
        self._creator_model.writeAnnotations(self._filenameStem)
        self._creator_model.exportToVtk(self._filenameStem)

    def _getSettings(self):
        """
        Ensures master model settings includes current settings for sub models.
        :return: Master setting dict.
        """
        settings = self._settings
        settings['scaffold_settings'] = self._creator_model.getSettings()
        settings['segmentation_data_settings'] = self._segmentation_data_model.getSettings()
        return settings

    def loadSettings(self):
        try:
            settings = self._settings
            with open(self._filenameStem + '-settings.json', 'r') as f:
                savedSettings = json.loads(f.read(), object_hook=Scaffolds_decodeJSON)
                settings.update(savedSettings)
            # migrate from generator_settings in version 0.3.2
            if 'generator_settings' in settings:
                settings = {
                    'scaffold_settings': settings['generator_settings'],
                    'segmentation_data_settings': settings['segmentation_data_settings']
                }
            if 'scaffold_settings' not in settings:
                # migrate from version 0.2.0 settings
                settings = {'scaffold_settings': settings, 'segmentation_data_settings': {}}
        except:
            # no settings saved yet, following gets defaults
            settings = self._getSettings()
        self._creator_model.setSettings(settings['scaffold_settings'])
        self._segmentation_data_model.setSettings(settings['segmentation_data_settings'])
        self._annotation_model.setScaffoldTypeByName(self._creator_model.getEditScaffoldTypeName())
        self._getSettings()

    def _saveSettings(self):
        self._creator_model.updateSettingsBeforeWrite()
        settings = self._getSettings()
        with open(self._filenameStem + '-settings.json', 'w') as f:
            f.write(json.dumps(settings, cls=Scaffolds_JSONEncoder, sort_keys=True, indent=4))

    def setSegmentationDataFile(self, data_filename):
        self._segmentation_data_model.setDataFilename(data_filename)
