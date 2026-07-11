"""Collapsible advanced settings panel, per project brief §7.3/§9."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.presentation.i18n.ar import (
    ADVANCED_SETTINGS_TITLE,
    CHOOSE_MAPPING_BUTTON,
    DEFAULT_MAPPING_LABEL,
    ENABLE_SPATIAL_SORT_LABEL,
    INCLUDE_LAGHI_LABEL,
    LOAD_PRESET_BUTTON,
    SAVE_PRESET_BUTTON,
)


@dataclass
class AdvancedSettings:
    """Serializable state of the advanced settings panel."""

    secondary_mapping_path: str | None = None
    include_laghi_rows: bool = False
    enable_spatial_sort: bool = True

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "AdvancedSettings":
        return cls(**json.loads(text))


class AdvancedSettingsPanel(QWidget):
    """A collapsible panel for power-user pipeline settings.

    Emits `settings_changed` whenever a control is edited, a mapping
    file is chosen, or a preset is loaded — the connected handler is
    expected to apply the settings immediately, so changes take effect
    within the current session per the brief's Phase 9 acceptance rule.
    """

    settings_changed = Signal(object)  # AdvancedSettings

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = AdvancedSettings()

        self._toggle_button = QToolButton()
        self._toggle_button.setText(ADVANCED_SETTINGS_TITLE)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(False)
        self._toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self._toggle_button.toggled.connect(self._on_toggled)

        self._content = QWidget()
        self._content.setVisible(False)
        self._build_content()

        layout = QVBoxLayout(self)
        layout.addWidget(self._toggle_button)
        layout.addWidget(self._content)

    def _build_content(self) -> None:
        content_layout = QVBoxLayout(self._content)

        mapping_row = QHBoxLayout()
        self._mapping_label = QLabel(DEFAULT_MAPPING_LABEL)
        choose_mapping_button = QPushButton(CHOOSE_MAPPING_BUTTON)
        choose_mapping_button.clicked.connect(self._on_choose_mapping)
        mapping_row.addWidget(self._mapping_label, stretch=1)
        mapping_row.addWidget(choose_mapping_button)
        content_layout.addLayout(mapping_row)

        self._include_laghi_checkbox = QCheckBox(INCLUDE_LAGHI_LABEL)
        self._include_laghi_checkbox.toggled.connect(self._on_settings_edited)
        content_layout.addWidget(self._include_laghi_checkbox)

        self._spatial_sort_checkbox = QCheckBox(ENABLE_SPATIAL_SORT_LABEL)
        self._spatial_sort_checkbox.setChecked(True)
        self._spatial_sort_checkbox.toggled.connect(self._on_settings_edited)
        content_layout.addWidget(self._spatial_sort_checkbox)

        preset_row = QHBoxLayout()
        save_button = QPushButton(SAVE_PRESET_BUTTON)
        save_button.clicked.connect(self._on_save_preset)
        load_button = QPushButton(LOAD_PRESET_BUTTON)
        load_button.clicked.connect(self._on_load_preset)
        preset_row.addWidget(save_button)
        preset_row.addWidget(load_button)
        content_layout.addLayout(preset_row)

    def _on_toggled(self, checked: bool) -> None:
        self._content.setVisible(checked)
        self._toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )

    def _on_choose_mapping(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, filter="YAML Files (*.yaml *.yml)")
        if not path:
            return
        self._settings.secondary_mapping_path = path
        self._mapping_label.setText(Path(path).name)
        self._emit_settings_changed()

    def _on_settings_edited(self) -> None:
        self._settings.include_laghi_rows = self._include_laghi_checkbox.isChecked()
        self._settings.enable_spatial_sort = self._spatial_sort_checkbox.isChecked()
        self._emit_settings_changed()

    def _on_save_preset(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, filter="JSON Files (*.json)")
        if not path:
            return
        Path(path).write_text(self._settings.to_json(), encoding="utf-8")

    def _on_load_preset(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, filter="JSON Files (*.json)")
        if not path:
            return
        self._settings = AdvancedSettings.from_json(Path(path).read_text(encoding="utf-8"))
        self._apply_settings_to_widgets()
        self._emit_settings_changed()

    def _apply_settings_to_widgets(self) -> None:
        self._include_laghi_checkbox.setChecked(self._settings.include_laghi_rows)
        self._spatial_sort_checkbox.setChecked(self._settings.enable_spatial_sort)
        if self._settings.secondary_mapping_path:
            self._mapping_label.setText(Path(self._settings.secondary_mapping_path).name)
        else:
            self._mapping_label.setText(DEFAULT_MAPPING_LABEL)

    def _emit_settings_changed(self) -> None:
        self.settings_changed.emit(self._settings)
