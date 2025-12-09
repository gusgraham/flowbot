"""
Custom QGraphicsItem classes for the graphical CSO editor.

This module provides graphical representations of CSOs and their downstream links.
"""

from PyQt6.QtWidgets import (QMenu, QMessageBox, QGraphicsItem,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsPathItem)
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QPolygonF
from typing import Optional, Dict, Any


class CSOGraphicsItem(QGraphicsRectItem):
    """
    Graphical representation of a CSO node.

    Features:
    - Displays CSO name
    - Draggable
    - Stores CSO properties
    - Context menu for editing/deleting
    """

    def __init__(self, cso_name: str, x: float, y: float, size: float = 60):
        """
        Initialize CSO node.

        Args:
            cso_name: Name of the CSO
            x: X position
            y: Y position
            size: Node size (width and height)
        """
        super().__init__(-size/2, -size/2, size, size)

        self.cso_name = cso_name
        self.size = size
        self.downstream_links = []  # List of CSOLinkGraphicsItem
        self.upstream_links = []    # List of CSOLinkGraphicsItem

        # Positioning
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        # Appearance
        self.setBrush(QBrush(QColor(100, 150, 255)))
        self.setPen(QPen(QColor(0, 0, 0), 2))

        # Add text label
        self.label = QGraphicsTextItem(cso_name, self)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)
        self.label.setPos(-self.label.boundingRect().width() / 2,
                          -self.label.boundingRect().height() / 2)

        self.setAcceptHoverEvents(True)
        self.setZValue(1)  # Ensure nodes are above links

    def itemChange(self, change, value):
        """Update connected links when node is moved."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update all connected links
            for link in self.downstream_links + self.upstream_links:
                link.update_position()
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setBrush(QBrush(QColor(120, 170, 255)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Remove highlight on hover exit."""
        self.setBrush(QBrush(QColor(100, 150, 255)))
        super().hoverLeaveEvent(event)

    def add_downstream_link(self, link):
        """Register a downstream link."""
        if link not in self.downstream_links:
            self.downstream_links.append(link)

    def add_upstream_link(self, link):
        """Register an upstream link."""
        if link not in self.upstream_links:
            self.upstream_links.append(link)

    def remove_downstream_link(self, link):
        """Remove a downstream link."""
        if link in self.downstream_links:
            self.downstream_links.remove(link)

    def remove_upstream_link(self, link):
        """Remove an upstream link."""
        if link in self.upstream_links:
            self.upstream_links.remove(link)

    def contextMenuEvent(self, event):
        """Show context menu for node operations."""
        menu = QMenu()
        delete_action = menu.addAction("Delete CSO")

        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.delete_node()

    def delete_node(self):
        """Delete this node and all connected links."""
        # Remove all connected links
        # Copy list to avoid modification during iteration
        for link in self.downstream_links[:]:
            link.delete_link()
        for link in self.upstream_links[:]:
            link.delete_link()

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)


