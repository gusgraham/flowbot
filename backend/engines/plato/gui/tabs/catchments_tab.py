"""Catchments Tab - Define named catchment groups with graphical relationship editor."""

from typing import List, Optional, Dict

from PyQt6.QtCore import pyqtSignal, Qt, QPointF
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QGroupBox, QMessageBox,
    QInputDialog, QSplitter, QToolBar, QLineEdit, QDialog,
    QDialogButtonBox, QGraphicsView, QGraphicsScene, QSizePolicy, QComboBox
)
from PyQt6.QtGui import QPainter

from plato.refactored.asset_models import Catchment, CatchmentRelationship, CSOAsset
from plato.gui.widgets.cso_graphics_items import CSOGraphicsItem, CSOLinkGraphicsItem
import pandas as pd


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
                        self.parent_tab.create_link_in_catchment(
                            self.parent_tab.link_start_node, cso_node)

                    # Reset
                    self.parent_tab.link_start_node = None
                    self.parent_tab.drawing_link = False
                    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                    self.parent_tab.status_label.setText("Link created.")
                return

        super().mousePressEvent(event)


class LinkPropertiesDialog(QDialog):
    """Dialog for entering link properties (distance, velocity, max PFF)."""

    def __init__(self, upstream_name: str, downstream_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            f"Link Properties: {upstream_name} → {downstream_name}")
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        from PyQt6.QtWidgets import QFormLayout, QDoubleSpinBox

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


