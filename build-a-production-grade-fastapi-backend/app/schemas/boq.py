from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.boq_item import SourcingType


class BoQItemRead(BaseModel):
    id: UUID
    project_id: UUID
    uploaded_file_id: UUID
    item_code: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    sourcing_type: SourcingType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoQParseResult(BaseModel):
    parsed_rows: int
    failed_rows: int
    validation_errors: list[str]
    items: list[BoQItemRead]
