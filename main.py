"""
Main Script

This script serves as the entry point for the application. It orchestrates the execution
of various components to achieve the intended functionality.

Usage:
To run the application, execute this script using Python:

    python main.py

Author:
Fergus Graham
"""
# import subprocess
import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import (QFile, QByteArray)
from qgis.core import QgsApplication
from flowbot_mainwindow_gis import FlowbotMainWindowGis
from flowbot_helper import rps_or_tt, strVersion, root_path, resource_path
import logging
from flowbot_logging import get_logger

# Disable logging for all third-party loggers, except 'flowbot_logger'
for name, log in logging.Logger.manager.loggerDict.items():
    if isinstance(log, logging.Logger):  # Only set level if it's an actual logger
        if name != 'flowbot_logger':
            log.setLevel(logging.CRITICAL)
        else:
            log.setLevel(logging.DEBUG)


# # Create or get the custom logger
# logger = logging.getLogger('flowbot_logger')

# # Set the logging level for your logger (DEBUG to capture everything)
# logger.setLevel(logging.DEBUG)

# # Create a file handler to log to a file
# file_handler = logging.FileHandler('flowbot.log')
# file_handler.setLevel(logging.DEBUG)

# # Create a console handler (optional, for debugging output in the terminal)
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)

# # Create a logging format
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
# console_handler.setFormatter(formatter)

# # Add the handlers to the logger
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)

# # Disable logging for all third-party loggers
# for name, log in logging.Logger.manager.loggerDict.items():
#     if isinstance(log, logging.Logger) and name != 'flowbot_logger':
#         log.setLevel(logging.CRITICAL)

# # Now, use the `logger` throughout your app
# logger.debug("Logging setup complete.")

logger = get_logger('flowbot_logger')


def setup_qgis(qgs_app):
    # Set QGIS paths based on whether running as a bundled application or not
    bundle_dir = resource_path('flowbot_qgis_bundle_env\\Library')
    qgis_prefix_path = bundle_dir
    qgis_plugin_path = bundle_dir + "\\plugins"

    # Set environment variables
    os.environ["GDAL_DATA"] = bundle_dir + "\\share\\gdal"
    os.environ["GDAL_DRIVER_PATH"] = bundle_dir + "\\lib\\gdalplugins"
    os.environ["GEOTIFF_CSV"] = bundle_dir + "\\share\\epsg_csv"
    os.environ["PDAL_DRIVER_PATH"] = bundle_dir + "\\bin"
    os.environ["QT_PLUGIN_PATH"] = bundle_dir + \
        "\\qtplugins;" + bundle_dir + "\\plugins"

    # Append paths to system path
    sys.path.append(bundle_dir + "\\python")
    sys.path.append(bundle_dir + "\\python\\plugins")
    sys.path.append(bundle_dir + "\\python\\qgis")
    sys.path.append(bundle_dir + "\\bin")
    sys.path.append(bundle_dir + "\\lib\\site-packages")

    # Log all paths and environment variables for debugging
    logger.debug("bundle_dir: %s", bundle_dir)
    logger.debug("qgis_prefix_path: %s", qgis_prefix_path)
    logger.debug("qgis_plugin_path: %s", qgis_plugin_path)
    logger.debug("GDAL_DATA: %s", os.environ.get("GDAL_DATA"))
    logger.debug("GDAL_DRIVER_PATH: %s", os.environ.get("GDAL_DRIVER_PATH"))
    logger.debug("GEOTIFF_CSV: %s", os.environ.get("GEOTIFF_CSV"))
    logger.debug("PDAL_DRIVER_PATH: %s", os.environ.get("PDAL_DRIVER_PATH"))
    logger.debug("QT_PLUGIN_PATH: %s", os.environ.get("QT_PLUGIN_PATH"))
    logger.debug("sys.path: %s", sys.path)

    # Set QGIS application paths
    qgs_app.setPrefixPath(qgis_prefix_path, True)
    qgs_app.setPluginPath(qgis_plugin_path)
    qgs_app.initQgis()

# def setup_qgis(qgs_app):
#     # """ Set QGIS paths based on whether running as a bundled application or not """
#     bundle_dir = resource_path('flowbot_qgis_bundle_env\\Library')
#     qgis_prefix_path = bundle_dir
#     qgis_plugin_path = bundle_dir + "\\plugins"

#     # os.environ["OSGEO4W_ROOT"] = bundle_dir
#     os.environ["GDAL_DATA"] = bundle_dir + "\\share\\gdal"
#     os.environ["GDAL_DRIVER_PATH"] = bundle_dir + "\\lib\\gdalplugins"
#     os.environ["GEOTIFF_CSV"] = bundle_dir + "\\share\\epsg_csv"
#     os.environ["PDAL_DRIVER_PATH"] = bundle_dir + "\\bin"
#     os.environ["QT_PLUGIN_PATH"] = bundle_dir + \
#         "\\qtplugins;" + bundle_dir + "\\plugins"

#     sys.path.append(bundle_dir + "\\python")
#     sys.path.append(bundle_dir + "\\python\\plugins")
#     sys.path.append(bundle_dir + "\\python\\qgis")
#     sys.path.append(bundle_dir + "\\bin")
#     sys.path.append(bundle_dir + "\\lib\\site-packages")

#     qgs_app.setPrefixPath(qgis_prefix_path, True)
#     qgs_app.setPluginPath(qgis_plugin_path)
#     qgs_app.initQgis()


app = QApplication(sys.argv)
app.setStyle('Fusion')

qgs = QgsApplication([], True)
setup_qgis(qgs)

mainWindow = FlowbotMainWindowGis(None, app)

stylesheet_path = os.path.join(os.path.dirname(
    __file__), f'resources/qss/{rps_or_tt}_default.qss')

# Open the file
file = QFile(stylesheet_path)
if file.open(QFile.ReadOnly):
    # Read the content
    content = QByteArray(file.readAll())
    # Close the file
    file.close()
else:
    print("Failed to open " + stylesheet_path)

# Set the stylesheet
app.setStyleSheet(str(content, encoding='utf-8'))
# mainWindow.setWindowTitle("Flowbot v" + strVersion)
mainWindow.show()


def excepthook(exctype, value, tb):
    traceback_formated = traceback.format_exception(exctype, value, tb)
    traceback_string = "".join(traceback_formated)
    print(traceback_string, file=sys.stderr)
    # sys.exit(1)


sys.excepthook = excepthook

app.exec_()

# import sys
# from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
# from qgis.gui import QgsMapCanvas
# from qgis.core import QgsApplication, QgsVectorLayer, QgsProject

# class MyMainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("QGIS Map in PyQt")
#         self.setGeometry(100, 100, 800, 600)

#         self.setupUi()

#     def setupUi(self):
#         layout = QVBoxLayout()
#         canvas = QgsMapCanvas()
#         layout.addWidget(canvas)

#         # Add layers to the canvas
#         layer = QgsVectorLayer("C:/Temp/ATO_Impermeable_Areas.shp", "Layer Name", "ogr")
#         QgsProject.instance().addMapLayer(layer)
#         canvas.setExtent(layer.extent())

#         widget = QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)


# def main():
#     app = QgsApplication([], True)
#     QgsApplication.setPrefixPath("C:/Users/Fergus.Graham/AppData/Local/anaconda3/envs/conda_qgis_env/Library", True)
#     QgsApplication.initQgis()

#     window = MyMainWindow()
#     window.show()

#     sys.exit(app.exec_())


# if __name__ == "__main__":
#     main()
