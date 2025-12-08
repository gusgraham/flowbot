from PyQt5 import QtWidgets, QtGui

from ui_elements.ui_flowbot_dialog_fmdataentry_base import Ui_Dialog


class flowbot_dialog_fmdataentry(QtWidgets.QDialog, Ui_Dialog):

    isInitialised = False
    editFM = None
    importedICMData = None

    def __init__(self, fm, icmData, parent=None):
        """Constructor."""
        super(flowbot_dialog_fmdataentry, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        self.cboPipeID.lineEdit().editingFinished.connect(self.pipeIDChanged)

        self.edtUSInvert.setValidator(QtGui.QDoubleValidator())
        self.edtDSInvert.setValidator(QtGui.QDoubleValidator())
        self.edtPipeLength.setValidator(QtGui.QDoubleValidator())
        self.edtWidth.setValidator(QtGui.QDoubleValidator())
        self.edtHeight.setValidator(QtGui.QDoubleValidator())
        self.edtRoughness.setValidator(QtGui.QDoubleValidator())

        self.editFM = fm
        self.importedICMData = icmData

        # if len(self.importedICMData) > 0 and len(self.importedICMData["Pipe ID"]) > 0:
        if self.importedICMData is not None:
            lstSorted = self.importedICMData["Pipe ID"]
            lstSorted.sort()
            self.cboPipeID.addItems(lstSorted)
            self.cboPipeID.insertSeparator(0)
        self.cboPipeID.insertItem(0, "Manual Entry")

        self.edtFMID.setText(fm.monitorName)
        self.cboPipeID.setCurrentText("Manual Entry")

        if fm.hasModelData:
            # if self.cboPipeID.findTex(str(fm.modelDataPipeRef)) == -1:
            # self.cboPipeID.addItems(str(fm.modelDataPipeRef))
            self.cboPipeID.setCurrentText(str(fm.modelDataPipeRef))
            self.edtRG.setText(str(fm.modelDataRG))
            self.edtPipeShape.setText(str(fm.modelDataPipeShape))
            self.edtWidth.setText(str(fm.modelDataPipeDia))
            self.edtHeight.setText(str(fm.modelDataPipeHeight))
            self.edtRoughness.setText(str(fm.modelDataPipeRoughness))
            self.edtUSInvert.setText(str(fm.modelDataPipeUSInvert))
            self.edtDSInvert.setText(str(fm.modelDataPipeDSInvert))
            self.edtPipeLength.setText(str(fm.modelDataPipeLength))
            self.edtSystemType.setText(str(fm.modelDataPipeSystemType))

        self.enableButtons()

        self.isInitialised = True

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def enableButtons(self):

        self.edtRG.setEnabled(False)
        self.edtPipeShape.setEnabled(False)
        self.edtWidth.setEnabled(False)
        self.edtHeight.setEnabled(False)
        self.edtRoughness.setEnabled(False)
        self.edtUSInvert.setEnabled(False)
        self.edtDSInvert.setEnabled(False)
        self.edtPipeLength.setEnabled(False)
        self.edtSystemType.setEnabled(False)

        if self.cboPipeID.currentText() == "Manual Entry":
            self.edtRG.setEnabled(True)
            self.edtPipeShape.setEnabled(True)
            self.edtWidth.setEnabled(True)
            self.edtHeight.setEnabled(True)
            self.edtRoughness.setEnabled(True)
            self.edtUSInvert.setEnabled(True)
            self.edtDSInvert.setEnabled(True)
            self.edtPipeLength.setEnabled(True)
            self.edtSystemType.setEnabled(True)

    def pipeIDChanged(self):

        if self.isInitialised:
            if not self.cboPipeID.currentText() == "Manual Entry":
                if self.importedICMData is not None:
                    index = self.importedICMData["Pipe ID"].index(
                        self.cboPipeID.currentText())
                    self.edtRG.setText("")
                    self.edtPipeLength.setText(
                        self.importedICMData["Length"][index])
                    self.edtWidth.setText(self.importedICMData["Width"][index])
                    self.edtRoughness.setText(
                        self.importedICMData["Roughness"][index])
                    self.edtUSInvert.setText(
                        self.importedICMData["US Invert"][index])
                    self.edtDSInvert.setText(
                        self.importedICMData["DS Invert"][index])
                    self.edtPipeShape.setText(
                        self.importedICMData["Shape"][index])
                    self.edtHeight.setText(
                        self.importedICMData["Height"][index])
                    self.edtSystemType.setText(
                        self.importedICMData["System"][index])

            self.enableButtons()
