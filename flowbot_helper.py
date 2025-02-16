# from PyQt5 import QtWidgets
import math
import matplotlib.dates as mpl_dates
from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
import numpy as np
from pdf2image import convert_from_path
from PyQt5.QtCore import Qt, pyqtSignal, QBuffer
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QSpacerItem, QHBoxLayout, QWidget,
                             QPushButton, QScrollArea, QSizePolicy, QMessageBox, QSlider)
from PyQt5.QtGui import QPixmap, QImage, QWheelEvent
# from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSpacerItem
# from PyQt5.QtCore import Qt
import sys
import os
import types
from PIL import Image
import io
import json
import pickle
from datetime import datetime
import pandas as pd
from pandas import Timestamp

from flowbot_logging import get_logger
# from flowbot_management import fsmRawData

logger = get_logger('flowbot_logger')

# from PyQt5.QtCore import QBuffer, Qt

# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QScrollArea


try:
    basestring  # type: ignore[attr-defined]
except NameError:
    basestring = str

strMajorRelease = "4"
strMinorRelease = "2"
strUpdate = "0"
strOther = " (Beta)"
strVersion = f'{strMajorRelease}.{strMinorRelease}.{strUpdate}{strOther}'

rps_or_tt = "rps"
# rps_or_tt = "tt"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def root_path():
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path


def serialize_list(data):
    if not data:  # Check if the list is empty
        return json.dumps(data)

    if isinstance(data[0], datetime):  # Check if the first element is a datetime object
        # Convert datetime objects to ISO 8601 formatted strings
        serialized_data = [date.isoformat() for date in data]
        return json.dumps(serialized_data)
    else:
        return json.dumps(data)


def deserialize_list(data):
    parsed_data = json.loads(data)
    if len(parsed_data) > 0:
        if isinstance(parsed_data[0], str):
            try:
                # Attempt to parse each string into a datetime object
                deserialized_data = [datetime.fromisoformat(
                    date) for date in parsed_data]
                return deserialized_data
            except ValueError:
                # If parsing fails, return the original parsed data
                pass
    return parsed_data


def serialize_timestamp_list(data):
    serialized_data = []
    for sublist in data:
        # Convert Timestamp objects to ISO 8601 formatted strings
        sublist_serialized = [ts.isoformat() for ts in sublist]
        serialized_data.append(sublist_serialized)
    return json.dumps(serialized_data)


def deserialize_timestamp_list(json_string):
    # Deserialize JSON string to a list of lists of ISO 8601 formatted strings
    deserialized_data = json.loads(json_string)

    # Convert ISO 8601 formatted strings to Timestamp objects
    data_timestamps = []
    for sublist in deserialized_data:
        sublist_timestamps = [Timestamp(date_string)
                              for date_string in sublist]
        data_timestamps.append(sublist_timestamps)

    return data_timestamps


def serialize_item(item):
    return pickle.dumps(item)


def deserialize_item(data):
    return pickle.loads(data)


def get_classification_legend_dataframe():
    # Define the legend data
    legendData = [['X', 'Not Working', '', 'G', 'Dry Pipe', '', 'L', 'Low Flow <10l/s', '', 'P', 'Pluming', '', 'U', 'Dislodged Sensor', '', 'O', 'Taken Out'],
                  ['V', 'Velocity Problem', '', 'B', 'Blocked Filter RG', '', 'T', 'Sediment', '',
                      'K', 'Monitor Submerged', '', 'H', 'Standing Water', '', 'M', 'Monitor Changed'],
                  ['D', 'Depth Problem', '', 'R', 'Ragging', '', 'S', 'Surcharged',
                      '', 'W', 'Working', '', 'I', 'Installed', '', '', '']
                  ]
    legIndex = pd.Index(['1', '2', '3'], name='RowNames')

    return pd.DataFrame(legendData, index=legIndex)


