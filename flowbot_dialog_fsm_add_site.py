from PyQt5 import QtWidgets

from ui_elements.ui_flowbot_dialog_fsm_add_site_base import Ui_Dialog


class flowbot_dialog_fsm_add_site(QtWidgets.QDialog, Ui_Dialog):

    site_type_settings = {
        "Network Asset": {
            "label_mh_ref": True,
            "txt_mh_ref": True,
            "label_easting": False,
            "label_northing": False,
            "txt_easting": False,
            "txt_northing": False,
        },
        "Location": {
            "label_mh_ref": False,
            "txt_mh_ref": False,
            "label_easting": True,
            "label_northing": True,
            "txt_easting": True,
            "txt_northing": True
        }        
        # "Flow Monitor": {
        #     "label_mh_ref": True,
        #     "txt_mh_ref": True,
        #     "label_easting": False,
        #     "label_northing": False,
        #     "txt_easting": False,
        #     "txt_northing": False,
        # },
        # "Depth Monitor": {
        #     "label_mh_ref": True,
        #     "txt_mh_ref": True,
        #     "label_easting": False,
        #     "label_northing": False,
        #     "txt_easting": False,
        #     "txt_northing": False,
        # },
        # "Rain Gauge": {
        #     "label_mh_ref": False,
        #     "txt_mh_ref": False,
        #     "label_easting": True,
        #     "label_northing": True,
        #     "txt_easting": True,
        #     "txt_northing": True,
        # },
        # "Pump Logger": {
        #     "label_mh_ref": True,
        #     "txt_mh_ref": True,
        #     "label_easting": False,
        #     "label_northing": False,
        #     "txt_easting": False,
        #     "txt_northing": False,
        # }
    }

    def __init__(self, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_add_site, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        self.cboSiteType.currentIndexChanged.connect(self.on_site_type_combobox_changed)

        self.txt_easting.setText("0.0")
        self.txt_northing.setText("0.0")

        self.on_site_type_combobox_changed()

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()

    def on_site_type_combobox_changed(self):
        selected_text = self.cboSiteType.currentText()
        settings = self.site_type_settings.get(selected_text, {})
        for widget_name, state in settings.items():
            widget = getattr(self, widget_name)
            widget.setEnabled(state)
