import math
from typing import Optional, List
# from flowbot_helper import cstCONNECTION
from PyQt5 import (QtWidgets, QtCore, QtGui)
from PyQt5.QtWidgets import (QInputDialog, QMenu, QGraphicsScene, QGraphicsTextItem, QGraphicsView, QGraphicsItem,
                             QStyle, QGraphicsEllipseItem, QAction, QLineEdit, QApplication, QLabel, QGraphicsRectItem)
from PyQt5.QtCore import (Qt, QRectF, QPointF)
from PyQt5.QtGui import (QBrush, QPen, QColor, QPainter, QPainterPath)
from PyQt5.QtPrintSupport import QPrintPreviewDialog
from flowbot_survey_events import surveyEvent

cstWWPS = 'WWPS'
cstCSO = 'CSO'
cstWWTW = 'WWTW'
cstOUTFALL = 'OUTFALL'
cstJUNCTION = 'JUNCTION'
cstCONNECTION = 'CONNECTION'
cstNONE = 'NONE'


class genericGraphicsItem(QGraphicsItem):

    # _thisApp: Optional[QApplication] = None
    _controls = []
    controlPen = QPen(QColor(127, 127, 127), 2)
    controlBrush = QBrush(QColor(127, 127, 127))
    _canConnect = True

    def getCanConnect(self):
        return self._canConnect

    def setCanConnect(self, value):
        self._canConnect = value

    canConnect = property(
        fget=getCanConnect,
        fset=setCanConnect
    )

    def __init__(self, x, y, thisApp, parent=None):
        super().__init__(parent)

        self._thisApp: Optional[QApplication] = thisApp
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._controls = []
        locations = ["top", "right", "bottom", "left"]
        for aLoc in locations:
            control = ControlPoint(self)
            control.setPen(self.controlPen)
            control.setBrush(self.controlBrush)

            if aLoc == "top":
                control.setX(self.boundingRect().left() +
                             (self.boundingRect().width() / 2))
                control.setY(self.boundingRect().top())
            elif aLoc == "right":
                control.setX(self.boundingRect().right())
                control.setY(self.boundingRect().top() +
                             (self.boundingRect().height() / 2))
            elif aLoc == "bottom":
                control.setX(self.boundingRect().left() +
                             (self.boundingRect().width() / 2))
                control.setY(self.boundingRect().bottom())
            else:
                control.setX(self.boundingRect().left())
                control.setY(self.boundingRect().top() +
                             (self.boundingRect().height() / 2))

            self._controls.append(control)

        self.hideControlPoints(True)

        self.setPos(x, y)
        self.setAcceptHoverEvents(True)

    def hideControlPoints(self, hide: bool):
        for cont in self._controls:
            if hide:
                cont.hide()
            else:
                cont.show()

    def removeAnyConnections(self):
        for cp in self._controls:
            while len(cp.lines) > 0:
                line = cp.lines.pop()
                line.fromControlPoint.removeLine(line)
                line.toControlPoint.removeLine(line)
                self.scene().removeItem(line)

    def containsControlPoint(self, cp):
        for cont in self._controls:
            if cp == cont:
                return True
        return False

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            new_pos = value
            new_bounds = self.mapRectToScene(self.boundingRect()).translated(new_pos - self.pos())
            scene = self.scene()
            if scene and not scene.sceneRect().contains(new_bounds):
                scene.setSceneRect(scene.sceneRect().united(new_bounds))
        return super().itemChange(change, value)

class fmGraphicsItem(genericGraphicsItem):

    _w = 90
    _h = 40
    _label = None
    _vollabel = None
    _textColor = 'White'
    _text = ''
    _penColor = QColor(80, 126, 50)
    _brushColor = QColor(112, 173, 71)
    _outlineWidth = 3
    _inTrace = False

    def __init__(self, x, y, thisApp, fmName, parent=None):
        super().__init__(x, y, thisApp)

        self._text = fmName
        self._inTrace = False
        self.updateLabel()

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(QPen(self._penColor, self._outlineWidth))
        painter.setBrush(QBrush(self._brushColor))
        painter.drawRect(QRectF(0, 0, self._w, self._h))

    def updateLabel(self):
        if self._label is None:
            self._label = QGraphicsTextItem(self)
            # self._label = noContextMenuGraphicsTextItem(self)
            # self._label.setAcceptedMouseButtons(Qt.NoButton)
        self._label.setHtml(
            '<center><h2 style="color:' + self._textColor + ';">' + self._text + '</h2></center>')
        self._label.setTextWidth(self.boundingRect().width())
        rect = self._label.boundingRect()
        rect.moveCenter(self.boundingRect().center())
        self._label.setPos(rect.topLeft())

    def toggleVolumeLabel(self, aMainValue: float = 0, aDiffValue: float | None = None, toggleOn: bool = True):
        if toggleOn:
            if self._vollabel is None:
                self._vollabel = QGraphicsTextItem(self)
            if aDiffValue is None:
                aParentheticValue = ""
            elif aDiffValue < 0:
                aParentheticValue = f' <span style="color: red;">({aDiffValue:.2f}m³)</span>'
            else:
                aParentheticValue = f' ({aDiffValue:.2f}m³)'
            self._vollabel.setHtml(
                f'<h3><span style="color: black;">{aMainValue:.2f}m³</span>{aParentheticValue}</h3>')
            # self._vollabel.setTextWidth(self.boundingRect().width())
            rect = self._vollabel.boundingRect()
            rect.moveBottomLeft(self.boundingRect().topLeft())
            # rect.moveCenter(self.boundingRect().center())
            self._vollabel.setPos(rect.topLeft())
        else:
            if self._vollabel is not None:
                self.scene().removeItem(self._vollabel)
                self._vollabel = None

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()

