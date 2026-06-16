from dataclasses import dataclass

from rapidfuzz import fuzz, process

from app.core.config import settings
from app.models.boq_item import BoQItem
from app.models.mandatory_list import MandatoryListItem


@dataclass(frozen=True)
class ComplianceMatch:
    mandatory_item: MandatoryListItem
    match_type: str
    score: float


def find_mandatory_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    code_match = _find_code_match(boq_item, mandatory_items)
    if code_match is not None:
        return code_match
    return _find_description_match(boq_item, mandatory_items)


def _find_code_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    normalized_code = _normalize_code(boq_item.item_code)
    for mandatory_item in mandatory_items:
        if _normalize_code(mandatory_item.item_code) == normalized_code:
            return ComplianceMatch(mandatory_item=mandatory_item, match_type="item_code", score=100)
    return None


def _find_description_match(
    boq_item: BoQItem,
    mandatory_items: list[MandatoryListItem],
) -> ComplianceMatch | None:
    choices = {
        mandatory_item.id: mandatory_item.product_name
        for mandatory_item in mandatory_items
        if mandatory_item.product_name
    }
    match = process.extractOne(
        boq_item.description,
        choices,
        scorer=fuzz.token_set_ratio,
        score_cutoff=settings.compliance_fuzzy_match_threshold,
    )
    if match is None:
        return None

    _, score, mandatory_item_id = match
    mandatory_item = next(item for item in mandatory_items if item.id == mandatory_item_id)
    return ComplianceMatch(mandatory_item=mandatory_item, match_type="description", score=score)


def _normalize_code(item_code: str) -> str:
    return item_code.strip().lower()