class CSOLinkGraphicsItem(QGraphicsPathItem):
    """
    Graphical representation of a downstream link between CSOs.

    Features:
    - Displays as arrow from upstream to downstream CSO
    - Stores link properties (distance, velocity, max PFF)
    - Context menu for editing/deleting
    """

    def __init__(self, upstream_cso: CSOGraphicsItem, downstream_cso: CSOGraphicsItem,
                 distance: float = 0, velocity: float = 0, max_pff: Optional[float] = None):
        """
        Initialize CSO link.

        Args:
            upstream_cso: Source CSO node
            downstream_cso: Target CSO node
            distance: Distance in meters
            velocity: Average velocity in m/s
            max_pff: Maximum pass-forward flow in m3/s (optional)
        """
        super().__init__()

        self.upstream_cso = upstream_cso
        self.downstream_cso = downstream_cso
        self.distance = distance
        self.velocity = velocity
        self.max_pff = max_pff

        # Register with connected nodes
        upstream_cso.add_downstream_link(self)
        downstream_cso.add_upstream_link(self)

        # Appearance
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(0)  # Ensure links are below nodes

        self.update_position()

    def update_position(self):
        """Update the link path based on node positions."""
        # Get node positions
        start_pos = self.upstream_cso.pos()
        end_pos = self.downstream_cso.pos()

        # Calculate line direction
        line = QLineF(start_pos, end_pos)

        # Offset from node centers to node edges
        angle = line.angle() * 3.14159 / 180.0
        dx = self.upstream_cso.size / 2 * 0.9
        dy = self.downstream_cso.size / 2 * 0.9

        # Adjust start and end to be at node edges
        start_offset = QPointF(dx * line.dx() / line.length(),
                               dx * line.dy() / line.length())
        end_offset = QPointF(dy * line.dx() / line.length(),
                             dy * line.dy() / line.length())

        line_start = start_pos + start_offset
        line_end = end_pos - end_offset

        # Create path with arrow
        path = QPainterPath()
        path.moveTo(line_start)
        path.lineTo(line_end)

        # Add arrowhead
        arrow_size = 15
        line_adjusted = QLineF(line_start, line_end)
        angle = line_adjusted.angle()

        # Calculate arrowhead points
        arrow_p1 = line_end + QPointF(
            arrow_size * 0.866 * (-line_adjusted.dx() / line_adjusted.length() +
                                  0.5 * line_adjusted.dy() / line_adjusted.length()),
            arrow_size * 0.866 * (-line_adjusted.dy() / line_adjusted.length() -
                                  0.5 * line_adjusted.dx() / line_adjusted.length())
        )
        arrow_p2 = line_end + QPointF(
            arrow_size * 0.866 * (-line_adjusted.dx() / line_adjusted.length() -
                                  0.5 * line_adjusted.dy() / line_adjusted.length()),
            arrow_size * 0.866 * (-line_adjusted.dy() / line_adjusted.length() +
                                  0.5 * line_adjusted.dx() / line_adjusted.length())
        )

        # Create arrowhead polygon
        arrow_head = QPolygonF([line_end, arrow_p1, arrow_p2])
        path.addPolygon(arrow_head)

        self.setPath(path)

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setPen(QPen(QColor(255, 100, 0), 3))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Remove highlight on hover exit."""
        self.setPen(QPen(QColor(0, 0, 0), 2))
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu for link operations."""
        menu = QMenu()
        edit_action = menu.addAction("Edit Link Properties")
        delete_action = menu.addAction("Delete Link")

        action = menu.exec(event.screenPos())
        if action == edit_action:
            self.edit_properties()
        elif action == delete_action:
            self.delete_link()

    def edit_properties(self):
        """Open dialog to edit link properties."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox

        dialog = QDialog()
        dialog.setWindowTitle(
            f"Edit Link: {self.upstream_cso.cso_name} → {self.downstream_cso.cso_name}")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Distance input
        distance_input = QLineEdit(str(self.distance))
        form_layout.addRow("Distance (m):", distance_input)

        # Velocity input
        velocity_input = QLineEdit(str(self.velocity))
        form_layout.addRow("Average Velocity (m/s):", velocity_input)

        # Max PFF input
        max_pff_input = QLineEdit(
            str(self.max_pff) if self.max_pff is not None else "")
        form_layout.addRow("Max Pass-Forward Flow (m³/s):", max_pff_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.distance = float(distance_input.text())
                self.velocity = float(velocity_input.text())
                max_pff_text = max_pff_input.text().strip()
                self.max_pff = float(max_pff_text) if max_pff_text else None
            except ValueError:
                QMessageBox.warning(None, "Invalid Input",
                                    "Please enter valid numeric values.")

    def delete_link(self):
        """Delete this link."""
        # Unregister from connected nodes
        self.upstream_cso.remove_downstream_link(self)
        self.downstream_cso.remove_upstream_link(self)

        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)

    def get_properties(self) -> Dict[str, Any]:
        """Get link properties as dictionary."""
        return {
            'upstream_cso': self.upstream_cso.cso_name,
            'downstream_cso': self.downstream_cso.cso_name,
            'distance': self.distance,
            'velocity': self.velocity,
            'max_pff': self.max_pff
        }
