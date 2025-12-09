"""
Graphical CSO Editor Tab - Visual representation of CSO relationships.

This tab provides an interactive graphical interface for defining CSO relationships
using drag-and-drop and visual links.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGraphicsView, QGraphicsScene, QToolBar, QLabel,
                             QInputDialog, QMessageBox, QFileDialog, QSizePolicy,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QAction, QIcon, QPainter
from typing import Dict, List, Optional, Any
import pandas as pd
import json

from plato.gui.widgets.cso_graphics_items import CSOGraphicsItem, CSOLinkGraphicsItem


class LinkPropertiesDialog(QDialog):
    """Dialog for entering link properties (distance, velocity, max PFF)."""

    def __init__(self, upstream_name: str, downstream_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            f"Link Properties: {upstream_name} → {downstream_name}")
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Distance input
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.01, 999999.0)
        self.distance_spin.setValue(100.0)
        self.distance_spin.setSuffix(" m")
        self.distance_spin.setDecimals(2)
        form_layout.addRow("Distance:", self.distance_spin)

        # Velocity input
        self.velocity_spin = QDoubleSpinBox()
        self.velocity_spin.setRange(0.01, 100.0)
        self.velocity_spin.setValue(1.0)
        self.velocity_spin.setSuffix(" m/s")
        self.velocity_spin.setDecimals(3)
        form_layout.addRow("Average Velocity:", self.velocity_spin)

        # Max PFF input (optional)
        self.max_pff_input = QLineEdit()
        self.max_pff_input.setPlaceholderText(
            "Optional - leave blank if unknown")
        form_layout.addRow("Max Pass-Forward Flow (m³/s):", self.max_pff_input)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_values(self):
        """Get the entered values."""
        distance = self.distance_spin.value()
        velocity = self.velocity_spin.value()

        max_pff = None
        max_pff_text = self.max_pff_input.text().strip()
        if max_pff_text:
            try:
                max_pff = float(max_pff_text)
            except ValueError:
                pass  # Leave as None if invalid

        return distance, velocity, max_pff


class CSOGraphicsView(QGraphicsView):
    """Custom QGraphicsView that handles link creation clicks."""

    def __init__(self, scene, parent_tab):
        super().__init__(scene)
        self.parent_tab = parent_tab

    def mousePressEvent(self, event):
        """Handle mouse clicks for link creation."""
        if self.parent_tab.drawing_link:
            # Map to scene coordinates
            scene_pos = self.mapToScene(event.pos())
            item = self.scene().itemAt(scene_pos, self.transform())

            # Check if clicked on a CSO node or its child (like text label)
            cso_node = None
            if isinstance(item, CSOGraphicsItem):
                cso_node = item
            elif item and isinstance(item.parentItem(), CSOGraphicsItem):
                # Clicked on a child item (like text label), get the parent CSO node
                cso_node = item.parentItem()

            if cso_node:
                if self.parent_tab.link_start_node is None:
                    self.parent_tab.link_start_node = cso_node
                    self.parent_tab.status_label.setText(
                        f"Selected upstream CSO: {cso_node.cso_name}. Now click downstream CSO."
                    )
                else:
                    # Create link
                    if self.parent_tab.link_start_node == cso_node:
                        QMessageBox.warning(self.parent_tab, "Invalid Link",
                                            "Cannot link a CSO to itself.")
                    else:
                        self.parent_tab.create_link(
                            self.parent_tab.link_start_node, cso_node)

                    # Reset
                    self.parent_tab.link_start_node = None
                    self.parent_tab.drawing_link = False
                    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                    self.parent_tab.status_label.setText("Link created.")
                return

        super().mousePressEvent(event)


class CSOGraphicalEditorTab(QWidget):
    """
    Graphical editor for defining CSO relationships.

    Features:
    - Visual representation of CSOs as nodes
    - Drag-and-drop link creation
    - Export to DataFrame format for analysis
    """

    # Signal emitted when configuration changes
    configuration_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data storage
        self.cso_nodes: Dict[str, CSOGraphicsItem] = {}
        self.available_cso_names: List[str] = []

        # Link drawing state
        self.drawing_link = False
        self.link_start_node: Optional[CSOGraphicsItem] = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()

        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        # Graphics view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)

        self.view = CSOGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(self.view)

        # Status bar
        self.status_label = QLabel("Ready. Add CSOs to begin.")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def create_toolbar(self) -> QToolBar:
        """Create the toolbar with action buttons."""
        toolbar = QToolBar()

        # Add CSO button
        add_cso_action = QAction("Add CSO", self)
        add_cso_action.triggered.connect(self.add_cso_node)
        toolbar.addAction(add_cso_action)

        toolbar.addSeparator()

        # Add Link button
        add_link_action = QAction("Add Link", self)
        add_link_action.triggered.connect(self.toggle_link_mode)
        toolbar.addAction(add_link_action)

        toolbar.addSeparator()

        # Clear all button
        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self.clear_all)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # Import/Export buttons
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.import_configuration)
        toolbar.addAction(import_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_configuration)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Validate button
        validate_action = QAction("Validate", self)
        validate_action.triggered.connect(self.validate_configuration)
        toolbar.addAction(validate_action)

        return toolbar

    def add_cso_node(self):
        """Add a new CSO node to the scene."""
        # Prompt for CSO name
        cso_name, ok = QInputDialog.getText(
            self, "Add CSO", "Enter CSO name:",
            text=f"CSO_{len(self.cso_nodes) + 1}"
        )

        if ok and cso_name:
            if cso_name in self.cso_nodes:
                QMessageBox.warning(self, "Duplicate Name",
                                    f"A CSO named '{cso_name}' already exists.")
                return

            # Create node at center of view
            view_center = self.view.mapToScene(
                self.view.viewport().rect().center())
            node = CSOGraphicsItem(cso_name, view_center.x(), view_center.y())

            self.scene.addItem(node)
            self.cso_nodes[cso_name] = node

            self.status_label.setText(f"Added CSO: {cso_name}")
            self.configuration_changed.emit()

    def toggle_link_mode(self):
        """Toggle link drawing mode."""
        if self.drawing_link:
            self.drawing_link = False
            self.link_start_node = None
            self.status_label.setText("Link mode disabled.")
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.drawing_link = True
            self.status_label.setText(
                "Link mode: Click first CSO (upstream), then second CSO (downstream).")
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def create_link(self, upstream_node: CSOGraphicsItem, downstream_node: CSOGraphicsItem):
        """Create a link between two CSO nodes."""
        # Check if link already exists
        for link in upstream_node.downstream_links:
            if link.downstream_cso == downstream_node:
                QMessageBox.warning(self, "Duplicate Link",
                                    "A link already exists between these CSOs.")
                return

        # Show dialog for link properties
        dialog = LinkPropertiesDialog(
            upstream_node.cso_name, downstream_node.cso_name, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            distance, velocity, max_pff = dialog.get_values()

            # Create link
            link = CSOLinkGraphicsItem(
                upstream_node, downstream_node, distance, velocity, max_pff)
            self.scene.addItem(link)

            self.configuration_changed.emit()

    def clear_all(self):
        """Clear all CSOs and links from the scene."""
        reply = QMessageBox.question(
            self, "Clear All", "Are you sure you want to clear all CSOs and links?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.scene.clear()
            self.cso_nodes.clear()
            self.status_label.setText("All cleared.")
            self.configuration_changed.emit()

    def validate_configuration(self):
        """Validate the current configuration."""
        errors = []

        # Check for CSOs
        if not self.cso_nodes:
            errors.append("No CSOs defined.")

        # Check for circular dependencies
        if self.has_circular_dependency():
            errors.append("Circular dependency detected in CSO relationships.")

        # Check for disconnected CSOs (optional warning)
        disconnected = [name for name, node in self.cso_nodes.items()
                        if not node.downstream_links and not node.upstream_links]

        if disconnected:
            errors.append(
                f"Disconnected CSOs (no links): {', '.join(disconnected)}")

        # Display results
        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(
                self, "Validation", "Configuration is valid!")

    def has_circular_dependency(self) -> bool:
        """Check for circular dependencies in the CSO graph."""
        visited = set()
        rec_stack = set()

        def visit(node_name: str) -> bool:
            if node_name in rec_stack:
                return True
            if node_name in visited:
                return False

            visited.add(node_name)
            rec_stack.add(node_name)

            node = self.cso_nodes.get(node_name)
            if node:
                for link in node.downstream_links:
                    if visit(link.downstream_cso.cso_name):
                        return True

            rec_stack.remove(node_name)
            return False

        for node_name in self.cso_nodes:
            if visit(node_name):
                return True

        return False

    def export_to_dataframe(self) -> pd.DataFrame:
        """
        Export the graphical configuration to a DataFrame format.

        Returns:
            DataFrame compatible with CatchmentAnalysisEngine
        """
        data = []

        for cso_name, node in self.cso_nodes.items():
            # Base CSO data
            cso_data = {
                'CSO Name': cso_name,
                'Continuation Link': '',  # To be filled by user or imported
                'Spill Target (Entire Period)': 10,  # Default
                'PFF Increase (m3/s)': 0,
                'Tank Volume (m3)': None,
                'Pumping Mode': 'Depth',
                'Pump Rate (m3/s)': None,
                'Flow Return Threshold (m3/s)': 0,
                'Depth Return Threshold (m)': 0,
                'Time Delay (hours)': 0,
                'Spill Flow Threshold (m3/s)': 0,
                'Spill Volume Threshold (m3)': 0,
            }

            # Add downstream relationship if exists
            if node.downstream_links:
                # Take first downstream link (assuming one downstream CSO)
                link = node.downstream_links[0]
                cso_data['Downstream CSO'] = link.downstream_cso.cso_name
                cso_data['Distance (m)'] = link.distance
                cso_data['Average Velocity (m/s)'] = link.velocity
                cso_data['Maximum Pass Forward Flow (m3/s)'] = link.max_pff or 'Unknown'

            # Add upstream relationships
            if node.upstream_links:
                upstream_names = [
                    link.upstream_cso.cso_name for link in node.upstream_links]
                cso_data['Upstream CSOs'] = ', '.join(upstream_names)

            data.append(cso_data)

        return pd.DataFrame(data)

    def import_configuration(self):
        """Import configuration from a JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                config = json.load(f)

            # Clear existing
            self.scene.clear()
            self.cso_nodes.clear()

            # Load nodes
            for node_data in config.get('nodes', []):
                node = CSOGraphicsItem(
                    node_data['name'],
                    node_data['x'],
                    node_data['y']
                )
                self.scene.addItem(node)
                self.cso_nodes[node_data['name']] = node

            # Load links
            for link_data in config.get('links', []):
                upstream = self.cso_nodes.get(link_data['upstream'])
                downstream = self.cso_nodes.get(link_data['downstream'])

                if upstream and downstream:
                    link = CSOLinkGraphicsItem(
                        upstream, downstream,
                        link_data['distance'],
                        link_data['velocity'],
                        link_data.get('max_pff')
                    )
                    self.scene.addItem(link)

            self.status_label.setText(
                f"Imported configuration from {file_path}")
            self.configuration_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Import Error",
                                 f"Failed to import: {str(e)}")

    def export_configuration(self):
        """Export configuration to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            config = {
                'nodes': [],
                'links': []
            }

            # Export nodes
            for name, node in self.cso_nodes.items():
                config['nodes'].append({
                    'name': name,
                    'x': node.pos().x(),
                    'y': node.pos().y()
                })

            # Export links
            for node in self.cso_nodes.values():
                for link in node.downstream_links:
                    config['links'].append({
                        'upstream': link.upstream_cso.cso_name,
                        'downstream': link.downstream_cso.cso_name,
                        'distance': link.distance,
                        'velocity': link.velocity,
                        'max_pff': link.max_pff
                    })

            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)

            self.status_label.setText(f"Exported configuration to {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error",
                                 f"Failed to export: {str(e)}")

    def set_available_csos(self, cso_names: List[str]):
        """Set the list of available CSO names from imported data."""
        self.available_cso_names = cso_names
        self.status_label.setText(
            f"Loaded {len(cso_names)} CSOs from data import.")
