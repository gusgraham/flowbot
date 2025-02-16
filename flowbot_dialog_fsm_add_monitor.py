from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_fsm_add_monitor_base import Ui_Dialog


class flowbot_dialog_fsm_add_monitor(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_add_monitor, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        self.cbo_monitor_type.currentIndexChanged.connect(self.on_monitor_type_combobox_changed)

        self.on_monitor_type_combobox_changed()

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def on_monitor_type_combobox_changed(self):

        selected_text = self.cbo_monitor_type.currentText()
        if selected_text == 'Rain Gauge':
            items = ['Casella/Technolog', 'Hobo', 'Telemetered']
        elif selected_text in ["Flow Monitor", "Depth Monitor"]:
            items = ["Detec", "Sigma", "MSFM", "ADS", "Ultrasonic D/O", "Pressure D/O"]
        else:
            items = ["Hobo"]

        self.cbo_subtype.clear()  # Clear the current items in the combo box
        self.cbo_subtype.addItems(items)  # Add the new set of items
