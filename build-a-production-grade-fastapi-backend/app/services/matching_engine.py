"""Fuzzy matching engine for compliance scanning.

Matches a BoQ item (from the client's tender) against the 1600+ mandatory
list items. Uses a two-stage strategy:

  1. EXACT code match: if the BoQ item_code exactly matches a mandatory
     item_code (case-insensitive, whitespace-normalised), it's a 100% match.
  2. FUZZY name match: otherwise, compare the BoQ description against BOTH
     the Arabic and English product names of every mandatory item, using
     rapidfuzz's token_set_ratio (handles word-order differences and
     partial matches well for both Arabic and Latin script). The threshold
     is configurable via settings.compliance_fuzzy_match_threshold (default 80).

Arabic text normalisation:
  - Arabic has many letter variants that look identical to humans but are
    different Unicode codepoints (أ إ آ ← ا, ة ← ه, ى ← ي). We normalise
    these before matching so that "أسمنت" matches "اسمنت".
  - Diacritics (tashkeel) are stripped.
  - Tatweel (ـ) is removed.
  - Leading/trailing whitespace is stripped; internal whitespace collapsed.

Performance:
  - rapidfuzz.process.extractOne is C-optimised and handles 1600 candidates
    in <5ms per query. For 100 imported BoQ items that's <500ms total.
  - The mandatory list is loaded ONCE per scan (in compliance_service) and
    passed to this function — no per-item DB round-trips.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.core.config import settings
from app.models.boq_item import BoQItem
from app.models.mandatory_list import MandatoryListItem

# Arabic letter normalisation map (variant → canonical form).
# This is the key to making fuzzy matching work on Arabic text: the same
# word can be spelled with أ or ا, ة or ه, etc. and they should match.
_ARABIC_NORMALISATIONS = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ٮ": "ي",
        "ڃ": "ي",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
        "ـ": "",  # tatweel (stretching character)
    }
)

# Arabic diacritics (tashkeel) Unicode range — stripped before matching.
_DIACRITICS_PATTERN = re.compile(r"[\u064B-\u0652\u0670]")


@dataclass(frozen=True)
class ComplianceMatch:
    mandatory_item: MandatoryListItem
    match_type: str  # "item_code" | "description_ar" | "description_en"
    score: float


def find_mandatory_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    """Find the best mandatory-list match for a single BoQ item.

    Strategy: exact code match first (fast), then fuzzy name match against
    both Arabic and English names. Returns None if no match ≥ threshold.
    """
    # Stage 1: exact code match.
    code_match = _find_code_match(boq_item, mandatory_items)
    if code_match is not None:
        return code_match

    # Stage 2: fuzzy name match.
    return _find_fuzzy_name_match(boq_item, mandatory_items)


def _find_code_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    normalized_code = _normalize_code(boq_item.item_code)
    if not normalized_code:
        return None
    for mandatory_item in mandatory_items:
        if _normalize_code(mandatory_item.item_code) == normalized_code:
            return ComplianceMatch(
                mandatory_item=mandatory_item,
                match_type="item_code",
                score=100.0,
            )
    return None


def _find_fuzzy_name_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    """Fuzzy-match the BoQ description against Arabic + English product names.

    Builds a list of (normalised_name, item, lang) tuples and runs
    rapidfuzz.process.extractOnce with token_set_ratio.
    """
    if not boq_item.description or not mandatory_items:
        return None

    threshold = settings.compliance_fuzzy_match_threshold  # default 80
    query = _normalize_text(boq_item.description)

    # Build parallel lists: choices[i] = normalised name, items[i] = (item, lang).
    choices: list[str] = []
    meta: list[tuple[MandatoryListItem, str]] = []  # (item, "ar"|"en")

    for item in mandatory_items:
        ar_name = _normalize_text(item.product_name or "")
        if ar_name:
            choices.append(ar_name)
            meta.append((item, "ar"))
        en_name = _normalize_text(item.product_name_en or "")
        if en_name:
            choices.append(en_name)
            meta.append((item, "en"))

    if not choices:
        return None

    # process.extractOne over a list returns (match_string, score, index).
    # Try token_set_ratio first (handles word reordering well), then fall back
    # to partial_ratio (handles substring matches — useful when the mandatory
    # name is very long and the BoQ description is a short substring).
    match = process.extractOne(
        query,
        choices,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold,
    )
    if match is None:
        # Fallback: partial_ratio — better for short queries against long names.
        match = process.extractOne(
            query,
            choices,
            scorer=fuzz.partial_ratio,
            score_cutoff=threshold,
        )
    if match is None:
        return None

    _, score, index = match
    mandatory_item, lang = meta[index]
    return ComplianceMatch(
        mandatory_item=mandatory_item,
        match_type=f"description_{lang}",
        score=score,
    )


def _normalize_code(item_code: str) -> str:
    """Normalise an item code: lowercase, strip, collapse whitespace."""
    if not item_code:
        return ""
    return " ".join(str(item_code).strip().lower().split())


def _normalize_text(text: str) -> str:
    """Normalise text for fuzzy matching (Arabic + Latin).

    Steps (order matters):
      1. Apply Arabic letter normalisation FIRST (أ→ا, ة→ه, ى→ي, etc.) on
         the raw string — these are precomposed characters that NFKD would
         split into base+hamza, breaking the translate map.
      2. Remove tatweel (ـ).
      3. Strip Arabic diacritics (tashkeel).
      4. NFKD unicode normalisation for Latin diacritics.
      5. Lowercase + collapse whitespace.
    """
    if not text:
        return ""
    s = text
    # 1. Arabic letter normalisation (precomposed forms).
    s = s.translate(_ARABIC_NORMALISATIONS)
    # 2. Remove tatweel (already done by translate map, but double-check).
    s = s.replace("ـ", "")
    # 3. Strip Arabic diacritics (tashkeel).
    s = _DIACRITICS_PATTERN.sub("", s)
    # 4. NFKD for Latin diacritics (é → e, etc.).
    s = unicodedata.normalize("NFKD", s)
    # 5. Lowercase + collapse whitespace.
    s = " ".join(s.lower().split())
    return s
