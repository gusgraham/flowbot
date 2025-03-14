from PyQt5 import QtWidgets
from flowbot_management import fsmMonitor

from ui_elements.ui_flowbot_dialog_fsm_add_monitor_base import Ui_Dialog


class flowbot_dialog_fsm_add_monitor(QtWidgets.QDialog, Ui_Dialog):

    def __init__(self, mon: fsmMonitor = None, editing = True, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_add_monitor, self).__init__(parent)
        self.setupUi(self)

        self.mon: fsmMonitor = mon
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        if editing:
            self.txt_asset_id.setText(self.mon.monitor_asset_id)
            self.txt_asset_id.setEnabled(False)
            if self.mon.monitor_type in ["Flow Monitor", "Depth Monitor", 'Pump Logger']:
                self.cbo_monitor_type.clear()  # Clear the current items in the combo box
                self.cbo_monitor_type.addItems(["Flow Monitor", "Depth Monitor", 'Pump Logger'])                
            else:
                self.cbo_monitor_type.clear()  # Clear the current items in the combo box
                self.cbo_monitor_type.addItems(["Rain Gauge"])                

            self.cbo_monitor_type.setCurrentText(self.mon.monitor_type)
            self.cbo_monitor_type.setCurrentText(self.mon.monitor_type)
            self.cbo_subtype.setCurrentText(self.mon.monitor_sub_type)
            self.txt_pmac_id.setText(self.mon.pmac_id)

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
