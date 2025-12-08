from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QDateTime
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap

from flowbot_management import fsmInstallPictures, fsmProject
from ui_elements.ui_flowbot_dialog_fsm_photographs_base import Ui_Dialog


class flowbot_dialog_fsm_view_photographs(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent, a_project: fsmProject, install_id: int):
        """Constructor."""
        super(flowbot_dialog_fsm_view_photographs, self).__init__(parent)
        self.setupUi(self)
        self.a_project: fsmProject = a_project
        self.install_id = install_id
        self.pictures = [pic for pic in self.a_project.dict_fsm_install_pictures.values() if pic.install_id == self.install_id]

        # Connect buttons
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)
        # self.btnOK.clicked.connect(self.save_pictures)
        # self.btnCancel.clicked.connect(self.reject)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next.clicked.connect(self.next_image)

        self.btn_add.clicked.connect(self.open_file_dialog)

        # # Additional button to add pictures
        # self.add_button = QtWidgets.QPushButton("Add Pictures")
        # self.gridLayout_4.addWidget(self.add_button, 2, 0, 1, 1)
        # self.add_button.clicked.connect(self.open_file_dialog)

        self.current_index = 0
        self.display_current_image()
        self.update_navigation_buttons()

    def open_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.jpeg)")

        if file_dialog.exec_():
            file_names = file_dialog.selectedFiles()
            self.load_pictures(file_names)

    def load_pictures(self, file_names):
        for file_name in file_names:
            pixmap = QPixmap(file_name)
            picture = fsmInstallPictures()
            picture.install_id = self.install_id
            picture.picture_taken_date = QDateTime.currentDateTime().toPyDateTime()
            picture.picture_type = "Other"
            with open(file_name, 'rb') as file:
                picture.picture = file.read()
            picture.picture_comment = ""

            # Generate a unique picture_id and add to the dictionary
            picture.picture_id = max(self.a_project.dict_fsm_install_pictures.keys(), default=0) + 1
            self.a_project.dict_fsm_install_pictures[picture.picture_id] = picture
            self.pictures.append(picture)
        self.current_index = len(self.pictures) - 1
        self.display_current_image()
        self.update_navigation_buttons()


    # def display_current_image(self):
    #     if self.pictures:
    #         picture = self.pictures[self.current_index]
    #         pixmap = QPixmap()
    #         pixmap.loadFromData(picture.picture)
    #         self.img_preview.setPixmap(pixmap.scaled(400, 300, QtCore.Qt.KeepAspectRatio))
    #         self.dateTimeEdit.setDate(QtCore.QDate(picture.picture_taken_date))
    #         self.txt_comment.setText(picture.picture_comment)
    #         self.cbo_photo_type.setCurrentText(picture.picture_type)
    #     else:
    #         self.img_preview.clear()
    #         self.dateTimeEdit.setDate(QtCore.QDate.currentDate())
    #         self.txt_comment.clear()
    #         self.cbo_photo_type.setCurrentIndex(3)

    def display_current_image(self):
        if self.pictures:
            picture = self.pictures[self.current_index]
            pixmap = QPixmap()
            pixmap.loadFromData(picture.picture)
            pixmap = pixmap.scaled(self.img_preview.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.img_preview.setPixmap(pixmap)
            self.img_preview.setAlignment(QtCore.Qt.AlignCenter)
            self.img_preview.setScaledContents(True)
            self.dateTimeEdit.setDateTime(QDateTime(picture.picture_taken_date))
            self.txt_comment.setText(picture.picture_comment)
            self.cbo_photo_type.setCurrentText(picture.picture_type)
        else:
            self.img_preview.clear()
            self.dateTimeEdit.setDateTime(QDateTime.currentDateTime())
            self.txt_comment.clear()
            self.cbo_photo_type.setCurrentIndex(3)

    def prev_image(self):
        if self.pictures:
            self.save_current_metadata()
            self.current_index = (self.current_index - 1) % len(self.pictures)
            self.display_current_image()
            self.update_navigation_buttons()

    def next_image(self):
        if self.pictures:
            self.save_current_metadata()
            self.current_index = (self.current_index + 1) % len(self.pictures)
            self.display_current_image()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        if not self.pictures:
            self.btn_prev.setEnabled(False)
            self.btn_next.setEnabled(False)
        else:
            self.btn_prev.setEnabled(self.current_index > 0)
            self.btn_next.setEnabled(self.current_index < len(self.pictures) - 1)

    def save_current_metadata(self):
        if self.pictures:
            picture = self.pictures[self.current_index]
            picture.picture_taken_date = self.dateTimeEdit.dateTime().toPyDateTime()
            picture.picture_comment = self.txt_comment.text()
            picture.picture_type = self.cbo_photo_type.currentText()

    def save_pictures(self):
        self.save_current_metadata()
        for picture in self.pictures:
            self.a_project.dict_fsm_install_pictures[picture.picture_id] = picture

        # QMessageBox.information(self, "Success", "Pictures added successfully")
        # self.accept()


    def onAccept(self):
        self.save_pictures()
        self.accept()

    def onReject(self):
        self.reject()
