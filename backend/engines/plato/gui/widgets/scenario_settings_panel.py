"""UI component for configuring scenario-level analysis settings."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QSpinBox,
)

from plato.refactored.config import ScenarioSettings


class ScenarioSettingsPanel(QGroupBox):
    """Group box providing scenario-level configuration controls."""

    def __init__(self, parent=None) -> None:
        super().__init__("Scenario Settings", parent)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QFormLayout()
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(8)

        self.spill_target_spin = QSpinBox()
        self.spill_target_spin.setRange(0, 10_000)
        self.spill_target_spin.setValue(10)
        form.addRow("Spill Target (entire period)", self.spill_target_spin)

        self.bathing_target_spin = QSpinBox()
        self.bathing_target_spin.setRange(0, 10_000)
        self.bathing_target_spin.setValue(0)
        form.addRow("Spill Target (bathing season)", self.bathing_target_spin)

        self.spill_flow_spin = QDoubleSpinBox()
        self.spill_flow_spin.setDecimals(5)
        self.spill_flow_spin.setRange(0.0, 10.0)
        self.spill_flow_spin.setSingleStep(0.0001)
        self.spill_flow_spin.setValue(0.001)
        form.addRow("Spill Flow Threshold (m3/s)", self.spill_flow_spin)

        self.spill_volume_spin = QDoubleSpinBox()
        self.spill_volume_spin.setDecimals(2)
        self.spill_volume_spin.setRange(0.0, 1_000_000.0)
        self.spill_volume_spin.setSingleStep(10.0)
        self.spill_volume_spin.setValue(0.0)
        form.addRow("Spill Volume Threshold (m3)", self.spill_volume_spin)

        self.bathing_start_edit = self._build_bathing_edit("15/05")
        form.addRow("Bathing Season Start (dd/mm)", self.bathing_start_edit)

        self.bathing_end_edit = self._build_bathing_edit("30/09")
        form.addRow("Bathing Season End (dd/mm)", self.bathing_end_edit)

        self.time_delay_spin = QSpinBox()
        self.time_delay_spin.setRange(0, 1_000)
        self.time_delay_spin.setValue(0)
        form.addRow("Return Time Delay (hours)", self.time_delay_spin)

        self.pump_mode_combo = QComboBox()
        self.pump_mode_combo.addItems(["Fixed", "Variable"])
        form.addRow("Pump Mode", self.pump_mode_combo)

        self.pump_rate_spin = QDoubleSpinBox()
        self.pump_rate_spin.setDecimals(5)
        self.pump_rate_spin.setRange(0.0, 10.0)
        self.pump_rate_spin.setSingleStep(0.0001)
        self.pump_rate_spin.setValue(0.0)
        form.addRow("Pump Rate (m3/s)", self.pump_rate_spin)

        self.flow_return_spin = QDoubleSpinBox()
        self.flow_return_spin.setDecimals(5)
        self.flow_return_spin.setRange(0.0, 10.0)
        self.flow_return_spin.setSingleStep(0.0001)
        self.flow_return_spin.setValue(0.0)
        form.addRow("Flow Return Threshold (m3/s)", self.flow_return_spin)

        self.depth_return_spin = QDoubleSpinBox()
        self.depth_return_spin.setDecimals(3)
        self.depth_return_spin.setRange(0.0, 50.0)
        self.depth_return_spin.setSingleStep(0.05)
        self.depth_return_spin.setValue(0.0)
        form.addRow("Depth Return Threshold (m)", self.depth_return_spin)

        self.pff_increase_spin = QDoubleSpinBox()
        self.pff_increase_spin.setDecimals(5)
        self.pff_increase_spin.setRange(0.0, 10.0)
        self.pff_increase_spin.setSingleStep(0.0001)
        self.pff_increase_spin.setValue(0.0)
        form.addRow("PFF Increase (m3/s)", self.pff_increase_spin)

        self.setLayout(form)

    def _build_bathing_edit(self, default: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setMaxLength(5)
        regex = QRegularExpression(
            r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])$")
        edit.setValidator(QRegularExpressionValidator(regex))
        edit.setText(default)
        return edit

    def get_settings(self) -> ScenarioSettings:
        return ScenarioSettings(
            spill_target=self.spill_target_spin.value(),
            bathing_spill_target=self.bathing_target_spin.value(),
            spill_flow_threshold=self.spill_flow_spin.value(),
            spill_volume_threshold=self.spill_volume_spin.value(),
            bathing_season_start=self._parse_day_month(
                self.bathing_start_edit.text()),
            bathing_season_end=self._parse_day_month(
                self.bathing_end_edit.text()),
            time_delay_hours=self.time_delay_spin.value(),
            pump_mode=self.pump_mode_combo.currentText(),
            pump_rate_m3s=self.pump_rate_spin.value(),
            flow_return_threshold_m3s=self.flow_return_spin.value(),
            depth_return_threshold_m=self.depth_return_spin.value(),
            pff_increase_m3s=self.pff_increase_spin.value(),
        )

    def set_settings(self, settings: ScenarioSettings) -> None:
        self.spill_target_spin.setValue(settings.spill_target)
        self.bathing_target_spin.setValue(settings.bathing_spill_target)
        self.spill_flow_spin.setValue(settings.spill_flow_threshold)
        self.spill_volume_spin.setValue(settings.spill_volume_threshold)
        self.bathing_start_edit.setText(self._format_day_month(
            settings.bathing_season_start) or "15/05")
        self.bathing_end_edit.setText(self._format_day_month(
            settings.bathing_season_end) or "30/09")
        self.time_delay_spin.setValue(settings.time_delay_hours)
        index = self.pump_mode_combo.findText(settings.pump_mode)
        if index >= 0:
            self.pump_mode_combo.setCurrentIndex(index)
        self.pump_rate_spin.setValue(settings.pump_rate_m3s)
        self.flow_return_spin.setValue(settings.flow_return_threshold_m3s)
        self.depth_return_spin.setValue(settings.depth_return_threshold_m)
        self.pff_increase_spin.setValue(settings.pff_increase_m3s)

    def _parse_day_month(self, text: str) -> Optional[date]:
        text = (text or "").strip()
        if not text:
            return None
        try:
            day, month = map(int, text.split("/"))
            return date(2000, month, day)
        except Exception:
            return None

    def _format_day_month(self, value: Optional[date]) -> Optional[str]:
        if value is None:
            return None
        return value.strftime("%d/%m")