class rgGraphicsItem(genericGraphicsItem):

    _w = 90
    _h = 40
    _label = None
    _textColor = 'Black'
    _text = ''
    _penColor = QColor(68, 114, 196)
    _brushColor = QColor(255, 255, 255)
    _outlineWidth = 3
    _inTrace = False

    def __init__(self, x, y, thisApp, rgName, parent=None):
        super().__init__(x, y, thisApp)

        self._text = rgName
        self._inTrace = False
        self.updateLabel()
        self.setCanConnect(False)

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(QPen(self._penColor, self._outlineWidth))
        painter.setBrush(QBrush(self._brushColor))
        painter.drawRect(0, 0, int(self._w), int(self._h))

    def updateLabel(self):
        if self._label is None:
            self._label = QGraphicsTextItem(self)
        self._label.setHtml(
            '<center><h2 style="color:' + self._textColor + ';">' + self._text + '</h2></center>')
        self._label.setTextWidth(self.boundingRect().width())
        rect = self._label.boundingRect()
        rect.moveCenter(self.boundingRect().center())
        self._label.setPos(rect.topLeft())


class csoGraphicsItem(genericGraphicsItem):

    _w = 20
    _h = 20
    _label = None
    _textColor = 'Black'
    _text = ''
    _penColor = QColor(0, 0, 0)
    _brushColor = QColor(255, 0, 0)
    _outlineWidth = 3
    _inTrace = False

    def __init__(self, x, y, thisApp, csoName, parent=None):
        super().__init__(x, y, thisApp)

        self._text = csoName
        self._inTrace = False
        self.updateLabel()

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(QPen(self._penColor, self._outlineWidth))
        painter.setBrush(QBrush(self._brushColor))
        painter.drawRect(0, 0, int(self._w), int(self._h))

    def updateLabel(self):
        if self._label is None:
            self._label = QGraphicsTextItem(self)
        self._label.setHtml(
            '<center><h2 style="color:' + self._textColor + ';">' + self._text + '</h2></center>')
        rect = self._label.boundingRect()
        rect.moveBottomLeft(self.boundingRect().topRight())
        self._label.setPos(rect.topLeft())

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()


class wwpsGraphicsItem(genericGraphicsItem):

    _w = 20
    _h = 20
    _label = None
    _textColor = 'Black'
    _text = ''
    _outlineWidth = 3
    combinedPen = QPen(QColor(0, 0, 0), _outlineWidth)
    foulPen = QPen(QColor(0, 0, 0), _outlineWidth)
    stormPen = QPen(QColor(0, 0, 0), _outlineWidth)
    combinedBrush = QBrush(QColor(255, 0, 0))
    foulBrush = QBrush(QColor(153, 102, 51))
    stormBrush = QBrush(QColor(0, 112, 192))
    _currentPen = combinedPen
    _currentBrush = combinedBrush
    _systemType = "COMB"
    _inTrace = False

    def __init__(self, x, y, thisApp, wwpsName, parent=None):
        super().__init__(x, y, thisApp)

        self._controls[1].setX(self._controls[1].x()-5)
        self._controls[3].setX(self._controls[3].x()+5)
        self._text = wwpsName
        self._inTrace = False
        self.updateLabel()

    def updateSystemType(self, systemType="COMB"):
        self._systemType = systemType
        if self._systemType == "COMB":
            self._currentPen = self.combinedPen
            self._currentBrush = self.combinedBrush
        elif self._systemType == "FOUL":
            self._currentPen = self.foulPen
            self._currentBrush = self.foulBrush
        else:
            self._currentPen = self.stormPen
            self._currentBrush = self.stormBrush

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def setPen(self, aPen):
        self._currentPen = aPen

    def setBrush(self, aBrush):
        self._currentBrush = aBrush

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(self._currentPen)
        painter.setBrush(self._currentBrush)
        # painter.drawPolygon(QPointF(0, int(self._h)), QPointF(
        #     int(self._w) / 2, 0), QPointF(int(self._w), int(self._h)))
        painter.drawPolygon([QPointF(0, int(self._h)), QPointF(int(self._w) / 2, 0), QPointF(int(self._w), int(self._h))])

    def updateLabel(self):
        if self._label is None:
            self._label = QGraphicsTextItem(self)
        self._label.setHtml(
            '<center><h3 style="color:' + self._textColor + ';">' + self._text + '</h3></center>')
        rect = self._label.boundingRect()
        rect.moveBottomLeft(self.boundingRect().topRight())
        self._label.setPos(rect.topLeft())

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()


class wwtwGraphicsItem(genericGraphicsItem):

    _w = 60
    _h = 30
    _label = None
    _wwtwLabel = None
    _textColor = 'Black'
    _text = ''
    _penColor = QColor(0, 0, 0)
    _brushColor = QColor(0, 0, 0)
    _outlineWidth = 3
    _inTrace = False

    def __init__(self, x, y, thisApp, wwtwName, parent=None):
        super().__init__(x, y, thisApp)

        self._text = wwtwName
        self._inTrace = False
        self.updateLabel()

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(QPen(self._penColor, self._outlineWidth))
        painter.setBrush(QBrush(self._brushColor))
        painter.drawRect(0, 0, int(self._w), int(self._h))

    def updateLabel(self):
        if self._label is None:
            self._label = QGraphicsTextItem(self)
        self._label.setHtml(
            '<center><h3 style="color:' + self._textColor + ';">' + self._text + '</h3></center>')
        rect = self._label.boundingRect()
        rect.moveBottomLeft(self.boundingRect().topRight())
        self._label.setPos(rect.topLeft())

        if self._wwtwLabel is None:
            self._wwtwLabel = QGraphicsTextItem(parent=self)
        self._wwtwLabel.setHtml(
            '<center><h5 style="color:White;">WwTW</h5></center>')
        self._wwtwLabel.setTextWidth(self.boundingRect().width())
        rect = self._wwtwLabel.boundingRect()
        rect.moveCenter(self.boundingRect().center())
        self._wwtwLabel.setPos(rect.topLeft())

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()


