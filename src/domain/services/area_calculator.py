"""Area conversion service, per project brief §5.1."""

from src.domain.value_objects.area import Area

FEDDAN_TO_SQM = 4200.833
QIRAT_TO_SQM = 175.03
SAHM_TO_SQM = 7.29


class AreaCalculator:
    """Converts feddan/qirat/sahm area components to square meters."""

    @staticmethod
    def calculate_total_sqm(area: Area) -> float | None:
        """Compute the total area in square meters.

        Empty/None components count as zero inside the formula, but if
        all three components are absent the result is None (not zero),
        per the brief's missing-data rule.

        Args:
            area: The raw area components.

        Returns:
            The total area in square meters, rounded to 2 decimal
            places, or None when `area` has no components at all.
        """
        if area.is_empty:
            return None
        total = (
            (area.feddan or 0.0) * FEDDAN_TO_SQM
            + (area.qirat or 0.0) * QIRAT_TO_SQM
            + (area.sahm or 0.0) * SAHM_TO_SQM
        )
        return round(total, 2)
