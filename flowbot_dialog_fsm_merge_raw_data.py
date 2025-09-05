from ui_elements.ui_flowbot_dialog_fsm_merge_raw_data_base  import Ui_Dialog
from PyQt5 import QtWidgets
from flowbot_graphing import graphFSMInstall
from typing import Optional
from flowbot_management import fsmInstall, fsmProject, fsmRawData
import pandas as pd

class flowbot_dialog_fsm_merge_raw_data(QtWidgets.QDialog, Ui_Dialog):
    
    # def __init__(self, interim_id: int, a_project: fsmProject, parent=None):
    def __init__(self, plotted_install: fsmInstall, plotted_raw: fsmRawData, parent=None):
        """Constructor."""
        super(flowbot_dialog_fsm_merge_raw_data, self).__init__(parent)
        self.setupUi(self)

        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)        

        self.aFSMGraph: Optional[graphFSMInstall] = graphFSMInstall(self.plotCanvasMergeData)
        self.aFSMGraph.plotted_install = plotted_install
        self.aFSMGraph.plotted_raw = plotted_raw
        self.aFSMGraph.update_plot(True, False)

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()


from ui_elements.ui_flowbot_dialog_fsm_merge_raw_data_base import Ui_Dialog
from PyQt5 import QtWidgets, QtCore
from flowbot_graphing import graphFSMInstall
from typing import Optional
from flowbot_management import fsmInstall, fsmRawData

class flowbot_dialog_fsm_merge_raw_data(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, plotted_install: fsmInstall,
                 plotted_existing_raw: fsmRawData,
                 plotted_temp_raw: fsmRawData,
                 parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # wire buttons
        self.btnOK.clicked.connect(self.onAccept)
        self.btnCancel.clicked.connect(self.onReject)

        # graph
        self.aFSMGraph: Optional[graphFSMInstall] = graphFSMInstall(self.plotCanvasMergeData)
        self.aFSMGraph.plotted_install = plotted_install
        self.aFSMGraph.plotted_raw = plotted_existing_raw
        self.aFSMGraph.overlay_temp_raw = plotted_temp_raw
        # self.aFSMGraph.set_selection_callback(self.on_span_selected)
        self.aFSMGraph.update_plot(True, False)

        # # show ranges in labels
        # self.lblExistingRange.setText(self.aFSMGraph._format_range(plotted_existing_raw))
        # self.lblNewRange.setText(self.aFSMGraph._format_range(plotted_temp_raw))

        # # seed dt edits from temp range if present
        # # start, end = self._guess_bounds(plotted_temp_raw)
        # start, end = self.aFSMGraph._guess_bounds_from_raw(plotted_temp_raw)
        # if start and end:
        #     # self._set_dt(self.dtStart, start)
        #     # self._set_dt(self.dtEnd, end)
        #     # draw shaded band
        #     if hasattr(self.aFSMGraph, "_shade_selection"):
        #         self.aFSMGraph._shade_selection(start, end)

        # self.selection_start = None
        # self.selection_end = None

    # def _format_range(self, raw: fsmRawData) -> str:
    #     mins = []
    #     maxs = []
    #     for attr in ("dep_data","vel_data","bat_data","rg_data","pl_data"):
    #         df = getattr(raw, attr, None)
    #         if df is not None and not df.empty:
    #             mins.append(df["Timestamp"].min())
    #             maxs.append(df["Timestamp"].max())
    #     if not mins:
    #         return "—"
    #     return f"{min(mins)}  →  {max(maxs)}"

    # def _guess_bounds(self, raw: fsmRawData):
    #     mins, maxs = [], []
    #     for attr in ("dep_data","vel_data","bat_data","rg_data","pl_data"):
    #         df = getattr(raw, attr, None)
    #         if df is not None and not df.empty:
    #             mins.append(df["Timestamp"].min())
    #             maxs.append(df["Timestamp"].max())
    #     if not mins:
    #         return None, None
    #     return min(mins), max(maxs)

    # def _set_dt(self, widget: QtWidgets.QDateTimeEdit, ts):
    #     if isinstance(ts, QtCore.QDateTime):
    #         widget.setDateTime(ts)
    #     else:
    #         widget.setDateTime(QtCore.QDateTime(ts))

    # def on_span_selected(self, start, end):
    #     self.selection_start, self.selection_end = start, end
    #     # self._set_dt(self.dtStart, start)
    #     # self._set_dt(self.dtEnd, end)

    # def selected_range(self):
    #     # prefer drag selection; fallback to edits
    #     if self.selection_start is None or self.selection_end is None:
    #         self.selection_start = self.dtStart.dateTime().toPyDateTime()
    #         self.selection_end   = self.dtEnd.dateTime().toPyDateTime()
    #     return self.selection_start, self.selection_end

    def onAccept(self):
        self.accept()

    def onReject(self):
        self.reject()