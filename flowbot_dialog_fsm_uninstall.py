import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from typing import Optional

from ui_elements.ui_flowbot_dialog_fsm_uninstall_base import Ui_Dialog


class flowbot_dialog_fsm_uninstall(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_uninstall, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        self.btn_get_inspection_sheet.clicked.connect(self.get_inspection_sheet)

        self.inspection_sheet: Optional[bytes] = None

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()
    
    def get_inspection_sheet(self) -> Optional[bytes]:
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Open PDF File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("PDF Files (*.pdf)")

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                pdf_file_path = selected_files[0]
                with open(pdf_file_path, 'rb') as file:
                    self.install_sheet = file.read()
                    self.txt_inspection_sheet.setText(os.path.basename(pdf_file_path))
                    self.pdf_view_widget.loadPdf(pdf_file_path)
                    