class juncGraphicsItem(genericGraphicsItem):

    _w = 12
    _h = 12
    _outlineWidth = 2
    combinedPen = QPen(QColor(0, 0, 0), _outlineWidth)
    foulPen = QPen(QColor(0, 0, 0), _outlineWidth)
    stormPen = QPen(QColor(0, 0, 0), _outlineWidth)
    combinedBrush = QBrush(QColor(255, 0, 0))
    foulBrush = QBrush(QColor(153, 102, 51))
    stormBrush = QBrush(QColor(0, 112, 192))
    _currentPen = combinedPen
    _currentBrush = combinedBrush
    _systemType = "COMB"
    _inTrace = False

    def __init__(self, x, y, thisApp, parent=None):
        super().__init__(x, y, thisApp)

        self._inTrace = False

    def updateSystemType(self, systemType="COMB"):
        self._systemType = systemType
        if self._systemType == "COMB":
            self._currentPen = self.combinedPen
            self._currentBrush = self.combinedBrush
        elif self._systemType == "FOUL":
            self._currentPen = self.foulPen
            self._currentBrush = self.foulBrush
        else:
            self._currentPen = self.stormPen
            self._currentBrush = self.stormBrush

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def setPen(self, aPen):
        self._currentPen = aPen

    def setBrush(self, aBrush):
        self._currentBrush = aBrush

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(self._currentPen)
        painter.setBrush(QBrush(self._currentBrush))
        painter.drawEllipse(0, 0, int(self._w), int(self._w))

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()


class outfallGraphicsItem(genericGraphicsItem):

    _w = 12
    _h = 12
    _outlineWidth = 3
    combinedPen = QPen(QColor(255, 0, 0), _outlineWidth)
    foulPen = QPen(QColor(153, 102, 51), _outlineWidth)
    stormPen = QPen(QColor(0, 112, 192), _outlineWidth)
    combinedBrush = QBrush(QColor(255, 0, 0, 0))
    foulBrush = QBrush(QColor(153, 102, 51, 0))
    stormBrush = QBrush(QColor(0, 112, 192, 0))
    _currentPen = combinedPen
    _currentBrush = combinedBrush
    _systemType = "COMB"
    _inTrace = False

    def __init__(self, x, y, thisApp, parent=None):
        super().__init__(x, y, thisApp)

        self._inTrace = False

    def updateSystemType(self, systemType="COMB"):
        self._systemType = systemType
        if self._systemType == "COMB":
            self._currentPen = self.combinedPen
            self._currentBrush = self.combinedBrush
        elif self._systemType == "FOUL":
            self._currentPen = self.foulPen
            self._currentBrush = self.foulBrush
        else:
            self._currentPen = self.stormPen
            self._currentBrush = self.stormBrush

    def boundingRect(self):
        return QRectF(-(self._outlineWidth / 2), -(self._outlineWidth / 2), self._w + self._outlineWidth, self._h + self._outlineWidth)

    def setPen(self, aPen):
        self._currentPen = aPen

    def setBrush(self, aBrush):
        self._currentBrush = aBrush

    def paint(self, painter, option, widget):
        if int(option.state) & QStyle.State_Selected:
            outline = QPen()
            outline.setColor(Qt.black)
            outline.setWidth(self._outlineWidth)
            outline.setDashPattern([2, 2])
            painter.setPen(outline)
        elif self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(self._currentPen)
        painter.setBrush(self._currentBrush)
        painter.drawEllipse(0, 0, int(self._w), int(self._w))

    def hoverEnterEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(False)
        else:
            self._thisApp.instance().setOverrideCursor(Qt.OpenHandCursor)

    def hoverLeaveEvent(self, event):
        if self.scene().views()[0]._curretSchematicTool == cstCONNECTION:
            self.hideControlPoints(True)
        else:
            self._thisApp.instance().restoreOverrideCursor()


class ControlPoint(QGraphicsEllipseItem):
    def __init__(self, parent):
        super().__init__(-5, -5, 10, 10, parent)

        self.lines = []
        # this flag **must** be set after creating self.lines!
        self.setFlags(self.ItemSendsScenePositionChanges)

    def addLine(self, lineItem):
        for existing in self.lines:
            if existing.controlPoints() == lineItem.controlPoints():
                # another line with the same control points already exists
                return False
        self.lines.append(lineItem)
        return True

    def removeLine(self, lineItem):
        for existing in self.lines:
            if existing.controlPoints() == lineItem.controlPoints():
                # self.scene().removeItem(existing)
                self.lines.remove(existing)
                return True
        return False

    def itemChange(self, change, value):
        for line in self.lines:
            # line.updatePath(self)
            line.updateLine(self)
        return super().itemChange(change, value)


