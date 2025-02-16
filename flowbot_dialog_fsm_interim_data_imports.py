from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QFontMetrics
from flowbot_management import fsmInterimReview
from typing import Dict

from ui_elements.ui_flowbot_dialog_fsm_interim_data_imports_base import Ui_Dialog


class flowbot_dialog_fsm_interim_data_imports(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, interim_reviews: Dict[int, fsmInterimReview], parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_interim_data_imports, self).__init__(parent)
        self.setupUi(self)

        # self.table_model_data = {}
        self.interim_reviews = interim_reviews
        self.table_model_data = self.createModelDataTable()
        self.dataReviewComplete = False
        self.updateTableWidget()

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

    def onAccept(self):
        self.updateInterimReviewsFromTable()
        
        self.accept()

    def onReject(self):
        self.reject()

    # def createModelDataTable(self):
    #     return {
    #         "SiteID": [review.site_id for review in self.interim_reviews.values()],
    #         "DataCovered": [review.data_covered for review in self.interim_reviews.values()],
    #         "IgnoreMissing": [review.ignore_missing for review in self.interim_reviews.values()],
    #         "ReasonMissing": [review.reason_missing for review in self.interim_reviews.values()]
    #     }
    def createModelDataTable(self):
        return {
            "IntRevID": [review.interim_review_id for review in self.interim_reviews.values()],
            "Ident": [review.dr_identifier for review in self.interim_reviews.values()],
            "DataCovered": ["Yes" if review.dr_data_covered else "No" for review in self.interim_reviews.values()],
            "IgnoreMissing": [review.dr_ignore_missing for review in self.interim_reviews.values()],
            "ReasonMissing": [review.dr_reason_missing for review in self.interim_reviews.values()]
        }    

    def updateTableWidget(self):
        self.statusTable.setRowCount(0)
        self.statusTable.setRowCount(len(self.table_model_data["Ident"]))
        horHeaders = ["Identifier", "Data Covers Interim", "Ignore Missing Data", "Reason for Missing Data"]
        
        # Iterate through the data, excluding the "IntRevID" key
        for n, key in enumerate(self.table_model_data.keys()):
            if key == "IntRevID":
                continue
            display_col_index = n - 1 if n > list(self.table_model_data.keys()).index("IntRevID") else n
            for m, item in enumerate(self.table_model_data[key]):
                if key == "IgnoreMissing":
                    check_box = QtWidgets.QCheckBox()
                    check_box.setChecked(item)
                    check_box.stateChanged.connect(self.handle_ignore_missing_data_checkbox)
                    self.statusTable.setCellWidget(m, display_col_index, check_box)
                else:
                    if key == "Ident" or key == "DataCovered":
                        newitem = QtWidgets.QTableWidgetItem(str(item))
                        newitem.setFlags(newitem.flags() & ~QtCore.Qt.ItemIsEditable)
                    else:
                        newitem = QtWidgets.QTableWidgetItem(str(item))
                    self.statusTable.setItem(m, display_col_index, newitem)

        for row in range(len(self.table_model_data["Ident"])):
            reason_missing_item = self.statusTable.item(row, 3)
            if self.statusTable.item(row, 1).text() == "Yes":
                widget = self.statusTable.cellWidget(row, 2)
                if widget:
                    widget.setDisabled(True)
                    widget.setStyleSheet("background-color: rgb(227, 227, 227);")
                    if widget.isChecked():
                        reason_missing_item.setFlags(reason_missing_item.flags() | QtCore.Qt.ItemIsEditable)
                    else:
                        reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)
            else:
                widget = self.statusTable.cellWidget(row, 2)
                if widget:
                    widget.setDisabled(False)
                reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)

        # Set the resize mode for the first three columns to be fixed
        for i in range(3):
            self.statusTable.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
        self.statusTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        # Set widths for columns
        self.statusTable.setColumnWidth(0, 90)
        self.statusTable.setColumnWidth(1, 50)
        self.statusTable.setColumnWidth(2, 50)

        self.statusTable.setHorizontalHeaderLabels(horHeaders)
        self.statusTable.horizontalHeader().setDefaultAlignment(Qt.AlignCenter | Qt.Alignment(Qt.TextWordWrap))
        # Resize columns to accommodate wrapped text
        font_metrics = QFontMetrics(self.statusTable.horizontalHeader().font())
        height = self.statusTable.horizontalHeader().height()
        for i in range(self.statusTable.horizontalHeader().count()):
            width = self.statusTable.horizontalHeader().sectionSize(i)
            text = self.statusTable.horizontalHeaderItem(i).text()
            wrapped_text = font_metrics.elidedText(text, Qt.ElideNone, width)
            height = max(height, font_metrics.boundingRect(QRect(), Qt.TextWordWrap, wrapped_text).height())
        self.statusTable.horizontalHeader().setFixedHeight(height)
        self.statusTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for row in range(len(self.table_model_data["Ident"])):
            for column in range(4):
                if column != 2:
                    item = self.statusTable.item(row, column)
                    if item is not None and not item.flags() & QtCore.Qt.ItemIsEditable:
                        self.statusTable.item(row, column).setBackground(QtGui.QColor(227, 227, 227))  # Grey background
                else:
                    widget = self.statusTable.cellWidget(row, column)
                    if widget:
                        reason_missing_item = self.statusTable.item(row, 3)
                        data_covered = self.table_model_data["DataCovered"][row]
                        ignore_missing = self.table_model_data["IgnoreMissing"][row]
                        if data_covered == "No" and ignore_missing:
                            reason_missing_item.setFlags(reason_missing_item.flags() | QtCore.Qt.ItemIsEditable)
                            reason_missing_item.setBackground(QtGui.QColor(255, 255, 255))
                        else:
                            reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)
                            reason_missing_item.setBackground(QtGui.QColor(227, 227, 227))


    # def updateTableWidget(self):
    #     self.statusTable.setRowCount(0)
    #     self.statusTable.setRowCount(len(self.table_model_data["Ident"]))
    #     horHeaders = ["Identifier", "Data Covers Interim", "Ignore Missing Data", "Reason for Missing Data"]
    #     for n, key in enumerate(self.table_model_data.keys()):
    #         for m, item in enumerate(self.table_model_data[key]):
    #             if key == "IgnoreMissing":
    #                 check_box = QtWidgets.QCheckBox()
    #                 check_box.setChecked(item)
    #                 check_box.stateChanged.connect(self.handle_ignore_missing_data_checkbox)
    #                 # check_box.setStyleSheet("margin-left:50%; margin-right:50%;")
    #                 self.statusTable.setCellWidget(m, n, check_box)
    #             else:
    #                 if key == "Ident" or key == "DataCovered":
    #                     newitem = QtWidgets.QTableWidgetItem(str(item))
    #                     newitem.setFlags(newitem.flags() & ~QtCore.Qt.ItemIsEditable)
    #                 else:
    #                     newitem = QtWidgets.QTableWidgetItem(str(item))
    #                 self.statusTable.setItem(m, n, newitem)

    #     for row in range(len(self.table_model_data["Ident"])):
    #         reason_missing_item = self.statusTable.item(row, 3)
    #         if self.statusTable.item(row, 1).text() == "Yes":
    #             widget = self.statusTable.cellWidget(row, 2)
    #             if widget:
    #                 widget.setDisabled(True)
    #                 widget.setStyleSheet("background-color: rgb(227, 227, 227);")
    #                 if widget.isChecked():
    #                     reason_missing_item.setFlags(reason_missing_item.flags() | QtCore.Qt.ItemIsEditable)
    #                 else:
    #                     reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)
    #         else:
    #             widget = self.statusTable.cellWidget(row, 2)
    #             if widget:
    #                 widget.setDisabled(False)
    #             reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)

    #     # Set the resize mode for the first three columns to be fixed
    #     for i in range(3):
    #         self.statusTable.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Fixed)
    #     self.statusTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    #     # Set widths for columns
    #     self.statusTable.setColumnWidth(0, 90)
    #     self.statusTable.setColumnWidth(1, 50)
    #     self.statusTable.setColumnWidth(2, 50)

    #     self.statusTable.setHorizontalHeaderLabels(horHeaders)
    #     self.statusTable.horizontalHeader().setDefaultAlignment(Qt.AlignCenter | Qt.Alignment(Qt.TextWordWrap))
    #     # Resize columns to accommodate wrapped text
    #     font_metrics = QFontMetrics(self.statusTable.horizontalHeader().font())
    #     height = self.statusTable.horizontalHeader().height()
    #     for i in range(self.statusTable.horizontalHeader().count()):
    #         width = self.statusTable.horizontalHeader().sectionSize(i)
    #         text = self.statusTable.horizontalHeaderItem(i).text()
    #         wrapped_text = font_metrics.elidedText(text, Qt.ElideNone, width)
    #         height = max(height, font_metrics.boundingRect(QRect(), Qt.TextWordWrap, wrapped_text).height())
    #     self.statusTable.horizontalHeader().setFixedHeight(height)
    #     self.statusTable.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    #     for row in range(len(self.table_model_data["Ident"])):
    #         for column in range(4):
    #             if column != 2:
    #                 item = self.statusTable.item(row, column)
    #                 if item is not None and not item.flags() & QtCore.Qt.ItemIsEditable:
    #                     self.statusTable.item(row, column).setBackground(QtGui.QColor(227, 227, 227))  # Grey background
    #             else:
    #                 widget = self.statusTable.cellWidget(row, column)
    #                 if widget:
    #                     reason_missing_item = self.statusTable.item(row, 3)
    #                     data_covered = self.table_model_data["DataCovered"][row]
    #                     ignore_missing = self.table_model_data["IgnoreMissing"][row]
    #                     if data_covered == "No" and ignore_missing:
    #                         reason_missing_item.setFlags(reason_missing_item.flags() | QtCore.Qt.ItemIsEditable)
    #                         reason_missing_item.setBackground(QtGui.QColor(255, 255, 255))
    #                     else:
    #                         reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)
    #                         reason_missing_item.setBackground(QtGui.QColor(227, 227, 227))

    def handle_ignore_missing_data_checkbox(self, state):
        check_box = self.sender()
        row = self.statusTable.indexAt(check_box.pos()).row()
        reason_missing_item = self.statusTable.item(row, 3)

        # Assuming self.table_model_data["DataCovered"] and self.table_model_data["IgnoreMissing"] contains the respective data
        data_covered = self.table_model_data["DataCovered"][row]
        ignore_missing = check_box.isChecked()  # Get the value from the checkbox

        if data_covered == "No" and ignore_missing:
            reason_missing_item.setFlags(reason_missing_item.flags() | QtCore.Qt.ItemIsEditable)
            reason_missing_item.setBackground(QtGui.QColor(255, 255, 255))
        else:
            reason_missing_item.setFlags(reason_missing_item.flags() & ~QtCore.Qt.ItemIsEditable)
            reason_missing_item.setBackground(QtGui.QColor(227, 227, 227))

    # def createModelDataTable(self):

    #     self.table_model_data = {
    #         "Ident": [],
    #         "DataCovered": [],
    #         "IgnoreMissing": [],
    #         "ReasonMissing": []
    #     }

    #     for a_int_rev in self.interim_reviews.values():
    #         self.table_model_data["Ident"].append(a_int_rev.site_id)
    #         self.table_model_data["DataCovered"].append(a_int_rev.data_covered)
    #         self.table_model_data["IgnoreMissing"].append(a_int_rev.ignore_missing)
    #         self.table_model_data["ReasonMissing"].append(a_int_rev.reason_missing)


    def updateInterimReviewsFromTable(self):
        
        self.dataReviewComplete = True
        for row in range(len(self.table_model_data['IntRevID'])):
            int_rev_id = self.table_model_data['IntRevID'][row]
            # ident = self.statusTable.item(row, 0).text()
            data_covered = self.statusTable.item(row, 1).text() == "Yes"
            ignore_missing_widget = self.statusTable.cellWidget(row, 2)
            ignore_missing = ignore_missing_widget.isChecked() if ignore_missing_widget else False
            reason_missing = self.statusTable.item(row, 3).text()
            
            for review in self.interim_reviews.values():
                if review.interim_review_id == int_rev_id:
                    review.dr_data_covered = data_covered
                    review.dr_ignore_missing = ignore_missing
                    review.dr_reason_missing = reason_missing
                    break
            
            if not data_covered:
                if not (ignore_missing and len(reason_missing) > 0):
                    self.dataReviewComplete = False
                

    # def updateInterimReviewsFromTable(self):
    #     for row in range(len(self.table_model_data["Ident"])):
    #         site_id = self.statusTable.item(row, 0).text()
    #         data_covered = self.statusTable.item(row, 1).text() == "Yes"
    #         ignore_missing_widget = self.statusTable.cellWidget(row, 2)
    #         ignore_missing = ignore_missing_widget.isChecked() if ignore_missing_widget else False
    #         reason_missing = self.statusTable.item(row, 3).text()

    #         for review in self.interim_reviews.values():
    #             if review.site_id == site_id:
    #                 review.data_covered = data_covered
    #                 review.ignore_missing = ignore_missing
    #                 review.reason_missing = reason_missing
    #                 break
