import webbrowser

from PySide6 import QtCore, QtWidgets
from mapclientplugins.scaffoldcreator.ui_configuredialog import Ui_ConfigureDialog

INVALID_STYLE_SHEET = 'background-color: rgba(239, 0, 0, 50)'
DEFAULT_STYLE_SHEET = ''


class ConfigureDialog(QtWidgets.QDialog):
    """
    Configure dialog to present the user with the options to configure this step.
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self._ui = Ui_ConfigureDialog()
        self._ui.setupUi(self)

        self._enable_auto_done = False

        # Keep track of the previous identifier so that we can track changes
        # and know how many occurrences of the current identifier there should
        # be.
        self._previousIdentifier = ''
        # Set a placeholder for a callable that will get set from the step.
        # We will use this method to decide whether the identifier is unique.
        self.identifierOccursCount = None

        self.setWhatsThis(
            '<html>Please read the documentation available \n<a href="https://abi-mapping-tools.readthedocs.io/en/latest/mapclientplugins.scaffoldcreator/docs/index.html">here</a> for further details.</html>')

        self._make_connections()

    def event(self, e):
        if e.type() == QtCore.QEvent.Type.WhatsThisClicked:
            webbrowser.open(e.href())
        return super().event(e)

    def _make_connections(self):
        self._ui.lineEdit0.textChanged.connect(self.validate)

    def accept(self):
        """
        Override the accept method so that we can confirm saving an
        invalid configuration.
        """
        result = QtWidgets.QMessageBox.StandardButton.Yes
        if not self.validate():
            result = QtWidgets.QMessageBox.warning(
                self, 'Invalid Configuration',
                'This configuration is invalid.  Unpredictable behaviour may result if you choose \'Yes\', are you sure you want to save this configuration?)',
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No, QtWidgets.QMessageBox.StandardButton.No
            )

        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            QtWidgets.QDialog.accept(self)

    def validate(self):
        """
        Validate the configuration dialog fields.  For any field that is not valid
        set the style sheet to the INVALID_STYLE_SHEET.  Return the outcome of the
        overall validity of the configuration.
        """
        # Determine if the current identifier is unique throughout the workflow
        # The identifierOccursCount method is part of the interface to the workflow framework.
        value = self.identifierOccursCount(self._ui.lineEdit0.text())
        valid = (value == 0) or (value == 1 and self._previousIdentifier == self._ui.lineEdit0.text())
        if valid:
            self._ui.lineEdit0.setStyleSheet(DEFAULT_STYLE_SHEET)
        else:
            self._ui.lineEdit0.setStyleSheet(INVALID_STYLE_SHEET)

        return valid

    def getConfig(self):
        """
        Get the current value of the configuration from the dialog.  Also
        set the _previousIdentifier value so that we can check uniqueness of the
        identifier over the whole of the workflow.
        """
        self._previousIdentifier = self._ui.lineEdit0.text()
        config = {
            'identifier': self._ui.lineEdit0.text(),
            'AutoDone': self._ui.autoDoneCheckBox.isChecked(),
            'enable-auto-done': self._enable_auto_done,
        }
        return config

    def setConfig(self, config):
        """
        Set the current value of the configuration for the dialog.  Also
        set the _previousIdentifier value so that we can check uniqueness of the
        identifier over the whole of the workflow.
        """
        self._previousIdentifier = config['identifier']
        self._ui.lineEdit0.setText(config['identifier'])
        self._ui.autoDoneCheckBox.setChecked(config['AutoDone'])
        self._enable_auto_done = config.get('enable-auto-done', False)
        tool_tip = 'Available' if self._enable_auto_done else 'This step must be run successfully first to produce an output, before auto done can be enabled.'
        self._ui.autoDoneCheckBox.setEnabled(self._enable_auto_done)
        self._ui.autoDoneCheckBox.setToolTip(tool_tip)
