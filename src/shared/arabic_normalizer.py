"""Arabic text normalization, per project brief §5.6.

Called by every text-comparison site in the codebase (join-key matching,
exclusion-rule matching, basin grouping, spatial-sort neighbor matching)
so that comparisons are consistent regardless of source-file spelling
variants.
"""

import re
import unicodedata

_ALEF_VARIANTS = str.maketrans("أإآ", "ااا")
_YA_VARIANT = str.maketrans("ى", "ي")
_DIACRITICS_PATTERN = re.compile("[" + "".join(chr(c) for c in range(0x064B, 0x0653)) + "ٰ" + "]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_arabic(text: str, normalize_taa_marbuta: bool = False) -> str:
    """Normalize Arabic text for comparison.

    Applies, in order: NFC unicode normalization, ى→ي, أ/إ/آ→ا,
    diacritic removal, optional ة→ه, and whitespace collapsing.

    Args:
        text: The raw text to normalize.
        normalize_taa_marbuta: When True, also maps ة→ه. Off by default
            since ة/ه are not always interchangeable in practice.

    Returns:
        The normalized, stripped text.
    """
    result = unicodedata.normalize("NFC", text)
    result = result.translate(_YA_VARIANT)
    result = result.translate(_ALEF_VARIANTS)
    result = _DIACRITICS_PATTERN.sub("", result)
    if normalize_taa_marbuta:
        result = result.replace("ة", "ه")
    result = _WHITESPACE_PATTERN.sub(" ", result)
    return result.strip()
