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

# Disable DPI scaling (must be before QApplication is created or Qt is imported)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import (QFile, QByteArray, Qt)

QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)

from qgis.core import QgsApplication
# from qgis.analysis import QgsNativeAlgorithms
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

    # Set QGIS application paths
    qgs_app.setPrefixPath(qgis_prefix_path, True)
    qgs_app.setPluginPath(qgis_plugin_path)
    qgs_app.initQgis()

app = QApplication(sys.argv)
app.setStyle('Fusion')

qgs = QgsApplication([], True)
setup_qgis(qgs)

mainWindow = FlowbotMainWindowGis(None, app, qgs)

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
