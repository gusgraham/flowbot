import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from typing import Optional

from ui_elements.ui_flowbot_dialog_fsm_install_data_base import Ui_Dialog


class flowbot_dialog_fsm_install_rg(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_install_rg, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        original_height = self.height()
        removed_height = self.vlo_fm_data.sizeHint().height()

        self.remove_fm_widgets()

        self.setFixedHeight(original_height - removed_height)
        self.install_sheet: Optional[bytes] = None
        # self.resize_form()

    def remove_fm_widgets(self):
        # Remove all layouts in vlo_fm_data
        while self.vlo_fm_data.count():
            layout_item = self.vlo_fm_data.takeAt(0)
            layout = layout_item.layout()
            if layout is not None:
                # Remove all widgets in the layout
                while layout.count():
                    widget = layout.takeAt(0).widget()
                    if widget is not None:
                        widget.setParent(None)
                # Remove the layout itself
                layout.setParent(None)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def get_install_sheet(self) -> Optional[bytes]:
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
                    self.txt_install_sheet.setText(os.path.basename(pdf_file_path))