class ConnectionPath(QtWidgets.QGraphicsPathItem):

    # fromControlPoint = None
    # toControlPoint = None
    # intermediateVertices = []
    # _sourcePoint = None
    # _destinationPoint = None
    _outlineWidth = 4
    # _currentPen = None
    combinedPen = QPen(QColor(255, 0, 0), _outlineWidth)
    foulPen = QPen(QColor(153, 102, 51), _outlineWidth)
    stormPen = QPen(QColor(0, 112, 192), _outlineWidth)
    combinedBrush = QBrush(QColor(255, 0, 0))
    foulBrush = QBrush(QColor(153, 102, 51))
    stormBrush = QBrush(QColor(0, 112, 192))
    _arrow_height = 10
    _arrow_width = 6
    # _systemType = "COMB"
    # _inTrace = False

    def __init__(self, sourceCP: Optional[ControlPoint]  = None, currentDynamicPoint: Optional[QtCore.QPointF] = None, *args, **kwargs):
        super(ConnectionPath, self).__init__(*args, **kwargs)

        self.fromControlPoint: Optional[ControlPoint] = sourceCP
        self.toControlPoint: Optional[ControlPoint] = None
        self.intermediateVertices = []
        self._sourcePoint: Optional[QtCore.QPointF] = sourceCP.scenePos()
        self._destinationPoint: Optional[QtCore.QPointF] = currentDynamicPoint
        # self._outlineWidth = 4
        self._currentPen: QPen = self.combinedPen
        # self._arrow_height = 10
        # self._arrow_width = 6
        self._systemType: str = "COMB"
        self._inTrace: bool = False
        self.setZValue(-1)

        self.setPath(self.directPath())

    def setSource(self, point: QtCore.QPointF):
        self._sourcePoint = point

    def setDestination(self, point: QtCore.QPointF, toCP: ControlPoint | None = None):
        if toCP is not None:
            self.toControlPoint = toCP
            self._destinationPoint = toCP.scenePos()
        else:
            self._destinationPoint = point

    def addVertex(self, point: QtCore.QPointF):
        self.intermediateVertices.append(point)

    def directPath(self):
        path = QtGui.QPainterPath(self._sourcePoint)
        for i in range(len(self.intermediateVertices)):
            pPoint = self.intermediateVertices[i]
            path.lineTo(pPoint)
        path.lineTo(self._destinationPoint)
        return path

    def updateLine(self, source):
        oldSourcePoint = self._sourcePoint
        oldDestinationPoint = self._destinationPoint

        if source == self.fromControlPoint:
            self.setSource(source.scenePos())
            self.updateIntermediateVertices(
                True, oldSourcePoint, oldDestinationPoint)
        else:
            self.setDestination(source.scenePos())
            self.updateIntermediateVertices(
                False, oldSourcePoint, oldDestinationPoint)

    def updateIntermediateVertices(self, sourceMoved, oldSource, oldDestination):

        orig_dx = oldDestination.x() - oldSource.x()
        orig_dy = oldDestination.y() - oldSource.y()

        new_dx = self._destinationPoint.x() - self._sourcePoint.x()
        new_dy = self._destinationPoint.y() - self._sourcePoint.y()

        if (orig_dx != new_dx) or (orig_dy != new_dy):
            for i in range(len(self.intermediateVertices)):

                int_dx = self.intermediateVertices[i].x() - oldSource.x()
                int_dy = self.intermediateVertices[i].y() - oldSource.y()

                fx = 0
                fy = 0

                if orig_dx != 0:
                    fx = int_dx / orig_dx
                if orig_dy != 0:
                    fy = int_dy / orig_dy

                dx = new_dx * fx
                dy = new_dy * fy

                self.intermediateVertices[i].setX(self._sourcePoint.x() + dx)
                self.intermediateVertices[i].setY(self._sourcePoint.y() + dy)

    def controlPoints(self):
        return self.fromControlPoint, self.toControlPoint

    def updateSystemType(self, systemType="COMB"):
        self._systemType = systemType
        if self._systemType == "COMB":
            self._currentPen = self.combinedPen
        elif self._systemType == "FOUL":
            self._currentPen = self.foulPen
        else:
            self._currentPen = self.stormPen

    def arrowCalc(self, start_point=None, myAngle=0):

        try:
            myAngle = math.pi - math.radians(myAngle)

            normX = math.cos(myAngle)
            normY = math.sin(myAngle)

            # perpendicular vector
            perpX = -normY
            perpY = normX

            leftX = start_point.x() + self._arrow_height * normX + self._arrow_width * perpX
            leftY = start_point.y() + self._arrow_height * normY + self._arrow_width * perpY

            rightX = start_point.x() + self._arrow_height * normX - self._arrow_width * perpX
            rightY = start_point.y() + self._arrow_height * normY - self._arrow_width * perpY

            point2 = QtCore.QPointF(leftX, leftY)
            point3 = QtCore.QPointF(rightX, rightY)

            return QtGui.QPolygonF([point2, start_point, point3])

        except (ZeroDivisionError, Exception):
            return None

    def paint(self, painter, option, widget):
        painter.setRenderHint(painter.Antialiasing)
        if self._inTrace:
            traceOutline = QPen()
            traceOutline.setColor(Qt.green)
            traceOutline.setWidth(self._outlineWidth + 2)
            painter.setPen(traceOutline)
        else:
            painter.setPen(self._currentPen)
        painter.setBrush(QtCore.Qt.NoBrush)

        path = self.directPath()
        painter.drawPath(path)
        self.setPath(path)

        triangle_source = self.arrowCalc(
            path.pointAtPercent(0.5), path.angleAtPercent(0.5))

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)

class SchematicGraphicsScene(QGraphicsScene):
    currentlyPrinting = False

    def __init__(self, parent):
        super().__init__(parent)

    def dragEnterEvent(self, e):
        e.acceptProposedAction()

    def dropEvent(self, e):
        e.acceptProposedAction()

    def dragMoveEvent(self, e):
        e.acceptProposedAction()

    def addItem(self, item):
        super().addItem(item)
        item_rect = item.sceneBoundingRect()
        if not self.sceneRect().contains(item_rect):
            new_rect = self.sceneRect().united(item_rect)
            self.setSceneRect(new_rect)

    # def drawBackground(self, painter, rect):
    #     super().drawBackground(painter, rect)
    #     # Draw a red border around the current scene rect
    #     pen = QPen(QColor("red"))
    #     pen.setWidth(2)
    #     painter.setPen(pen)
    #     painter.drawRect(self.sceneRect())
        
# from PyQt5.QtWidgets import QGraphicsScene
# from PyQt5.QtCore import QRectF
# from PyQt5.QtGui import QPen, QColor

# class CustomGraphicsScene(QGraphicsScene):
#     def __init__(self, parent=None):
#         super().__init__(parent)



