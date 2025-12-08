from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_sumFM_multiplier_base import Ui_Dialog


class flowbot_dialog_sumFMmultiplier(QtWidgets.QDialog, Ui_Dialog):

    summedFM = None
    fmModelData = {}

    def __init__(self, sFM, parent=None):
        """Constructor."""
        super(flowbot_dialog_sumFMmultiplier, self).__init__(parent)
        self.setupUi(self)

        self.summedFM = sFM
        self.updateTableWidget()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def updateTableWidget(self):
        self.createModelDataTable()
        self.setData()

    def setData(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.setRowCount(len(self.fmModelData["FM"]))
        horHeaders = []
        for n, key in enumerate(self.fmModelData.keys()):
            horHeaders.append(key)
            for m, item in enumerate(self.fmModelData[key]):
                newitem = QtWidgets.QTableWidgetItem(str(item))
                self.tableWidget.setItem(m, n, newitem)
        self.tableWidget.setHorizontalHeaderLabels(horHeaders)

    def createModelDataTable(self):

        self.fmModelData = {
            "FM": [],
            "Mult": []
        }

        for fm, multFM in self.summedFM.fmCollection.values():
            self.fmModelData["FM"].append(fm.monitorName)
            self.fmModelData["Mult"].append(multFM)
