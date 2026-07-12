"""Merge mode value object, per Iteration 3 Task B.

The "system file" (a fixed-schema export) only describes the real
world about 80% of the time — sometimes both files a user has are
external/variable-schema exports. `MergeMode` names which situation
the user is in; it constrains which mapping choices are valid for each
slot, but does not otherwise change merge behavior — once two
`SlotAssignment`s are resolved to concrete (file, mapping) pairs,
`MergeParcelsUseCase` runs identically regardless of mode.
"""

from enum import Enum


class MergeMode(Enum):
    """Which of the two supported input configurations the user selected.

    SYSTEM_PLUS_EXTERNAL: the primary slot's mapping is fixed to the
        default system-file mapping; only the supplementary slot's
        mapping is user-selectable. This is the default mode and the
        only one with a Stitch-designed UI so far (see
        resources/design/INVENTORY.md).
    TWO_EXTERNAL: both slots' mappings are user-selectable. No UI
        exists yet for this mode — it's supported at the
        domain/application level so the presentation layer can adopt
        it once that design is delivered.
    """

    SYSTEM_PLUS_EXTERNAL = "system_plus_external"
    TWO_EXTERNAL = "two_external"
