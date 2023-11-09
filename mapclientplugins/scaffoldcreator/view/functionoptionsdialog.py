from PySide6 import QtCore, QtWidgets
from functools import partial

class FunctionOptionsDialog(QtWidgets.QDialog):
    '''
    Modal dialog allowing a dict of options to be edited, then OK/Cancel to be returned.
    '''

    def __init__(self, functionName, functionOptions, parent):
        '''
        :param functionOptions: dict of name -> value.
        '''
        super(FunctionOptionsDialog, self).__init__(parent)
        self._functionName = functionName
        self._functionOptions = functionOptions
        self._setup()

    def _setup(self):
        self.setWindowTitle(self._functionName)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self._dialogLayout = QtWidgets.QVBoxLayout(self)
        self._dialogLayout.setObjectName("dialogLayout")
        self.setModal(True)
        self._addOptions()
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)  # hide window context help (?)
        self.resize(300, 150)
        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._buttonBox.sizePolicy().hasHeightForWidth())
        self._buttonBox.setSizePolicy(sizePolicy)
        self._buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self._buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self._buttonBox.setObjectName("buttonBox")
        self._dialogLayout.addWidget(self._buttonBox)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)

    def _optionCheckBoxClicked(self, checkBox):
        self._functionOptions[checkBox.objectName()] = checkBox.isChecked()

    def _optionRadioButtonClicked(self, radioButton):
        key = radioButton.objectName()
        option = self._functionOptions[key]
        subKey = radioButton.text()
        for tmpKey in option:
            option[tmpKey] = (tmpKey == subKey)

    def _optionLineEditChanged(self, lineEdit):
        key = lineEdit.objectName()
        oldValue = self._functionOptions[key]
        text = lineEdit.text()
        try:
            if type(oldValue) is int:
                newValue = int(text)
            elif type(oldValue) is float:
                newValue = float(text)
            elif type(oldValue) is str:
                newValue = str(text)
            else:
                assert False, 'Unimplemented type in function option dialog'
        except:
            print('FunctionOptionDialog: Invalid value')
            return
        self._functionOptions[key] = newValue

    def _addOptions(self):
        for key in self._functionOptions:
            value = self._functionOptions[key]
            if type(value) is bool:
                checkBox = QtWidgets.QCheckBox(self)
                checkBox.setObjectName(key)
                checkBox.setText(key)
                checkBox.setChecked(value)
                callback = partial(self._optionCheckBoxClicked, checkBox)
                checkBox.clicked.connect(callback)
                self._dialogLayout.addWidget(checkBox)
            else:
                label = QtWidgets.QLabel(self)
                label.setObjectName(key)
                label.setText(key)
                self._dialogLayout.addWidget(label)
                if type(value) is dict:
                    # radio buttons
                    for subKey, subValue in value.items():
                        radioButton = QtWidgets.QRadioButton(self)
                        radioButton.setObjectName(key)
                        radioButton.setText(subKey)
                        radioButton.setChecked(subValue)
                        callback = partial(self._optionRadioButtonClicked, radioButton)
                        radioButton.clicked.connect(callback)
                        self._dialogLayout.addWidget(radioButton)
                else:
                    lineEdit = QtWidgets.QLineEdit(self)
                    lineEdit.setObjectName(key)
                    lineEdit.setText(str(value))
                    callback = partial(self._optionLineEditChanged, lineEdit)
                    lineEdit.editingFinished.connect(callback)
                    self._dialogLayout.addWidget(lineEdit)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self._dialogLayout.addItem(spacerItem)
