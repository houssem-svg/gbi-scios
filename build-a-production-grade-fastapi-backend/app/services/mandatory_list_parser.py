from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile

from app.models.mandatory_list import MandatoryStatus

REQUIRED_COLUMNS = {
    "item_code",
    "product_name",
    "category",
    "local_manufacturer",
    "mandatory_status",
}

COLUMN_ALIASES = {
    "item code": "item_code",
    "item_code": "item_code",
    "code": "item_code",
    "product": "product_name",
    "product name": "product_name",
    "product_name": "product_name",
    "name": "product_name",
    "category": "category",
    "local manufacturer": "local_manufacturer",
    "local_manufacturer": "local_manufacturer",
    "manufacturer": "local_manufacturer",
    "mandatory status": "mandatory_status",
    "mandatory_status": "mandatory_status",
    "status": "mandatory_status",
}


@dataclass(frozen=True)
class ParsedMandatoryListRow:
    item_code: str
    product_name: str
    category: str
    local_manufacturer: str
    mandatory_status: MandatoryStatus


@dataclass(frozen=True)
class MandatoryListParserResult:
    rows: list[ParsedMandatoryListRow]
    failed_rows: int
    validation_errors: list[str]


def parse_mandatory_list_file(file: UploadFile) -> MandatoryListParserResult:
    dataframe = _read_file(file)
    dataframe = _normalize_columns(dataframe)

    missing_columns = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing_columns:
        return MandatoryListParserResult(
            rows=[],
            failed_rows=len(dataframe.index),
            validation_errors=[f"Missing required columns: {', '.join(missing_columns)}"],
        )

    rows: list[ParsedMandatoryListRow] = []
    validation_errors: list[str] = []
    failed_rows = 0

    for index, raw_row in dataframe.iterrows():
        parsed_row, row_errors = _parse_row(index + 2, raw_row.to_dict())
        if row_errors:
            failed_rows += 1
            validation_errors.extend(row_errors)
            continue
        rows.append(parsed_row)

    return MandatoryListParserResult(
        rows=rows,
        failed_rows=failed_rows,
        validation_errors=validation_errors,
    )


def _read_file(file: UploadFile) -> pd.DataFrame:
    extension = Path(file.filename or "").suffix.lower()
    file.file.seek(0)
    if extension == ".csv":
        return pd.read_csv(file.file)
    if extension == ".xlsx":
        return pd.read_excel(file.file, engine="openpyxl")
    if extension == ".xls":
        return pd.read_excel(file.file, engine="xlrd")
    raise ValueError("Only Excel and CSV files can be uploaded as a mandatory list")


def _normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized_columns = {}
    for column in dataframe.columns:
        normalized = str(column).strip().lower().replace("-", " ").replace(".", " ")
        normalized = " ".join(normalized.split())
        normalized_columns[column] = COLUMN_ALIASES.get(normalized, normalized.replace(" ", "_"))
    return dataframe.rename(columns=normalized_columns)


def _parse_row(
    row_number: int,
    row: dict[str, Any],
) -> tuple[ParsedMandatoryListRow | None, list[str]]:
    errors: list[str] = []
    item_code = _as_text(row.get("item_code"))
    product_name = _as_text(row.get("product_name"))
    category = _as_text(row.get("category"))
    local_manufacturer = _as_text(row.get("local_manufacturer"))
    mandatory_status = _as_status(row.get("mandatory_status"))

    if not item_code:
        errors.append(f"Row {row_number}: item_code is required")
    if not product_name:
        errors.append(f"Row {row_number}: product_name is required")
    if not category:
        errors.append(f"Row {row_number}: category is required")
    if not local_manufacturer:
        errors.append(f"Row {row_number}: local_manufacturer is required")

    if errors:
        return None, errors

    return (
        ParsedMandatoryListRow(
            item_code=item_code,
            product_name=product_name,
            category=category,
            local_manufacturer=local_manufacturer,
            mandatory_status=mandatory_status,
        ),
        [],
    )


def _as_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _as_status(value: Any) -> MandatoryStatus:
    if value is None or pd.isna(value):
        return MandatoryStatus.MANDATORY
    normalized = str(value).strip().lower()
    if normalized in {status.value for status in MandatoryStatus}:
        return MandatoryStatus(normalized)
    if normalized in {"yes", "true", "required"}:
        return MandatoryStatus.MANDATORY
    return MandatoryStatus.INACTIVE
