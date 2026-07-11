"""Full holding detail panel, per Task C §6.4.D."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from src.domain.entities.parcel import Parcel
from src.domain.services.area_calculator import AreaCalculator
from src.presentation.i18n.ar import (
    AREA_SUMMARY_TEXT,
    EMPTY_VALUE_PLACEHOLDER,
    FIELD_ADMINISTRATION,
    FIELD_BASIN_CODE,
    FIELD_BASIN_NAME,
    FIELD_DIRECTORATE,
    FIELD_HOLDER_NAME,
    FIELD_HOLDING_ID,
    FIELD_LAND_NUMBER,
    FIELD_NATIONAL_ID,
    FIELD_PAGE_NUMBER,
    FIELD_TOTAL_AREA,
)

_FIELD_ORDER = [
    FIELD_HOLDER_NAME,
    FIELD_NATIONAL_ID,
    FIELD_HOLDING_ID,
    FIELD_LAND_NUMBER,
    FIELD_BASIN_NAME,
    FIELD_BASIN_CODE,
    FIELD_DIRECTORATE,
    FIELD_ADMINISTRATION,
    FIELD_PAGE_NUMBER,
]


class HoldingDetailPanel(QWidget):
    """Shows every field of a selected `Parcel` as label/value rows.

    Empty fields render as EMPTY_VALUE_PLACEHOLDER ("—"), never blank;
    the total area is shown larger via the `statValue` theme token.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        form = QFormLayout(self)
        self._value_labels: dict[str, QLabel] = {}
        for field_label in _FIELD_ORDER:
            value_label = QLabel(EMPTY_VALUE_PLACEHOLDER)
            self._value_labels[field_label] = value_label
            form.addRow(QLabel(field_label), value_label)

        self._total_area_label = QLabel(EMPTY_VALUE_PLACEHOLDER)
        self._total_area_label.setProperty("statValue", True)
        form.addRow(QLabel(FIELD_TOTAL_AREA), self._total_area_label)

    def display(self, parcel: Parcel) -> None:
        """Render `parcel`'s fields, replacing whatever was shown before."""
        values = {
            FIELD_HOLDER_NAME: parcel.holder.name,
            FIELD_NATIONAL_ID: parcel.holder.national_id,
            FIELD_HOLDING_ID: str(parcel.holding_id),
            FIELD_LAND_NUMBER: parcel.land_number,
            FIELD_BASIN_NAME: parcel.basin.name,
            FIELD_BASIN_CODE: parcel.basin.code,
            FIELD_DIRECTORATE: parcel.directorate,
            FIELD_ADMINISTRATION: parcel.administration,
            FIELD_PAGE_NUMBER: parcel.page_number,
        }
        for label, value in values.items():
            self._value_labels[label].setText(value or EMPTY_VALUE_PLACEHOLDER)

        self._total_area_label.setText(self._format_area(parcel))

    def _format_area(self, parcel: Parcel) -> str:
        total_sqm = AreaCalculator.calculate_total_sqm(parcel.area)
        sqm_text = f"{total_sqm:,.2f}" if total_sqm is not None else EMPTY_VALUE_PLACEHOLDER
        return AREA_SUMMARY_TEXT.format(
            feddan=parcel.area.feddan or 0,
            qirat=parcel.area.qirat or 0,
            sahm=parcel.area.sahm or 0,
            sqm=sqm_text,
        )
