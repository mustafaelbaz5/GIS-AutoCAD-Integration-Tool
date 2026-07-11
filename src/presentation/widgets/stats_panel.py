"""Statistics panel: a responsive grid of StatCards, per Iteration 2 §4.

Replaces the log console as the default post-processing view (the log
stays available behind a toggle — see MainWindow).
"""

from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from src.application.dto.processing_stats import ProcessingStats
from src.presentation.i18n.ar import (
    INCOMPLETE_ROWS_POPOVER_TITLE,
    STAT_DISTINCT_BASINS,
    STAT_INCOMPLETE_ROWS,
    STAT_TOTAL_FEDDAN,
    STAT_TOTAL_MERGED,
    STAT_TOTAL_SQM,
    STAT_UNPLACED,
    STAT_WITH_NATIONAL_ID,
    STATS_PANEL_TITLE,
)
from src.presentation.widgets.stat_card import StatCard

_GRID_COLUMNS = 3


def _thousands(value: float) -> str:
    return f"{value:,.2f}"


class StatsPanel(QWidget):
    """Renders a `ProcessingStats` as a grid of stat cards."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._title_label = QLabel(STATS_PANEL_TITLE)
        self._grid_container = QWidget()
        self._layout.addWidget(self._title_label)
        self._layout.addWidget(self._grid_container)
        self._stats: ProcessingStats | None = None

    def display(self, stats: ProcessingStats) -> None:
        """Render the given stats, replacing any previously shown cards."""
        self._stats = stats
        old_grid = self._grid_container
        self._grid_container = QWidget()
        grid = QGridLayout(self._grid_container)

        cards = self._build_cards(stats)
        for index, card in enumerate(cards):
            grid.addWidget(card, index // _GRID_COLUMNS, index % _GRID_COLUMNS)

        self._layout.replaceWidget(old_grid, self._grid_container)
        old_grid.deleteLater()

    def _build_cards(self, stats: ProcessingStats) -> list[StatCard]:
        incomplete_card = StatCard(
            "⚠",
            STAT_INCOMPLETE_ROWS,
            str(stats.incomplete_rows),
            variant="warning" if stats.incomplete_rows else "neutral",
            clickable=bool(stats.incomplete_holding_ids),
        )
        incomplete_card.clicked.connect(lambda: self._show_incomplete_popover(stats))

        unplaced_card = StatCard(
            "🧭",
            STAT_UNPLACED,
            str(stats.unplaced_count),
            variant="warning" if stats.unplaced_count else "neutral",
        )

        return [
            StatCard("🌾", STAT_TOTAL_MERGED, str(stats.total_merged), variant="success"),
            incomplete_card,
            StatCard("🪪", STAT_WITH_NATIONAL_ID, str(stats.with_national_id)),
            StatCard("📐", STAT_TOTAL_FEDDAN, _thousands(stats.total_feddan)),
            StatCard("📐", STAT_TOTAL_SQM, _thousands(stats.total_sqm)),
            StatCard("🗺", STAT_DISTINCT_BASINS, str(stats.distinct_basin_count)),
            unplaced_card,
        ]

    def _show_incomplete_popover(self, stats: ProcessingStats) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(INCOMPLETE_ROWS_POPOVER_TITLE)
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        list_widget.addItems(stats.incomplete_holding_ids)
        layout.addWidget(list_widget)
        dialog.resize(300, 400)
        dialog.exec()