def get_classification_color_mapping():

    # Define the color mapping
    return {
        'X': '#c0c0c0',
        'V': '#ffff00',
        'D': '#00ffff',
        'G': '#ffff00',
        'B': '#c0c0c0',
        'R': '#99ccff',
        'L': '#0000ff',
        'T': '#ffcc99',
        'S': '#808000',
        'P': '#ccffcc',
        'K': '#993300',
        'W': '#ffffff',
        'U': '#c0c0c0',
        'H': '#ffff99',
        'I': '#000000',
        'O': '#000000',
        'M': '#000000',
        '': '#c0c0c0',
    }


class myCustomToolbar(NavigationToolbar2QT):

    def __init__(self, canvas, parent, coordinates=True, lockNav=False):
        super().__init__(canvas, parent, coordinates)

        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to  previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle (x-constrained)', 'zoom_to_rect', 'zoom'),
            ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
            ('Save', 'Save the figure', 'filesave', 'save_figure')
        )

        self.lockNavigation(lockNav)
        # for ac in NavigationToolbar2QT.actions(self):
        #     if ac.text() in ['Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Subplots', 'Customize']:
        #         ac.setEnabled(False)

    def lockNavigation(self, makeLocked: bool):
        for ac in NavigationToolbar2QT.actions(self):
            if ac.text() in ['Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Subplots', 'Customize']:
                ac.setEnabled(not makeLocked)

    def press_zoom_x(self, event):
        event.key = 'x'
        NavigationToolbar2QT.press_zoom(self, event)

    def drag_zoom_x(self, event):
        event.key = 'x'
        NavigationToolbar2QT.drag_zoom(self, event)

    def release_zoom_x(self, event):
        event.key = 'x'
        NavigationToolbar2QT.release_zoom(self, event)


class PdfViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        self.main_layout = QHBoxLayout(self)

        # Custom scroll area for the label
        self.scroll_area = CustomScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Label for displaying PDF pages
        self.label = QLabel(self.scroll_area)
        self.label.setAlignment(Qt.AlignCenter)
        # Disable QLabel's own scaling to handle it manually
        self.label.setScaledContents(False)

        # Navigation buttons
        self.prev_button = QPushButton('⬆', self)
        self.next_button = QPushButton('⬇', self)
        self.zoom_in_button = QPushButton('+', self)
        self.zoom_out_button = QPushButton('-', self)

        # Set fixed size for buttons
        button_size = 30
        self.prev_button.setFixedSize(button_size, button_size)
        self.next_button.setFixedSize(button_size, button_size)
        self.zoom_in_button.setFixedSize(button_size, button_size)
        self.zoom_out_button.setFixedSize(button_size, button_size)

        # Connect buttons to functions
        self.prev_button.clicked.connect(self.prevPage)
        self.next_button.clicked.connect(self.nextPage)
        self.zoom_in_button.clicked.connect(self.zoomIn)
        self.zoom_out_button.clicked.connect(self.zoomOut)

        # Layout for buttons
        self.button_layout = QVBoxLayout()
        self.button_layout.addWidget(self.zoom_in_button)
        self.button_layout.addWidget(self.zoom_out_button)
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addItem(QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add widgets to scroll area
        self.scroll_area.setWidget(self.label)

        # Add scroll area and buttons layout to main layout
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

        # PDF pages
        self.pages = []
        self.current_page = 0
        self.current_pixmap = None
        self.zoom_factor = 1.0

        # Variables for panning
        self.last_mouse_pos = None

    def loadPdf(self, filePath):
        try:
            # type: ignore[attr-defined]
            poppler_path = os.path.join(
                sys._MEIPASS, "resources\\poppler\\bin")
        except Exception:
            poppler_path = 'C:\\Users\\Fergus.Graham\\AppData\\Local\\anaconda3\\envs\\conda_qgis_env\\Library\\bin'
            logger.error('Exception occurred', exc_info=True)
        try:
            if os.path.exists(poppler_path):
                self.pages = convert_from_path(
                    filePath, poppler_path=poppler_path)
            else:
                self.pages = convert_from_path(filePath)
            self.current_page = 0
            self.showPage()
        except Exception as e:
            logger.error('Exception occurred', exc_info=True)
            msg = QMessageBox(self)
            msg.critical(
                self, 'Error', f'An error occurred: {e}', QMessageBox.Ok)

    def showPage(self):
        if self.pages:
            page_image = self.pages[self.current_page]
            self.current_pixmap = self.pil2pixmap(page_image)
            self.updatePixmap()

    def nextPage(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.showPage()

    def prevPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.showPage()

    def zoomIn(self):
        self.zoom_factor += 0.1
        self.updatePixmap()

    def zoomOut(self):
        if self.zoom_factor > 0.1:
            self.zoom_factor -= 0.1
            self.updatePixmap()

    def pil2pixmap(self, im):
        im = im.convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimage = QImage(data, im.size[0], im.size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qimage)

    def updatePixmap(self):
        if self.current_pixmap:
            # Get the size of the viewport
            viewport_size = self.scroll_area.viewport().size()

            # Calculate the zoomed size based on the viewport size and the zoom factor
            zoomed_size = viewport_size * self.zoom_factor

            # Scale the pixmap to the zoomed size while maintaining aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                zoomed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Set the scaled pixmap to the label
            self.label.setPixmap(scaled_pixmap)

            # Ensure that the scroll bars are correctly updated
            self.scroll_area.ensureVisible(0, 0, 0, 0)

    def resizeEvent(self, event):
        self.updatePixmap()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.scroll_area.horizontalScrollBar().setValue(
                self.scroll_area.horizontalScrollBar().value() - delta.x())
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = None

    def wheelEvent(self, event: QWheelEvent):
        # Zoom in or out depending on the scroll direction
        if event.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()


class CustomScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

    # def wheelEvent(self, event: QWheelEvent):
    #     # Reimplement the wheel event to ensure zooming
    #     if event.modifiers() & Qt.ControlModifier:
    #         if event.angleDelta().y() > 0:
    #             self.parent().zoomIn()
    #         else:
    #             self.parent().zoomOut()
    #     else:
    #         super().wheelEvent(event)
    def wheelEvent(self, event: QWheelEvent):
        # Reimplement the wheel event to ensure zooming
        if event.modifiers() & Qt.ControlModifier:
            super().wheelEvent(event)
        else:
            if event.angleDelta().y() > 0:
                self.parent().zoomIn()
            else:
                self.parent().zoomOut()


class PlotWidget(QWidget):

    toolbar: myCustomToolbar | None = None
    mouseClicked = pyqtSignal(object)
    scrollZoomCompleted = pyqtSignal()
    pan_finished = pyqtSignal(object)
    event_connections = []

    def __init__(self, parent=None, toolbar=False, figsize=None, dpi=100, scroll_zoom=False, x_pan=False):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(toolbar, figsize, dpi)

        self.scroll_zoom_enabled = scroll_zoom
        self.x_pan_enabled = x_pan
        self.canvas.mpl_connect('button_press_event', self.on_canvas_clicked)
        self.canvas.mpl_connect('scroll_event', self.on_canvas_scrolled)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)

        self._dragging = False
        self._last_mouse_x = None

    def setupUi(self, toolbar=True, figsize=None, dpi=100):
        layout = QVBoxLayout(self)
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = myCustomToolbar(self.canvas, self)
        self.toolbar.press_zoom = types.MethodType(
            myCustomToolbar.press_zoom_x, self.toolbar)
        self.toolbar.drag_zoom = types.MethodType(
            myCustomToolbar.drag_zoom_x, self.toolbar)
        self.toolbar.release_zoom = types.MethodType(
            myCustomToolbar.release_zoom_x, self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.showToolbar(toolbar)

    def showToolbar(self, show: bool = True):
        if show:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def toolbarNavigation(self, allow: bool = False):
        self.toolbar.lockNavigation(allow)

    def on_canvas_clicked(self, event):

        if event.button == 1:  # Left mouse button
            if self.toolbar.mode.name == 'PAN':
                self._dragging = True
        if event.button == 2:  # Middle mouse button
            if not self.x_pan_enabled:
                return
            self._dragging = True
            self._last_mouse_x = event.x
        else:
            self.mouseClicked.emit(event)

    def on_canvas_scrolled(self, event):
        if not self.scroll_zoom_enabled:
            return

        ax = event.inaxes
        if ax is None:
            return

        if event.button == 'up':
            scale_factor = 0.8
        elif event.button == 'down':
            scale_factor = 1.2
        else:
            return

        xlim = ax.get_xlim()
        xdata = event.xdata
        new_xlim = [xdata + (x - xdata) * scale_factor for x in xlim]
        ax.set_xlim(new_xlim)

        self.scrollZoomCompleted.emit()

    # def on_mouse_press(self, event):
    #     if event.button == 2:  # Middle mouse button
    #         self._dragging = True
    #         self._last_mouse_x = event.x

    def on_mouse_move(self, event):
        if not self.x_pan_enabled:
            return
        # # if self._dragging and event.inaxes and event.xdata:
        # if self._dragging and event.inaxes and event.xdata is not None and self._last_mouse_x is not None:
        #     a_xdata = event.xdata
        #     dx = self._last_mouse_x - a_xdata
        #     xlim = event.inaxes.get_xlim()
        #     new_xlim = [x + dx for x in xlim]
        #     event.inaxes.set_xlim(new_xlim)
        #     self._last_mouse_x = a_xdata
        #     self.canvas.draw_idle()
        if self._dragging and event.inaxes and event.xdata is not None:
            start_x = event.x
            if self._last_mouse_x is not None:
                dx_pixels = self._last_mouse_x - start_x
                ax = event.inaxes
                dx_data = dx_pixels * \
                    (ax.get_xlim()[1] - ax.get_xlim()[0]) / ax.bbox.width
                xlim = ax.get_xlim()
                new_xlim = [x + dx_data for x in xlim]
                ax.set_xlim(new_xlim)

                self._last_mouse_x = start_x  # Update last mouse x position in pixels
                self.canvas.draw_idle()

    def on_mouse_release(self, event):
        if event.button == 1:  # Left mouse button
            if self.toolbar.mode.name == 'PAN':
                self._dragging = False
                self.pan_finished.emit(event.inaxes)
        if event.button == 2:  # Middle mouse button
            if not self.x_pan_enabled:
                return
            self._dragging = False
            self._last_mouse_x = None
            self.scrollZoomCompleted.emit()

        # # Adjust y-axis limits to fit the visible data within new x-axis limits
        # new_xmin, new_xmax = mpl_dates.num2date(ax.get_xlim())
        # new_xmin = np.datetime64(new_xmin)
        # new_xmax = np.datetime64(new_xmax)
        # lines = ax.get_lines()
        # min_y = float('inf')
        # max_y = float('-inf')

        # for line in lines:
        #     x_data = line.get_xdata()
        #     y_data = line.get_ydata()

        #     mask = (x_data >= new_xmin) & (x_data <= new_xmax)
        #     if any(mask):
        #         min_y = min(min_y, min(y_data[mask]))
        #         max_y = max(max_y, max(y_data[mask]))

        # # Set new limits for y-axis
        # if min_y != float('inf') and max_y != float('-inf'):
        #     padding = 0.1 * (max_y - min_y)  # Optional padding around the data range
        #     ax.set_ylim(min_y - padding, max_y + padding)

        # # Update and redraw
        # ax.relim()
        # ax.autoscale_view()

        # ax.relim()
        # ax.autoscale(axis='y')

        self.canvas.draw_idle()

        self.scrollZoomCompleted.emit()

    # def resizeEvent(self, event):
    #     new_size = event.size()
    #     self.update_figure_size(new_size.width(), new_size.height())

    # def update_figure_size(self, width, height):
    #     # Calculate the new figure size while maintaining aspect ratio of A4 paper (14.1:10)
    #     widget_aspect_ratio = width / height
    #     desired_aspect_ratio = 14.1 / 10

    #     if widget_aspect_ratio > desired_aspect_ratio:
    #         new_width = height * desired_aspect_ratio
    #         new_height = height
    #     else:
    #         new_width = width
    #         new_height = width / desired_aspect_ratio

    #     # # Convert to inches (1 inch = 2.54 cm)
    #     # new_width_inch = new_width / self.canvas.logicalDpiX() * 2.54
    #     # new_height_inch = new_height / self.canvas.logicalDpiY() * 2.54
    #     # Convert to inches (1 inch = 2.54 cm)
    #     new_width_inch = new_width / self.canvas.logicalDpiX()
    #     new_height_inch = new_height / self.canvas.logicalDpiY()

    #     # Update figure size
    #     self.figure.set_size_inches(new_width_inch, new_height_inch)
    #     self.canvas.draw()

    # if event.button == 1:  # Left mouse button
    #     self.leftMouseClicked.emit(event)
    # elif event.button == 3:  # Right mouse button
    #     self.rightMouseClicked.emit(x_clicked)

    # if event.inaxes:
    #     # Get the x-coordinate of the mouse click
    #     x_clicked = event.xdata
    #     # Emit signals based on mouse button clicked
    #     if event.button == 1:  # Left mouse button
    #         self.leftMouseClicked.emit(event)
    #     elif event.button == 3:  # Right mouse button
    #         self.rightMouseClicked.emit(x_clicked)

    # def convert_x_to_date(self, x_coordinate):
    #     # Implement logic to convert x-coordinate to date
    #     # This will depend on your specific date formatting and axis scaling

    # def handle_left_click(self, clicked_date):
    #     # Implement logic to handle left click selection

    # def handle_right_click(self, clicked_date):
    #     # Implement logic to handle right click selection

# class NavToolbarWidget(QWidget):

#     def __init__(self, parent=None, canvas=None) -> None:
#         super().__init__(parent)
#         self.canvas = canvas
#         self.toolbar = None
#         # self.vbLayout = None
#         self.setupUi()

#     # def __init__(self, flags, parent=None, canvas=None) -> None:
#     #     super().__init__(parent, flags)
#     #     self.canvas = canvas
#     #     self.setupUi()

#     def setupUi(self):
#         self.vbLayout = QVBoxLayout(self)
#         if not self.canvas is None:
#             self.toolbar = myCustomToolbar(self.canvas, self, lockNav=False)
#             self.vbLayout.addWidget(self.toolbar, 1)


class DoubleSlider(QSlider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decimals = 5
        self._max_int = 10 ** self.decimals

        super().setMinimum(0)
        super().setMaximum(self._max_int)

        self._min_value = 0.0
        self._max_value = 1.0

    @property
    def _value_range(self):
        return self._max_value - self._min_value

    def value(self):
        return float(super().value()) / self._max_int * self._value_range + self._min_value

    def setValue(self, value):
        if (self._value_range * self._max_int) == 0:
            super().setValue(int(self._max_valueq))
        else:
            super().setValue(int((value - self._min_value) / self._value_range * self._max_int))

    def setMinimum(self, value):
        if value > self._max_value:
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._min_value = value
        self.setValue(self.value())

    def setMaximum(self, value):
        if value < self._min_value:
            raise ValueError("Minimum limit cannot be higher than maximum")

        self._max_value = value
        self.setValue(self.value())

    def minimum(self):
        return self._min_value

    def maximum(self):
        return self._max_value


def getBlankFigure(plotWidget: PlotWidget):

    plotWidget.figure.clear()

    # rpsImage = QPixmap(f'resources/{rps_or_tt}_logo.png')
    rpsImage = QPixmap(resource_path(f'resources/{rps_or_tt}_logo.png'))
    buffer = QBuffer()
    buffer.open(QBuffer.ReadWrite)
    rpsImage.toImage().save(buffer, "PNG")
    image = Image.open(io.BytesIO(buffer.data()))

    plotAxisImage = plotWidget.figure.add_subplot(111)
    plotAxisImage.imshow(image)
    plotAxisImage.set_xticklabels([])
    plotAxisImage.set_yticklabels([])
    plotAxisImage.grid(False)
    plotAxisImage.set_xticks([])
    plotAxisImage.set_yticks([])
    plotAxisImage.spines['top'].set_visible(False)
    plotAxisImage.spines['right'].set_visible(False)
    plotAxisImage.spines['bottom'].set_visible(False)
    plotAxisImage.spines['left'].set_visible(False)


def getKlingGupta(df, obsColName, predColName):
    correl = df[obsColName].corr(df[predColName])
    obsStdDev = df[obsColName].std()
    predStdDev = df[predColName].std()
    obsMean = df[obsColName].mean()
    predMean = df[predColName].mean()

    if np.isnan(correl):
        myKGE = round(1-((((-1)**2)+(((predStdDev/obsStdDev)-1)
                      ** 2)+(((predMean/obsMean)-1)**2))**0.5), 4)
    else:
        myKGE = round(1-((((correl-1)**2)+(((predStdDev/obsStdDev)-1)
                      ** 2)+(((predMean/obsMean)-1)**2))**0.5), 4)

    return myKGE


def getNashSutcliffe(df, obsColName, predColName):
    dfNash = df.copy()
    dfNash['Numerator'] = (dfNash[predColName] - dfNash[obsColName])**2
    dfNash['Denominator'] = (dfNash[obsColName] - dfNash[obsColName].mean())**2

    myNSE = round(1 - (dfNash['Numerator'].sum() /
                  dfNash['Denominator'].sum()), 4)

    return myNSE


def getCoeffVariation(df, colName):
    stdDev = df[colName].std()
    mean = df[colName].mean()

    myCV = round((stdDev/mean), 4)

    return myCV


def generate_shape(width, height, intervals, shape_type):
    """
    Generate evenly spaced (width, height) pairs for a specified shape.

    :param width: Total width (W) of the pipe.
    :param height: Total height (H) of the pipe.
    :param intervals: Number of intervals for generating the shape.
    :param shape_type: Shape name ('ARCH', 'CIRC', 'CNET', 'EGG', 'EGG2', 'OVAL', 'RECT', 'UTOP').
    :return: List of (width, height) pairs defining the shape.
    :raises ValueError: If the input parameters violate the shape rules.
    """

    if intervals < 2:
        raise ValueError("Number of intervals must be at least 2.")

    # Generate evenly spaced height intervals
    heights = [i * height / (intervals - 1) for i in range(intervals)]
    points = []

    # Check shape-specific constraints
    if shape_type.upper() == "ARCH":
        if height <= width / 2:
            raise ValueError("ARCH requires H > W/2.")
        radius = width / 2
        flat_height = height - radius

        for h in heights:
            if h >= flat_height:  # In the semicircle
                offset = h - flat_height
                w = 2 * math.sqrt(radius**2 - offset**2)
            else:  # In the flat rectangle
                w = width
            points.append((w, h))

    elif shape_type.upper() == "CIRC":
        if height != width:
            raise ValueError("CIRC requires H = W.")
        # CIRCLE shape: full circle with a diameter of `width`
        radius = width / 2
        center = height / 2  # Center of the circle

        for h in heights:
            offset = abs(h - center)
            if offset <= radius:  # Ensure offset is within the circle's radius
                w = 2 * math.sqrt(radius**2 - offset**2)
            else:
                w = 0  # Outside the circle (should not occur)
            points.append((w, h))

    elif shape_type.upper() == "CNET":
        if not ((width / 2) < height < width):
            raise ValueError("CNET requires W/2 < H < W.")
        # CNET: Top semicircle with diameter W, bottom semicircle with radius H - W/2
        top_radius = width / 2  # Radius of the top semicircle
        bottom_radius = height - top_radius  # Radius of the bottom semicircle

        top_center = height - top_radius  # Center of the top semicircle
        bottom_center = bottom_radius  # Center of the bottom semicircle

        for h in heights:
            if h >= top_center:  # In the top semicircle
                offset = h - top_center
                if abs(offset) <= top_radius:
                    w = 2 * math.sqrt(top_radius**2 - offset**2)
                else:
                    w = 0  # Should not occur
            elif h <= bottom_center:  # In the bottom semicircle
                offset = bottom_center - h
                if abs(offset) <= bottom_radius:
                    w = 2 * math.sqrt(bottom_radius**2 - offset**2)
                else:
                    w = 0  # Should not occur
            else:  # Connecting rectangle (constant width)
                w = width
            points.append((w, h))

    elif shape_type.upper() == "EGG":
        if not (width < height < 2 * width):
            raise ValueError("EGG requires W < H < 2W.")
        # EGG: Defined by two touching circles
        top_radius = width / 2  # Top circle radius
        bottom_radius = (height - width) / 2  # Bottom circle radius
        top_center = height - top_radius  # Center of the top circle
        bottom_center = bottom_radius  # Center of the bottom circle

        for h in heights:
            if h >= top_center:  # In the top circle
                offset = h - top_center
                w = 2 * math.sqrt(top_radius**2 - offset**2)
            elif h <= bottom_center:  # In the bottom circle
                offset = bottom_center - h
                w = 2 * math.sqrt(bottom_radius**2 - offset**2)
            else:  # Tapering section
                # Linear interpolation of width from W to H - W
                w = (height - width) + ((width - (height - width)) *
                                        (h - bottom_center) / (top_center - bottom_center))
            points.append((w, h))

    elif shape_type.upper() == "EGG2":
        if not (width < height < 3 * width):
            raise ValueError("EGG2 requires W < H < 3W.")
        # EGG2: Top circle, tapering section, and bottom circle
        top_radius = width / 2  # Radius of the top circle
        # Total gap height (tapering + bottom circle)
        gap_height = 0.5 * (height - width)
        bottom_radius = (0.5 * (height - width)) / \
            2  # Radius of the bottom circle

        top_center = height - top_radius  # Center of the top circle
        bottom_center = bottom_radius  # Center of the bottom circle

        for h in heights:
            if h >= top_center:  # In the top circle
                offset = h - top_center
                if offset <= top_radius:
                    w = 2 * math.sqrt(top_radius**2 - offset**2)
                else:
                    w = 0  # Handle any out-of-boundary cases (shouldn't occur)
            elif h >= bottom_center:  # In the tapering section
                # Linearly interpolate width from W to 2 * bottom_radius
                bottom_diameter = 2 * bottom_radius
                w = bottom_diameter + \
                    ((width - bottom_diameter) * (h - bottom_center) /
                     (top_center - bottom_center))
            else:  # In the bottom circle
                offset = h - bottom_center
                if offset <= bottom_radius:
                    w = 2 * math.sqrt(bottom_radius**2 - offset**2)
                else:
                    w = 0  # Handle any out-of-boundary cases (shouldn't occur)
            points.append((w, h))

    elif shape_type.upper() == "OVAL":
        if height <= width:
            raise ValueError("OVAL requires H > W.")
        # OVAL shape: top semicircle, middle rectangle, bottom semicircle
        radius = width / 2
        top_center = height - radius  # Center of the top semicircle
        bottom_center = radius  # Center of the bottom semicircle

        for h in heights:
            if h >= top_center:  # In the top semicircle
                offset = h - top_center
                if abs(offset) <= radius:
                    w = 2 * math.sqrt(radius**2 - offset**2)
                else:
                    w = 0  # Should not occur
            elif h <= bottom_center:  # In the bottom semicircle
                offset = bottom_center - h
                if abs(offset) <= radius:
                    w = 2 * math.sqrt(radius**2 - offset**2)
                else:
                    w = 0  # Should not occur
            else:  # In the middle rectangle
                w = width
            points.append((w, h))

    elif shape_type.upper() == "RECT":
        for h in heights:
            w = width
            points.append((w, h))

    elif shape_type.upper() == "UTOP":
        if height <= width / 2:
            raise ValueError("UTOP requires H > W/2.")
        # UTOP shape: Bottom semicircle, top rectangle
        radius = width / 2  # Radius of the bottom semicircle
        flat_height_start = radius  # Where the flat rectangle starts

        for h in heights:
            if h <= flat_height_start:  # In the bottom semicircle
                offset = abs(h - flat_height_start)
                if offset <= radius:
                    w = 2 * math.sqrt(radius**2 - offset**2)
                else:
                    w = 0  # Should not occur
            else:  # In the top rectangle
                w = width
            points.append((w, h))

    else:
        raise ValueError(f"Unsupported shape: {shape_type}. "
                         f"Supported shapes are: ARCH, CIRC, CNET, EGG, EGG2, OVAL, RECT, UTOP.")

    return points


def bytes_to_text(data, encoding='utf-8'):
    try:
        decoded_text = data.decode(encoding).rstrip('\x00')
        return decoded_text
    except UnicodeDecodeError:
        # If decoding using the specified encoding fails, fallback to ANSI
        decoded_text = data.decode('ansi').rstrip('\x00')
        return decoded_text


# class Handler(QObject):
#     signal_popup_clicked = Signal(str)

#     @Slot(str)
#     def popupClicked(self, popupText):
#         self.signal_popup_clicked.emit(popupText)

# class WebPage(QWebEnginePage):
#     def __init__(self, parent=None):
#         super().__init__(parent)

# class WebView(QWebEngineView):
#     def __init__(self, parent=None):
#         super().__init__(parent)

#         # Inside WebView class
#         self.handler = Handler()
#         # Set up the web channel and register the handler object
#         self.web_channel = QWebChannel()
#         self.web_channel.registerObject('handler', self.handler)

#         # Set the web channel for the page
#         self.page().setWebChannel(self.web_channel)

# class MplCanvas(FigureCanvasQTAgg):

#     def __init__(self, fig, parent=None, width=5, height=4, dpi=100):
#         super(MplCanvas, self).__init__(fig)


# class fbCustomToolbar(NavigationToolbar2QT):

#     def __init__(self, canvas_, parent_, lockNavigation=False):
#         self.toolitems = (
#             ('Home', 'Reset original view', 'home', 'home'),
#             ('Back', 'Back to  previous view', 'back', 'back'),
#             ('Forward', 'Forward to next view', 'forward', 'forward'),
#             ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
#             ('Zoom', 'Zoom to rectangle (x-constrained)', 'zoom_to_rect', 'zoom'),
#             ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#             ('Save', 'Save the figure', 'filesave', 'save_figure')
#             #            ('Port', 'Go to specific date', "hand", 'go_to_date')
#         )
#         NavigationToolbar2QT.__init__(self, canvas_, parent_)

#         if lockNavigation:
#             for ac in NavigationToolbar2QT.actions(self):
#                 if ac.text() in ['Home', 'Back', 'Forward', 'Pan', 'Zoom', 'Subplots', 'Customize']:
#                     ac.setEnabled(False)
# #                    self.mode = ''

#     def press_zoom_x(self, event):
#         event.key = 'x'
#         NavigationToolbar2QT.press_zoom(self, event)
#         #NavigationToolbar2QT.drag_zoom(self, event)

#     def drag_zoom_x(self, event):
#         event.key = 'x'
#         NavigationToolbar2QT.drag_zoom(self, event)

#     def release_zoom_x(self, event):
#         event.key = 'x'
#         NavigationToolbar2QT.release_zoom(self, event)
