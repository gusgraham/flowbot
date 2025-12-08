from typing import Dict
import csv
from flowbot_dialog_fmdataentry import flowbot_dialog_fmdataentry
from flowbot_monitors import flowMonitors, dummyFlowMonitor

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QTableWidgetItem, QDialog)

from ui_elements.ui_flowbot_dialog_modeldata_base import Ui_Dialog


class flowbot_dialog_modeldata(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, FMs, icmData, parent=None):
        """Constructor."""
        super(flowbot_dialog_modeldata, self).__init__(parent)
        self.setupUi(self)

        self.lastOpenDialogPath = ''
        self.notDummyFM: bool = True
        self.oFMs: flowMonitors = flowMonitors()
        self.dFMs: Dict[str, dummyFlowMonitor] = {}
        self.fmModelData = {}

        self.tableWidget.doubleClicked.connect(self.editFMData)
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btnTemplateMappings.clicked.connect(self.exportTemplate)
        self.btnExportMappings.clicked.connect(self.exportMappings)
        self.btnImportMappings.clicked.connect(self.importMappings)

        if isinstance(FMs, flowMonitors):
            self.oFMs = FMs
            self.notDummyFM = True
        else:
            self.dFMs = FMs
            self.notDummyFM = False

        self.importData = icmData
        self.updateTableWidget()

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def exportTemplate(self):
        fileSpec = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save FM data mappings template", self.lastOpenDialogPath, 'CSV Files (*.CSV)')

        if len(fileSpec[0]) > 0:
            with open(fileSpec[0], 'w', newline='') as csvfile:
                fieldnames = ["FM", "Pipe ID", "RG", "System", "Shape", "Width",
                              "Height", "US Invert", "DS Invert", "Length", "Roughness"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    def exportMappings(self):

        fileSpec = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save FM data mapping", self.lastOpenDialogPath, 'CSV Files (*.CSV)')

        if len(fileSpec[0]) > 0:
            with open(fileSpec[0], 'w', newline='') as csvfile:
                fieldnames = ["FM", "Pipe ID", "RG", "System", "Shape", "Width",
                              "Height", "US Invert", "DS Invert", "Length", "Roughness"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i in range(len(self.fmModelData["FM"])):
                    writer.writerow({"FM": self.fmModelData["FM"][i],
                                     "Pipe ID": self.fmModelData["Pipe ID"][i],
                                     "RG": self.fmModelData["RG"][i],
                                     "System": self.fmModelData["System"][i],
                                     "Shape": self.fmModelData["Shape"][i],
                                     "Width": self.fmModelData["Width"][i],
                                     "Height": self.fmModelData["Height"][i],
                                     "US Invert": self.fmModelData["US Invert"][i],
                                     "DS Invert": self.fmModelData["DS Invert"][i],
                                     "Length": self.fmModelData["Length"][i],
                                     "Roughness": self.fmModelData["Roughness"][i]})

    def importMappings(self):

        fileSpec = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open FM data mapping", self.lastOpenDialogPath, 'CSV Files (*.CSV)')

        if len(fileSpec[0]) > 0:
            with open(fileSpec[0][0], newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if self.notDummyFM:
                        if row["FM"] in self.oFMs.dictFlowMonitors:
                            self.oFMs.dictFlowMonitors[row["FM"]
                                                       ].modelDataPipeRef = row["Pipe ID"]
                            self.oFMs.dictFlowMonitors[row["FM"]
                                                       ].modelDataRG = row["RG"]
                            self.oFMs.dictFlowMonitors[row["FM"]
                                                       ].modelDataPipeSystemType = row["System"]
                            self.oFMs.dictFlowMonitors[row["FM"]
                                                       ].modelDataPipeShape = row["Shape"]
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeDia = int(
                                row["Width"])
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeHeight = int(
                                row["Height"])
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeUSInvert = float(
                                row["US Invert"])
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeDSInvert = float(
                                row["DS Invert"])
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeLength = float(
                                row["Length"])
                            self.oFMs.dictFlowMonitors[row["FM"]].modelDataPipeRoughness = float(
                                row["Roughness"])
                            self.oFMs.dictFlowMonitors[row["FM"]
                                                       ].hasModelData = True
                    else:
                        if row["FM"] in self.dFMs:
                            self.dFMs[row["FM"]
                                      ].equivalentFM.modelDataPipeRef = row["Pipe ID"]
                            self.dFMs[row["FM"]
                                      ].equivalentFM.modelDataRG = row["RG"]
                            self.dFMs[row["FM"]
                                      ].equivalentFM.modelDataPipeSystemType = row["System"]
                            self.dFMs[row["FM"]
                                      ].equivalentFM.modelDataPipeShape = row["Shape"]
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeDia = int(
                                row["Width"])
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeHeight = int(
                                row["Height"])
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeUSInvert = float(
                                row["US Invert"])
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeDSInvert = float(
                                row["DS Invert"])
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeLength = float(
                                row["Length"])
                            self.dFMs[row["FM"]].equivalentFM.modelDataPipeRoughness = float(
                                row["Roughness"])
                            self.dFMs[row["FM"]
                                      ].equivalentFM.hasModelData = True

            self.updateTableWidget()

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
                newitem = QTableWidgetItem(str(item))
                self.tableWidget.setItem(m, n, newitem)
        self.tableWidget.setHorizontalHeaderLabels(horHeaders)

    def createModelDataTable(self):

        self.fmModelData = {
            "FM": [],
            "Pipe ID": [],
            "RG": [],
            "System": [],
            "Shape": [],
            "Width": [],
            "Height": [],
            "US Invert": [],
            "DS Invert": [],
            "Length": [],
            "Roughness": []
        }

        if self.notDummyFM:
            for fm in self.oFMs.dictFlowMonitors.values():
                self.fmModelData["FM"].append(fm.monitorName)
                self.fmModelData["Pipe ID"].append(fm.modelDataPipeRef)
                self.fmModelData["RG"].append(fm.modelDataRG)
                self.fmModelData["System"].append(fm.modelDataPipeSystemType)
                self.fmModelData["Shape"].append(fm.modelDataPipeShape)
                self.fmModelData["Width"].append(fm.modelDataPipeDia)
                self.fmModelData["Height"].append(fm.modelDataPipeHeight)
                self.fmModelData["US Invert"].append(fm.modelDataPipeUSInvert)
                self.fmModelData["DS Invert"].append(fm.modelDataPipeDSInvert)
                self.fmModelData["Length"].append(fm.modelDataPipeLength)
                self.fmModelData["Roughness"].append(fm.modelDataPipeRoughness)
        else:
            for fm in self.dFMs.values():
                self.fmModelData["FM"].append(fm.equivalentFM.monitorName)
                # if len(fm.equivalentFM.modelDataPipeRef) == 0:

                # else:
                self.fmModelData["Pipe ID"].append(
                    fm.equivalentFM.modelDataPipeRef)
                self.fmModelData["RG"].append(fm.equivalentFM.modelDataRG)
                self.fmModelData["System"].append(
                    fm.equivalentFM.modelDataPipeSystemType)
                self.fmModelData["Shape"].append(
                    fm.equivalentFM.modelDataPipeShape)
                self.fmModelData["Width"].append(
                    fm.equivalentFM.modelDataPipeDia)
                self.fmModelData["Height"].append(
                    fm.equivalentFM.modelDataPipeHeight)
                self.fmModelData["US Invert"].append(
                    fm.equivalentFM.modelDataPipeUSInvert)
                self.fmModelData["DS Invert"].append(
                    fm.equivalentFM.modelDataPipeDSInvert)
                self.fmModelData["Length"].append(
                    fm.equivalentFM.modelDataPipeLength)
                self.fmModelData["Roughness"].append(
                    fm.equivalentFM.modelDataPipeRoughness)

    def editFMData(self):

        fmID = self.tableWidget.item(self.tableWidget.currentRow(), 0).text()
        if self.notDummyFM:
            fm = self.oFMs.getFlowMonitor(fmID)
        else:
            fm = self.dFMs[fmID].equivalentFM

        editFMDataDialog = flowbot_dialog_fmdataentry(
            fm, self.importData, self)
        editFMDataDialog.setWindowTitle('Edit FM Data Dialog')
        editFMDataDialog.show()
        ret = editFMDataDialog.exec_()
        if ret == QDialog.Accepted:
            fm.modelDataPipeRef = editFMDataDialog.cboPipeID.currentText()
            fm.modelDataRG = editFMDataDialog.edtRG.text()
            fm.modelDataPipeSystemType = editFMDataDialog.edtSystemType.text()
            fm.modelDataPipeShape = editFMDataDialog.edtPipeShape.text()
            fm.modelDataPipeDia = int(editFMDataDialog.edtWidth.text())
            fm.modelDataPipeHeight = int(editFMDataDialog.edtHeight.text())
            fm.modelDataPipeUSInvert = float(
                editFMDataDialog.edtUSInvert.text())
            fm.modelDataPipeDSInvert = float(
                editFMDataDialog.edtDSInvert.text())
            fm.modelDataPipeLength = float(
                editFMDataDialog.edtPipeLength.text())
            fm.modelDataPipeRoughness = float(
                editFMDataDialog.edtRoughness.text())
            fm.hasModelData = True

            self.updateTableWidget()