class CatchmentsTab(QWidget):
    """
    Tab for managing catchments with integrated graphical editor.

    Left panel: List of catchments
    Right panel: Graphical editor for selected catchment
    """

    catchments_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data
        self.catchments: List[Catchment] = []
        self.current_catchment: Optional[Catchment] = None
        self.available_cso_assets: List[CSOAsset] = []

        # Graphics state
        self.cso_nodes: Dict[str, CSOGraphicsItem] = {}
        self.drawing_link = False
        self.link_start_node: Optional[CSOGraphicsItem] = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QHBoxLayout()

        # Create splitter for left panel and right panel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Catchment list
        left_panel = self.create_catchment_list_panel()
        splitter.addWidget(left_panel)

        # Right panel - Graphical editor
        right_panel = self.create_graphical_editor_panel()
        splitter.addWidget(right_panel)

        # Set initial sizes (30% left, 70% right)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def create_catchment_list_panel(self) -> QWidget:
        """Create the left panel with catchment list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel("Catchments")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Catchment list
        self.catchment_list = QListWidget()
        self.catchment_list.currentItemChanged.connect(
            self.on_catchment_selected)
        layout.addWidget(self.catchment_list)

        # Buttons
        btn_layout = QVBoxLayout()

        self.add_catchment_btn = QPushButton("+ New Catchment")
        self.add_catchment_btn.clicked.connect(self.add_catchment)
        btn_layout.addWidget(self.add_catchment_btn)

        self.rename_catchment_btn = QPushButton("Rename")
        self.rename_catchment_btn.clicked.connect(self.rename_catchment)
        self.rename_catchment_btn.setEnabled(False)
        btn_layout.addWidget(self.rename_catchment_btn)

        self.delete_catchment_btn = QPushButton("Delete")
        self.delete_catchment_btn.clicked.connect(self.delete_catchment)
        self.delete_catchment_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_catchment_btn)

        # btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return panel

    def create_graphical_editor_panel(self) -> QWidget:
        """Create the right panel with graphical editor."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title and status
        title_layout = QHBoxLayout()
        self.editor_title = QLabel("No catchment selected")
        self.editor_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.editor_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Toolbar
        toolbar = self.create_editor_toolbar()
        layout.addWidget(toolbar)

        # Graphics view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)

        self.view = CSOGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.view.setEnabled(False)  # Disabled until catchment selected
        layout.addWidget(self.view)

        # Status bar
        self.status_label = QLabel("Select or create a catchment to begin")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        return panel

    def create_editor_toolbar(self) -> QToolBar:
        """Create the toolbar for the graphical editor."""
        from PyQt6.QtGui import QAction

        toolbar = QToolBar()

        # Add CSO dropdown
        toolbar.addWidget(QLabel("Add CSO:"))
        self.cso_combo = QComboBox()
        self.cso_combo.setMinimumWidth(150)
        self.cso_combo.currentTextChanged.connect(
            self.on_cso_selected_from_dropdown)
        toolbar.addWidget(self.cso_combo)

        toolbar.addSeparator()

        # Add Link button
        self.add_link_action = QAction("Add Link", self)
        self.add_link_action.triggered.connect(self.toggle_link_mode)
        self.add_link_action.setEnabled(False)
        toolbar.addAction(self.add_link_action)

        toolbar.addSeparator()

        # Validate button
        self.validate_action = QAction("Validate", self)
        self.validate_action.triggered.connect(self.validate_current_catchment)
        self.validate_action.setEnabled(False)
        toolbar.addAction(self.validate_action)

        # Clear button
        self.clear_action = QAction("Clear All", self)
        self.clear_action.triggered.connect(self.clear_current_catchment)
        self.clear_action.setEnabled(False)
        toolbar.addAction(self.clear_action)

        return toolbar

    def add_catchment(self):
        """Create a new catchment."""
        name, ok = QInputDialog.getText(
            self, "New Catchment", "Catchment name:")

        if ok and name:
            # Check for duplicate names
            if any(c.name == name for c in self.catchments):
                QMessageBox.warning(self, "Duplicate Name",
                                    f"A catchment named '{name}' already exists.")
                return

            # Create new catchment
            catchment = Catchment(name=name, cso_relationships=[])
            self.catchments.append(catchment)

            # Add to list
            item = QListWidgetItem(name)
            self.catchment_list.addItem(item)
            self.catchment_list.setCurrentItem(item)

            self.catchments_changed.emit()
            self.status_label.setText(f"Created catchment: {name}")

    def rename_catchment(self):
        """Rename the selected catchment."""
        if not self.current_catchment:
            return

        name, ok = QInputDialog.getText(
            self, "Rename Catchment", "New name:",
            text=self.current_catchment.name
        )

        if ok and name:
            # Check for duplicates
            if any(c.name == name and c != self.current_catchment for c in self.catchments):
                QMessageBox.warning(self, "Duplicate Name",
                                    f"A catchment named '{name}' already exists.")
                return

            old_name = self.current_catchment.name
            self.current_catchment.name = name

            # Update list
            current_item = self.catchment_list.currentItem()
            if current_item:
                current_item.setText(name)

            self.editor_title.setText(f"Editing: {name}")
            self.catchments_changed.emit()
            self.status_label.setText(f"Renamed '{old_name}' to '{name}'")

    def delete_catchment(self):
        """Delete the selected catchment."""
        if not self.current_catchment:
            return

        reply = QMessageBox.question(
            self, "Delete Catchment",
            f"Are you sure you want to delete catchment '{self.current_catchment.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            name = self.current_catchment.name
            self.catchments.remove(self.current_catchment)
            self.current_catchment = None

            # Remove from list
            current_row = self.catchment_list.currentRow()
            self.catchment_list.takeItem(current_row)

            # Clear editor
            self.clear_editor()

            self.catchments_changed.emit()
            self.status_label.setText(f"Deleted catchment: {name}")

    def on_catchment_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle catchment selection."""
        # Save positions of the previous catchment before switching
        if previous and self.current_catchment:
            self._save_current_node_positions()

        if not current:
            self.current_catchment = None
            self.clear_editor()
            return

        # Find catchment by name
        catchment_name = current.text()
        self.current_catchment = next(
            (c for c in self.catchments if c.name == catchment_name), None)

        if self.current_catchment:
            self.load_catchment_to_editor(self.current_catchment)
            self.rename_catchment_btn.setEnabled(True)
            self.delete_catchment_btn.setEnabled(True)
            self.add_link_action.setEnabled(True)
            self.validate_action.setEnabled(True)
            self.clear_action.setEnabled(True)
            self.view.setEnabled(True)

    def clear_editor(self):
        """Clear the graphical editor."""
        self.scene.clear()
        self.cso_nodes.clear()
        self.editor_title.setText("No catchment selected")
        self.status_label.setText("Select or create a catchment to begin")
        self.rename_catchment_btn.setEnabled(False)
        self.delete_catchment_btn.setEnabled(False)
        self.add_link_action.setEnabled(False)
        self.validate_action.setEnabled(False)
        self.clear_action.setEnabled(False)
        self.view.setEnabled(False)

    def load_catchment_to_editor(self, catchment: Catchment):
        """Load a catchment into the graphical editor."""
        self.scene.clear()
        self.cso_nodes.clear()

        self.editor_title.setText(f"Editing: {catchment.name}")
        self.status_label.setText(f"Loaded catchment: {catchment.name}")

        # Get saved node positions if available
        saved_positions = getattr(catchment, '_node_positions', {})

        # Add CSO nodes
        for i, rel in enumerate(catchment.cso_relationships):
            # Use saved position if available, otherwise use grid layout
            if saved_positions and rel.cso_name in saved_positions:
                pos = saved_positions[rel.cso_name]
                x = pos['x']
                y = pos['y']
            else:
                # Calculate position in a grid layout (fallback)
                col = i % 4
                row = i // 4
                x = 200 + col * 200
                y = 200 + row * 200

            node = CSOGraphicsItem(rel.cso_name, x, y)
            self.scene.addItem(node)
            self.cso_nodes[rel.cso_name] = node

        # Add links
        for rel in catchment.cso_relationships:
            if rel.downstream_cso:
                upstream_node = self.cso_nodes.get(rel.cso_name)
                downstream_node = self.cso_nodes.get(rel.downstream_cso)

                if upstream_node and downstream_node:
                    link = CSOLinkGraphicsItem(
                        upstream_node, downstream_node,
                        rel.distance_to_downstream or 100.0,
                        rel.average_velocity or 1.0,
                        rel.max_pff
                    )
                    self.scene.addItem(link)

        self.update_cso_dropdown()

    def update_cso_dropdown(self):
        """Update the CSO dropdown with available CSOs."""
        self.cso_combo.clear()
        self.cso_combo.addItem("-- Select CSO to Add --")

        # Get CSOs already in the catchment
        used_csos = set(self.cso_nodes.keys())

        # Get available CSOs from assets
        available = [
            asset.name for asset in self.available_cso_assets if asset.name not in used_csos]

        self.cso_combo.addItems(available)

    def on_cso_selected_from_dropdown(self, cso_name: str):
        """Handle CSO selection from dropdown."""
        if cso_name and cso_name != "-- Select CSO to Add --":
            self.add_cso_to_catchment(cso_name)
            self.cso_combo.setCurrentIndex(0)  # Reset dropdown

    def add_cso_to_catchment(self, cso_name: str):
        """Add a CSO node to the current catchment."""
        if not self.current_catchment:
            return

        if cso_name in self.cso_nodes:
            QMessageBox.warning(self, "Duplicate CSO",
                                f"CSO '{cso_name}' is already in this catchment.")
            return

        # Add to catchment model
        rel = CatchmentRelationship(cso_name=cso_name)
        self.current_catchment.cso_relationships.append(rel)

        # Add to graphics view (at center)
        view_center = self.view.mapToScene(
            self.view.viewport().rect().center())
        node = CSOGraphicsItem(cso_name, view_center.x(), view_center.y())
        self.scene.addItem(node)
        self.cso_nodes[cso_name] = node

        self.update_cso_dropdown()
        self.catchments_changed.emit()
        self.status_label.setText(f"Added CSO: {cso_name}")

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

    def create_link_in_catchment(self, upstream_node: CSOGraphicsItem, downstream_node: CSOGraphicsItem):
        """Create a link between two CSO nodes in the current catchment."""
        if not self.current_catchment:
            return

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

            # Update the relationship in the catchment model
            rel = next((r for r in self.current_catchment.cso_relationships
                       if r.cso_name == upstream_node.cso_name), None)

            if rel:
                rel.downstream_cso = downstream_node.cso_name
                rel.distance_to_downstream = distance
                rel.average_velocity = velocity
                rel.max_pff = max_pff

                # Also update upstream CSOs for the downstream node
                downstream_rel = next((r for r in self.current_catchment.cso_relationships
                                      if r.cso_name == downstream_node.cso_name), None)
                if downstream_rel:
                    if not downstream_rel.upstream_csos:
                        downstream_rel.upstream_csos = []
                    if upstream_node.cso_name not in downstream_rel.upstream_csos:
                        downstream_rel.upstream_csos.append(
                            upstream_node.cso_name)

            # Create graphical link
            link = CSOLinkGraphicsItem(
                upstream_node, downstream_node, distance, velocity, max_pff)
            self.scene.addItem(link)

            self.catchments_changed.emit()

    def validate_current_catchment(self):
        """Validate the current catchment configuration."""
        if not self.current_catchment:
            return

        # Use the catchment's validate method
        errors = self.current_catchment.validate()

        # Check for circular dependencies
        if self.has_circular_dependency():
            errors.append("Circular dependency detected in CSO relationships.")

        # Check for disconnected CSOs
        disconnected = []
        for rel in self.current_catchment.cso_relationships:
            node = self.cso_nodes.get(rel.cso_name)
            if node and not node.downstream_links and not node.upstream_links:
                disconnected.append(rel.cso_name)

        if disconnected:
            errors.append(
                f"Disconnected CSOs (no links): {', '.join(disconnected)}")

        # Display results
        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation",
                                    f"Catchment '{self.current_catchment.name}' is valid!")

    def has_circular_dependency(self) -> bool:
        """Check for circular dependencies in the current catchment."""
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

    def clear_current_catchment(self):
        """Clear all CSOs and links from the current catchment."""
        if not self.current_catchment:
            return

        reply = QMessageBox.question(
            self, "Clear Catchment",
            f"Are you sure you want to clear all CSOs and links from '{self.current_catchment.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_catchment.cso_relationships.clear()
            self.scene.clear()
            self.cso_nodes.clear()
            self.update_cso_dropdown()
            self.catchments_changed.emit()
            self.status_label.setText("Catchment cleared.")

    def set_cso_assets(self, assets: List[CSOAsset]):
        """Set the available CSO assets from the CSO Assets tab."""
        self.available_cso_assets = assets
        self.update_cso_dropdown()

    def set_available_cso_assets(self, assets: List[CSOAsset]):
        """Alias for set_cso_assets for backward compatibility."""
        self.set_cso_assets(assets)

    def get_catchments(self) -> List[Catchment]:
        """Get all defined catchments."""
        return self.catchments

    def get_catchment_names(self) -> List[str]:
        """Get names of all defined catchments."""
        return [c.name for c in self.catchments]

    def load_catchments(self, catchments: List[Catchment]):
        """Load catchments from saved data."""
        self.catchments = catchments
        self.catchment_list.clear()

        for catchment in catchments:
            item = QListWidgetItem(catchment.name)
            self.catchment_list.addItem(item)

    def get_state(self) -> dict:
        """Get current state for project save."""
        # Save the current catchment's node positions before serializing
        if self.current_catchment:
            self._save_current_node_positions()

        return {
            'catchments': [
                {
                    'name': c.name,
                    'cso_relationships': [
                        {
                            'cso_name': rel.cso_name,
                            'upstream_csos': rel.upstream_csos,
                            'downstream_cso': rel.downstream_cso,
                            'max_pff': rel.max_pff,
                            'distance_to_downstream': rel.distance_to_downstream,
                            'average_velocity': rel.average_velocity
                        }
                        for rel in c.cso_relationships
                    ],
                    # Save graphical positions
                    'node_positions': getattr(c, '_node_positions', {})
                }
                for c in self.catchments
            ]
        }

    def _save_current_node_positions(self):
        """Save the current graphical positions of CSO nodes for the current catchment."""
        if not self.current_catchment:
            return

        positions = {}
        for cso_name, node in self.cso_nodes.items():
            positions[cso_name] = {
                'x': node.pos().x(),
                'y': node.pos().y()
            }

        # Store positions on the catchment object (temporary attribute for serialization)
        self.current_catchment._node_positions = positions

    def load_state(self, state: dict):
        """Load state from project file."""
        if 'catchments' not in state:
            return

        # Clear existing catchments
        self.catchments = []
        self.catchment_list.clear()
        self.scene.clear()

        # Reconstruct catchments from saved data
        for catchment_data in state['catchments']:
            relationships = []
            for rel in catchment_data['cso_relationships']:
                # Only include distance/velocity if downstream CSO exists
                downstream_cso = rel.get('downstream_cso')

                if downstream_cso:
                    # CSO has downstream connection - include all fields
                    relationship = CatchmentRelationship(
                        cso_name=rel['cso_name'],
                        upstream_csos=rel.get('upstream_csos', []),
                        downstream_cso=downstream_cso,
                        max_pff=rel.get('max_pff'),
                        distance_to_downstream=rel.get(
                            'distance_to_downstream'),
                        average_velocity=rel.get('average_velocity')
                    )
                else:
                    # CSO has no downstream (outlet) - don't include distance/velocity
                    relationship = CatchmentRelationship(
                        cso_name=rel['cso_name'],
                        upstream_csos=rel.get('upstream_csos', []),
                        downstream_cso=None,
                        max_pff=rel.get('max_pff'),
                        distance_to_downstream=None,
                        average_velocity=None
                    )

                relationships.append(relationship)

            catchment = Catchment(
                name=catchment_data['name'],
                cso_relationships=relationships
            )

            # Store node positions for later use when loading to editor
            node_positions = catchment_data.get('node_positions', {})
            if node_positions:
                catchment._node_positions = node_positions

            self.catchments.append(catchment)

            # Add to list widget
            item = QListWidgetItem(catchment.name)
            self.catchment_list.addItem(item)

        # Emit signal
        self.catchments_changed.emit()
