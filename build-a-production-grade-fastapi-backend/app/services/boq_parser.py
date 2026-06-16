from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

from app.models.boq_item import SourcingType

REQUIRED_COLUMNS = {"item_code", "description", "quantity", "unit_price"}
OPTIONAL_COLUMNS = {"total_price", "sourcing_type"}

COLUMN_ALIASES = {
    "item code": "item_code",
    "item_code": "item_code",
    "code": "item_code",
    "description": "description",
    "item description": "description",
    "quantity": "quantity",
    "qty": "quantity",
    "unit price": "unit_price",
    "unit_price": "unit_price",
    "price": "unit_price",
    "total price": "total_price",
    "total_price": "total_price",
    "total": "total_price",
    "sourcing type": "sourcing_type",
    "sourcing_type": "sourcing_type",
    "sourcing": "sourcing_type",
}


@dataclass(frozen=True)
class ParsedBoQRow:
    item_code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    sourcing_type: SourcingType


@dataclass(frozen=True)
class BoQParserResult:
    rows: list[ParsedBoQRow]
    failed_rows: int
    validation_errors: list[str]


def parse_boq_file(storage_path: str) -> BoQParserResult:
    path = Path(storage_path)
    dataframe = _read_file(path)
    dataframe = _normalize_columns(dataframe)

    missing_columns = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing_columns:
        return BoQParserResult(
            rows=[],
            failed_rows=len(dataframe.index),
            validation_errors=[f"Missing required columns: {', '.join(missing_columns)}"],
        )

    rows: list[ParsedBoQRow] = []
    validation_errors: list[str] = []
    failed_rows = 0

    for index, raw_row in dataframe.iterrows():
        parsed_row, row_errors = _parse_row(index + 2, raw_row.to_dict())
        if row_errors:
            failed_rows += 1
            validation_errors.extend(row_errors)
            continue
        rows.append(parsed_row)

    return BoQParserResult(rows=rows, failed_rows=failed_rows, validation_errors=validation_errors)


def _read_file(path: Path) -> pd.DataFrame:
    extension = path.suffix.lower()
    if extension == ".csv":
        return pd.read_csv(path)
    if extension in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError("Only Excel and CSV files can be parsed as BoQ data")


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {}
    for column in dataframe.columns:
        normalized = str(column).strip().lower().replace("-", " ").replace(".", " ")
        normalized = " ".join(normalized.split())
        normalized_columns[column] = COLUMN_ALIASES.get(normalized, normalized.replace(" ", "_"))
    return dataframe.rename(columns=normalized_columns)


def _parse_row(row_number: int, row: dict[str, Any]) -> tuple[ParsedBoQRow | None, list[str]]:
    errors: list[str] = []
    item_code = _as_text(row.get("item_code"))
    description = _as_text(row.get("description"))
    quantity = _as_decimal(row.get("quantity"))
    unit_price = _as_decimal(row.get("unit_price"))
    total_price = _as_decimal(row.get("total_price"))
    sourcing_type = _as_sourcing_type(row.get("sourcing_type"))

    if not item_code:
        errors.append(f"Row {row_number}: item_code is required")
    if not description:
        errors.append(f"Row {row_number}: description is required")
    if quantity is None or quantity <= 0:
        errors.append(f"Row {row_number}: quantity must be greater than zero")
    if unit_price is None or unit_price < 0:
        errors.append(f"Row {row_number}: unit_price must be zero or greater")
    if total_price is not None and total_price < 0:
        errors.append(f"Row {row_number}: total_price must be zero or greater")

    if errors:
        return None, errors

    computed_total = total_price if total_price is not None else quantity * unit_price
    return (
        ParsedBoQRow(
            item_code=item_code,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            total_price=computed_total,
            sourcing_type=sourcing_type,
        ),
        [],
    )


def _as_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _as_sourcing_type(value: Any) -> SourcingType:
    if value is None or pd.isna(value):
        return SourcingType.UNKNOWN
    normalized = str(value).strip().lower()
    if normalized in {sourcing_type.value for sourcing_type in SourcingType}:
        return SourcingType(normalized)
    return SourcingType.UNKNOWN