class SchematicGraphicsView(QGraphicsView):

    _zoom = 0
    _scene = None
    _contextMenuClickPos = None
    _itemNumber = 0
    _rgItemNumber = 0
    _panning = False
    _origin = None
    _anchorMode = 0
    _curretSchematicTool = ''
    _currentContextItem = None

    def __init__(self, parent):
        super(SchematicGraphicsView, self).__init__(parent)

        self._thisApp: Optional[QApplication] = None
        self.createNewScene()
        self.setAcceptDrops(True)
        self.setDragMode(self.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(self.ViewportUpdateMode.FullViewportUpdate)

        self._isdrawingPath: bool = False
        self._current_path: Optional[ConnectionPath] = None
        self._currentTrace: List = []
        self.startItem: Optional[ControlPoint] = None

        self._currentEvent: Optional[surveyEvent] = None
        self.overlayLabel = QLabel("Full Period", self)
        self.overlayLabel.setStyleSheet("background-color: rgba(0, 0, 0, 127); color: white; padding: 5px;")
        self.overlayLabel.setFixedSize(250, 30)  # Set a fixed size
        self.updateOverlayLabel()

    def resizeEvent(self, event):
        """ Update label position when the view is resized """
        super().resizeEvent(event)
        self.updateOverlayLabel()

    def updateOverlayLabel(self):
        """ Position the overlay label in the bottom-left corner """
        margin = 20  # Padding from the edge
        self.overlayLabel.move(int(margin / 2), self.height() - self.overlayLabel.height() - margin)

    def addEvent(self, se: surveyEvent):
        self._currentEvent = se
        event_label = f"{se.eventName}: {se.eventStart.strftime('%d/%m/%Y %H:%M')} - {se.eventEnd.strftime('%d/%m/%Y %H:%M')}"
        self.overlayLabel.setText(event_label)
        self.updateOverlayLabel()
        self.volumeBalance(True)

    def removeEvent(self):
        self._currentEvent = None
        self.overlayLabel.setText("Full Period")
        self.updateOverlayLabel()
        self.volumeBalance(True)

    def createNewScene(self):
        self._scene = SchematicGraphicsScene(self)
        self._scene.setSceneRect(0, 0, 3200, 1800)
        self.setScene(self._scene)

        # # Create a rectangle item for the scene outline
        # rect_item = QGraphicsRectItem(self._scene.sceneRect())
        
        # # Set the pen for the rectangle (red color, 2 pixels wide)
        # pen = QPen(QColor(255, 0, 0))  # Red color
        # pen.setWidth(2)  # Set the width of the outline
        # rect_item.setPen(pen)
        
        # # Optionally, set the brush to transparent if you want just the outline
        # rect_item.setBrush(Qt.transparent)
        
        # # Add the rectangle item to the scene
        # self._scene.addItem(rect_item)        

    def getSchematicGraphicsItemAt(self, pPointF, searchBuffer):

        pTlPoint = QPointF(pPointF.x()-(searchBuffer/2),
                           pPointF.y()+(searchBuffer/2))
        pBrPoint = QPointF(pPointF.x()+(searchBuffer/2),
                           pPointF.y()-(searchBuffer/2))
        pRectF = QRectF(pTlPoint, pBrPoint)

        itemList = self.scene().items(pRectF)
        for item in itemList:
            if type(item).__name__ in ['fmGraphicsItem', 'rgGraphicsItem', 'juncGraphicsItem', 'outfallGraphicsItem',
                                       'csoGraphicsItem', 'wwpsGraphicsItem', 'wwtwGraphicsItem', 'ConnectionPath']:
                return item
        return None

    def getSchematicFlowMonitors(self):
        fmItems = []
        for item in self.items():
            if isinstance(item, fmGraphicsItem):
                fmItems.append(item._text)
        return fmItems

    def getSchematicFlowMonitorsByName(self, fmName):
        for item in self.items():
            if isinstance(item, fmGraphicsItem):
                if item._text == fmName:
                    return item
        return None

    def getSchematicRainGaugeByName(self, rgName):
        for item in self.items():
            if isinstance(item, rgGraphicsItem):
                if item._text == rgName:
                    return item
        return None

    def contextMenuEvent(self, event):
        menu = None

        self._currentContextItem = self.getSchematicGraphicsItemAt(
            self.mapToScene(event.pos()), 5)

        if self._currentContextItem is not None:
            menu = QMenu()
            if any(isinstance(self._currentContextItem, cls) for cls in (wwpsGraphicsItem, csoGraphicsItem, wwtwGraphicsItem)):
                aCallback = QAction("Edit Label", menu)
                aCallback.triggered.connect(self.schematicEditLabel)
                menu.addAction(aCallback)

            if isinstance(self._currentContextItem, ConnectionPath):
                aCallback = QAction("Delete Connection", menu)
                aCallback.triggered.connect(self.schematicDeleteConnection)
                menu.addAction(aCallback)
                subMenuSysType = QtWidgets.QMenu(menu)
                subMenuSysType.setTitle("Set System Type:")
                menu.addAction(subMenuSysType.menuAction())
                aCallback = QAction("Combined", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeComb)
                subMenuSysType.addAction(aCallback)
                aCallback = QAction("Foul", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeFoul)
                subMenuSysType.addAction(aCallback)
                aCallback = QAction("Storm", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeStorm)
                subMenuSysType.addAction(aCallback)

            if any(isinstance(self._currentContextItem, cls) for cls in (fmGraphicsItem, rgGraphicsItem, juncGraphicsItem,
                                                                         outfallGraphicsItem, wwpsGraphicsItem,
                                                                         csoGraphicsItem, wwtwGraphicsItem)):
                aCallback = QAction("Delete", menu)
                aCallback.triggered.connect(self.schematicDeleteItem)
                menu.addAction(aCallback)
                subMenuSysType = QtWidgets.QMenu(menu)

            if any(isinstance(self._currentContextItem, cls) for cls in (juncGraphicsItem, outfallGraphicsItem, wwpsGraphicsItem)):
                subMenuSysType = QtWidgets.QMenu(menu)
                subMenuSysType.setTitle("Set System Type:")
                menu.addAction(subMenuSysType.menuAction())
                aCallback = QAction("Combined", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeComb)
                subMenuSysType.addAction(aCallback)
                aCallback = QAction("Foul", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeFoul)
                subMenuSysType.addAction(aCallback)
                aCallback = QAction("Storm", subMenuSysType)
                aCallback.triggered.connect(self.schematicSetSystemTypeStorm)
                subMenuSysType.addAction(aCallback)

            if isinstance(self._currentContextItem, fmGraphicsItem):
                aCallback = QAction("US Trace", menu)
                aCallback.triggered.connect(
                    lambda: self.schematicFMUSTrace(None, False))
                menu.addAction(aCallback)
                aCallback = QAction("DS Trace", menu)
                aCallback.triggered.connect(self.schematicFMDSTrace)
                menu.addAction(aCallback)
                aCallback = QAction("Check Volume Balance", menu)
                aCallback.triggered.connect(self.volumeBalance)
                menu.addAction(aCallback)
        else:
            if len(self._currentTrace) > 0:
                menu = QMenu()
                aCallback = QAction("Clear Trace", menu)
                aCallback.triggered.connect(self.clearCurrentTrace)
                menu.addAction(aCallback)

            if self._currentEvent is not None:
                if menu is None:
                    menu = QMenu()
                aCallback = QAction("Remove Event", menu)
                aCallback.triggered.connect(self.removeEvent)
                menu.addAction(aCallback)

            # if menu is None:
            #         menu = QMenu()
            # aCallback = QAction("Toggle Volume Balance", menu)
            # aCallback.triggered.connect(self.toggleVolumeBalance)
            # menu.addAction(aCallback)

        if menu is not None:
            if not len(menu.actions()) == 0:
                self._contextMenuClickPos = self.mapToScene(event.pos())
                menu.exec_(self.mapToGlobal(event.pos()))
                self._contextMenuClickPos = None
                self._currentContextItem = None

    # def toggleVolumeBalance(self):
    #     self.showVolumeBalance = not self.showVolumeBalance

    #     # if update:
    #     #     if self._currentTrace is not None:
    #     #         self._currentContextItem = self._currentTrace[0]
    #     # else:
    #     #     self.schematicFMUSTrace(stopAtFM=True)

    #     if self._currentEvent is not None:
    #         startDate = self._currentEvent.eventStart
    #         endDate = self._currentEvent.eventEnd

    #     for item in self.scene().items():
    #         if isinstance(item, fmGraphicsItem):
    #             fmVolume = 0
    #             fm = self._thisApp.activeWindow().openFlowMonitors.getFlowMonitor(item._text)

    #             if self._currentEvent is None:
    #                 startDate = fm.dateRange[0]
    #                 endDate = fm.dateRange[len(fm.dateRange)-1]

    #             fmVolume += fm.getFlowVolumeBetweenDates(startDate, endDate)

    #             self.schematicFMUSTrace(stopAtFM=True)                

    #             cumUsVolume = 0
    #             incUsVolume = 0
    #             hasUSFM = False
    #             for item in self._currentTrace:
    #                 if isinstance(item, fmGraphicsItem):
    #                     if item is not self._currentContextItem:
    #                         hasUSFM = True
    #                         fm = self._thisApp.activeWindow().openFlowMonitors.getFlowMonitor(item._text)
    #                         incUsVolume = fm.getFlowVolumeBetweenDates(startDate, endDate)
    #                         cumUsVolume += incUsVolume
    #                         item.toggleVolumeLabel(incUsVolume)

    #             volDiff = fmVolume - cumUsVolume
    #             if hasUSFM:
    #                 self._currentContextItem.toggleVolumeLabel(fmVolume, volDiff)
    #             else:
    #                 self._currentContextItem.toggleVolumeLabel(fmVolume)        

    def clearCurrentTrace(self):
        for item in self._currentTrace:
            item._inTrace = False
            if isinstance(item, fmGraphicsItem):
                item.toggleVolumeLabel(toggleOn=False)
        self._currentTrace = []
        self.viewport().repaint()

    # def getFMUS(self, fmName):
    #     currentTrace = self._currentTrace
    #     self.clearCurrentTrace()

    #     itemsInTrace = []
    #     itemsToTrace = []
    #     currentItem = self.getSchematicFlowMonitorsByName(fmName)
    #     if currentItem is not None:
    #         itemsToTrace.append(self._currentContextItem)

    #     while len(itemsToTrace) > 0:
    #         traceItem = itemsToTrace.pop()
    #         itemsInTrace.append(traceItem)
    #         traceItem._inTrace = True
    #         if isinstance(traceItem, ConnectionPath):
    #             cp = traceItem.fromControlPoint
    #             item = self.getItemByControlPoint(cp)
    #             if not item._inTrace:
    #                 if isinstance(item, fmGraphicsItem) and stopAtFM:
    #                     itemsInTrace.append(item)
    #                     item._inTrace = True
    #                 else:
    #                     itemsToTrace.append(item)
    #         else:
    #             for cp in traceItem._controls:
    #                 usConns = self.getIncomingConnections(cp)
    #                 if len(usConns) > 0:
    #                     for conn in usConns:
    #                         if not conn._inTrace:
    #                             itemsToTrace.append(conn)

    #     self._currentTrace = itemsInTrace
    #     self.viewport().repaint()

    def schematicFMUSTrace(self, fmName=None, stopAtFM=False):
        self.clearCurrentTrace()
        itemsInTrace = []
        itemsToTrace = []
        if fmName is not None:
            self._currentContextItem = self.getSchematicFlowMonitorsByName(
                fmName)
        if self._currentContextItem is not None:
            itemsToTrace.append(self._currentContextItem)

        while len(itemsToTrace) > 0:
            traceItem = itemsToTrace.pop()
            itemsInTrace.append(traceItem)
            traceItem._inTrace = True
            if isinstance(traceItem, ConnectionPath):
                cp = traceItem.fromControlPoint
                item = self.getItemByControlPoint(cp)
                if not item._inTrace:
                    if isinstance(item, fmGraphicsItem) and stopAtFM:
                        itemsInTrace.append(item)
                        item._inTrace = True
                    else:
                        itemsToTrace.append(item)
            else:
                for cp in traceItem._controls:
                    usConns = self.getIncomingConnections(cp)
                    if len(usConns) > 0:
                        for conn in usConns:
                            if not conn._inTrace:
                                itemsToTrace.append(conn)

        self._currentTrace = itemsInTrace
        self.viewport().repaint()

    def schematicFMDSTrace(self):
        self.clearCurrentTrace()
        itemsInTrace = []
        itemsToTrace = []
        itemsToTrace.append(self._currentContextItem)

        while len(itemsToTrace) > 0:
            traceItem = itemsToTrace.pop()
            itemsInTrace.append(traceItem)
            traceItem._inTrace = True
            if isinstance(traceItem, ConnectionPath):
                cp = traceItem.toControlPoint
                item = self.getItemByControlPoint(cp)
                if not item._inTrace:
                    itemsToTrace.append(item)
            else:
                for cp in traceItem._controls:
                    dsConns = self.getOutgoingConnections(cp)
                    if len(dsConns) > 0:
                        for conn in dsConns:
                            if not conn._inTrace:
                                itemsToTrace.append(conn)

        self._currentTrace = itemsInTrace
        self.viewport().repaint()

    def getItemByControlPoint(self, cp):
        for item in self.scene().items():
            if isinstance(item, genericGraphicsItem):
                if item.containsControlPoint(cp):
                    return item
        return None

    def getIncomingConnections(self, cp):
        icList = []
        for line in cp.lines:
            if line.toControlPoint == cp:
                icList.append(line)
        return icList

    def getOutgoingConnections(self, cp):
        ogList = []
        for line in cp.lines:
            if line.fromControlPoint == cp:
                ogList.append(line)
        return ogList

    def volumeBalance(self, update:bool = False):

        if update:
            if self._currentTrace is not None:
                self._currentContextItem = self._currentTrace[0]
        else:
            self.schematicFMUSTrace(stopAtFM=True)

        fmVolume = 0
        fm = self._thisApp.activeWindow().openFlowMonitors.getFlowMonitor(
            self._currentContextItem._text)

        startDate = fm.dateRange[0]
        endDate = fm.dateRange[len(fm.dateRange)-1]

        if self._currentEvent is not None:
            startDate = self._currentEvent.eventStart
            endDate = self._currentEvent.eventEnd

        fmVolume += fm.getFlowVolumeBetweenDates(startDate, endDate)

        cumUsVolume = 0
        incUsVolume = 0
        hasUSFM = False
        for item in self._currentTrace:
            if isinstance(item, fmGraphicsItem):
                if item is not self._currentContextItem:
                    hasUSFM = True
                    fm = self._thisApp.activeWindow().openFlowMonitors.getFlowMonitor(item._text)
                    incUsVolume = fm.getFlowVolumeBetweenDates(startDate, endDate)
                    cumUsVolume += incUsVolume
                    item.toggleVolumeLabel(incUsVolume)

        volDiff = fmVolume - cumUsVolume
        if hasUSFM:
            self._currentContextItem.toggleVolumeLabel(fmVolume, volDiff)
        else:
            self._currentContextItem.toggleVolumeLabel(fmVolume)

    def schematicEditLabel(self):
        newLabel, hitOK = QInputDialog.getText(
            self, "Edit Label", "Label:", QLineEdit.Normal, str(self._currentContextItem._text))
        if hitOK:
            self._currentContextItem._text = newLabel
            self._currentContextItem.updateLabel()

    def printSchematic(self):
        printDlg = QPrintPreviewDialog(self)
        printDlg.setWindowFlags(Qt.Window)
        printDlg.paintRequested.connect(self.paintRequest)
        printDlg.exec_()

    def paintRequest(self, printer):
        self._scene.currentlyPrinting = True
        self.render(QPainter(printer))
        self._scene.currentlyPrinting = False

    def addFlowMonitor(self, fmName: str, position, offset):
        testFm = fmGraphicsItem(position.x() + offset,
                                position.y() + offset, self._thisApp, fmName)
        self.scene().addItem(testFm)
        return testFm

    def addRaingauge(self, rgName, position, offset):
        testRg = rgGraphicsItem(position.x() + offset,
                                position.y() + offset, self._thisApp, rgName)
        self.scene().addItem(testRg)
        return testRg

    def addWwPS(self, wwpsName, position, systemType="COMB"):
        testWwps = wwpsGraphicsItem(
            position.x(), position.y(), self._thisApp, wwpsName)
        self.scene().addItem(testWwps)
        testWwps.updateSystemType(systemType)
        self.viewport().repaint()

    def addCSO(self, csoName, position):
        testCso = csoGraphicsItem(
            position.x(), position.y(), self._thisApp, csoName)
        self.scene().addItem(testCso)

    def addWwTW(self, wwtwName, position):
        testWwtw = wwtwGraphicsItem(
            position.x(), position.y(), self._thisApp, wwtwName)
        self.scene().addItem(testWwtw)

    def addJunction(self, juncName, position, systemType="COMB"):
        testJunc = juncGraphicsItem(
            position.x(), position.y(), self._thisApp, juncName)
        self.scene().addItem(testJunc)
        testJunc.updateSystemType(systemType)
        self.viewport().repaint()

    def addOutfall(self, outfallName, position, systemType="COMB"):
        testOutfall = outfallGraphicsItem(
            position.x(), position.y(), self._thisApp, outfallName)
        self.scene().addItem(testOutfall)
        testOutfall.updateSystemType(systemType)
        self.viewport().repaint()

    def schematicDeleteItem(self):
        if len(self.scene().selectedItems()) > 0:
            for gItem in self.scene().selectedItems():
                self.deleteItem(gItem)
        else:
            self.deleteItem(self._currentContextItem)

    def deleteItem(self, gItem):
        if not isinstance(gItem, ConnectionPath):
            gItem.removeAnyConnections()
            if isinstance(gItem, fmGraphicsItem):
                fm = self._thisApp.activeWindow().openFlowMonitors.getFlowMonitor(
                    gItem._text)
                fm._schematicGraphicItem = None
            elif isinstance(gItem, rgGraphicsItem):
                rg = self._thisApp.activeWindow().openRainGauges.getRainGauge(
                    gItem._text)
                rg._schematicGraphicItem = None
            self.scene().removeItem(gItem)

    def schematicDeleteConnection(self):
        if isinstance(self._currentContextItem, ConnectionPath):
            self._currentContextItem.fromControlPoint.removeLine(
                self._currentContextItem)
            self._currentContextItem.toControlPoint.removeLine(
                self._currentContextItem)
            self.scene().removeItem(self._currentContextItem)

    def schematicSetSystemTypeComb(self):
        self._currentContextItem.updateSystemType("COMB")
        self.viewport().repaint()

    def schematicSetSystemTypeFoul(self):
        self._currentContextItem.updateSystemType("FOUL")
        self.viewport().repaint()

    def schematicSetSystemTypeStorm(self):
        self._currentContextItem.updateSystemType("STORM")
        self.viewport().repaint()

    def controlPointAt(self, pos):
        mask = QPainterPath()
        mask.setFillRule(Qt.WindingFill)
        for item in self.scene().items(pos):
            if mask.contains(pos):
                # ignore objects hidden by others
                return
            if isinstance(item, ControlPoint):
                return item

    def connectionAt(self, pos):
        mask = QPainterPath()
        mask.setFillRule(Qt.WindingFill)
        for item in self.scene().items(pos):
            if mask.contains(pos):
                # ignore objects hidden by others
                return
            if isinstance(item, ConnectionPath):
                return item

    def clearAllVisibleControlPoints(self):
        for item in self.scene().items():
            if isinstance(item, genericGraphicsItem):
                item.hideControlPoints(True)

    def showAllVisibleControlPoints(self):
        for item in self.scene().items():
            if isinstance(item, genericGraphicsItem):
                item.hideControlPoints(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._thisApp.instance().setOverrideCursor(Qt.ClosedHandCursor)
            self._anchorMode = self.transformationAnchor()
            self.setTransformationAnchor(QGraphicsView.NoAnchor)
            self.setDragMode(QGraphicsView.NoDrag)
            self._origin = event.pos()
            self._panning = True
        elif event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            if self._curretSchematicTool == cstWWPS:
                self.addWwPS('', self.mapToScene(event.pos()))
            elif self._curretSchematicTool == cstCSO:
                self.addCSO('', self.mapToScene(event.pos()))
            elif self._curretSchematicTool == cstJUNCTION:
                self.addJunction('', self.mapToScene(event.pos()))
            elif self._curretSchematicTool == cstOUTFALL:
                self.addOutfall('', self.mapToScene(event.pos()))
            elif self._curretSchematicTool == cstWWTW:
                self.addWwTW('', self.mapToScene(event.pos()))
            elif self._curretSchematicTool == cstCONNECTION:
                if self._isdrawingPath:
                    item = self.controlPointAt(self.mapToScene(event.pos()))
                    if item and item != self.startItem:
                        self._current_path.setDestination(item.scenePos(), item)
                        if self.startItem:
                            if self.startItem.addLine(self._current_path):
                                item.addLine(self._current_path)
                        else:
                            pass
                        self._isdrawingPath = False
                        self._current_path = None
                        self.startItem = self._current_path = None
                        self.clearAllVisibleControlPoints()
                    else:
                        self._current_path.addVertex(self.mapToScene(event.pos()))
                    self.viewport().repaint()
                else:
                    self.setDragMode(QGraphicsView.NoDrag)
                    if event.button() == Qt.LeftButton:
                        item = self.controlPointAt(self.mapToScene(event.pos()))
                        if item:
                            self.startItem = item
                            pos = self.mapToScene(event.pos())
                            self._isdrawingPath = True
                            self._current_path = ConnectionPath(
                                sourceCP=item, currentDynamicPoint=pos)
                            self.scene().addItem(self._current_path)
                            self.viewport().repaint()
                            return

            else:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        super(SchematicGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            oldP = self._origin
            newP = event.pos()
            translation = newP - oldP

            self.translate(translation.x(), translation.y())
            self._origin = event.pos()

        if self._curretSchematicTool == cstCONNECTION:

            if self._current_path:
                self.clearAllVisibleControlPoints()
                for item in self.scene().items(self.mapToScene(event.pos())):
                    if isinstance(item, genericGraphicsItem):
                        if item.canConnect:
                            item.hideControlPoints(False)
                item = self.controlPointAt(self.mapToScene(event.pos()))
                if (item and item != self.startItem):
                    p2 = item.scenePos()
                else:
                    p2 = self.mapToScene(event.pos())

                self._current_path.setDestination(p2)

                self.viewport().repaint()
                return

        super(SchematicGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._thisApp.instance().restoreOverrideCursor()
            self.setTransformationAnchor(self._anchorMode)
            self._panning = False

        self.setDragMode(QGraphicsView.RubberBandDrag)

        super(SchematicGraphicsView, self).mouseReleaseEvent(event)

    # def wheelEvent(self, event):
    #     if event.angleDelta().y() > 0:
    #         factor = 1.25
    #         self._zoom += 1
    #     else:
    #         factor = 0.75
    #         self._zoom -= 1

    #     if self._zoom == 0:
    #         self.scale(1, 1)

    #     self.scale(factor, factor)

    # def wheelEvent(self, event):
    #     # Get the cursor position in scene coordinates
    #     cursor_pos = self.mapToScene(event.pos())

    #     if event.angleDelta().y() > 0:
    #         factor = 1.25
    #         self._zoom += 1
    #     else:
    #         factor = 0.75
    #         self._zoom -= 1

    #     # Prevent zooming out too much
    #     if self._zoom < 0:
    #         self._zoom = 0

    #     # Save the current transformation
    #     self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    #     self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    #     # Scale the view
    #     self.scale(factor, factor)

    #     # Get the new cursor position in the view after scaling
    #     new_cursor_pos = self.mapToScene(event.pos())

    #     # Calculate the difference in position
    #     delta = new_cursor_pos - cursor_pos

    #     # Adjust the view to keep the cursor position the same
    #     self.translate(delta.x(), delta.y())
    
    def wheelEvent(self, event):
        # Get the cursor position in scene coordinates
        cursor_pos = self.mapToScene(event.pos())

        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.75
            self._zoom -= 1

        # Prevent zooming out too much
        if self._zoom < 0:
            self._zoom = 0

        # Scale the view
        self.scale(factor, factor)

        # Get the new cursor position in the scene after scaling
        new_cursor_pos = self.mapToScene(event.pos())

        # Calculate the difference in position
        delta = new_cursor_pos - cursor_pos

        # Adjust the view to keep the cursor position the same
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + int(-delta.x()))
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + int(-delta.y()))