import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.boq_item import BoQItem, SourcingType
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus, ViolationType
from app.models.mandatory_list import MandatoryListItem, MandatoryStatus
from app.models.user import User
from app.schemas.compliance import ComplianceScanResult, FlagStatusUpdate, MandatoryListUploadResult
from app.services.mandatory_list_parser import MandatoryListParserResult, parse_mandatory_list_file
from app.services.matching_engine import find_mandatory_match
from app.services.project_service import get_project

logger = logging.getLogger(__name__)

DEFAULT_PENALTY_PERCENTAGE = Decimal("0.30")


def upload_mandatory_list(db: Session, file: UploadFile) -> MandatoryListUploadResult:
    try:
        parser_result = parse_mandatory_list_file(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for validation_error in parser_result.validation_errors:
        logger.warning("Skipped invalid mandatory list row", extra={"error": validation_error})

    if parser_result.rows:
        _upsert_mandatory_items(db, parser_result)

    result = MandatoryListUploadResult(
        imported_rows=len(parser_result.rows),
        failed_rows=parser_result.failed_rows,
        validation_errors=parser_result.validation_errors,
    )
    _write_mandatory_upload_audit_log(file.filename or "unknown", result)
    return result


def scan_project_compliance(
    db: Session,
    project_id: UUID,
    current_user: User,
) -> ComplianceScanResult:
    get_project(db, project_id, current_user)

    imported_items = list(
        db.scalars(
            select(BoQItem).where(
                BoQItem.project_id == project_id,
                BoQItem.sourcing_type == SourcingType.IMPORTED,
            )
        ).all()
    )
    mandatory_items = list(
        db.scalars(
            select(MandatoryListItem).where(
                MandatoryListItem.mandatory_status.in_(
                    [MandatoryStatus.MANDATORY, MandatoryStatus.ACTIVE]
                )
            )
        ).all()
    )

    flags: list[ComplianceFlag] = []
    for boq_item in imported_items:
        match = find_mandatory_match(boq_item, mandatory_items)
        if match is None:
            continue

        exposure_amount = boq_item.total_price * DEFAULT_PENALTY_PERCENTAGE
        flags.append(
            ComplianceFlag(
                project_id=project_id,
                boq_item_id=boq_item.id,
                mandatory_item_id=match.mandatory_item.id,
                violation_type=ViolationType.IMPORTED_MANDATORY_ITEM,
                penalty_percentage=DEFAULT_PENALTY_PERCENTAGE,
                exposure_amount=exposure_amount,
            )
        )

    # Preserve manually-waived/resolved flags across rescans.
    # Only OPEN flags are deleted and recomputed; WAIVED/RESOLVED flags carry an
    # audit trail (waived_by, waived_at, waiver_reason) that must survive rescans.
    preserved_flags = list(
        db.scalars(
            select(ComplianceFlag).where(
                ComplianceFlag.project_id == project_id,
                ComplianceFlag.status.in_(
                    [ComplianceFlagStatus.WAIVED, ComplianceFlagStatus.RESOLVED]
                ),
            )
        ).all()
    )
    preserved_keys = {(f.boq_item_id, f.mandatory_item_id): f for f in preserved_flags}

    # Merge: recompute OPEN flags, keep preserved ones, drop OPEN flags that no longer match.
    existing_open = list(
        db.scalars(
            select(ComplianceFlag).where(
                ComplianceFlag.project_id == project_id,
                ComplianceFlag.status == ComplianceFlagStatus.OPEN,
            )
        ).all()
    )
    new_keys = {(f.boq_item_id, f.mandatory_item_id) for f in flags}
    for stale in existing_open:
        if (stale.boq_item_id, stale.mandatory_item_id) not in new_keys:
            db.delete(stale)

    # Upsert OPEN flags: update exposure/penalty if the (boq, mandatory) pair already exists as OPEN.
    open_by_key = {(f.boq_item_id, f.mandatory_item_id): f for f in existing_open}
    for flag in flags:
        key = (flag.boq_item_id, flag.mandatory_item_id)
        if key in preserved_keys:
            # Keep the preserved flag as-is; do not re-add.
            continue
        existing_open_flag = open_by_key.get(key)
        if existing_open_flag is not None:
            existing_open_flag.exposure_amount = flag.exposure_amount
            existing_open_flag.penalty_percentage = flag.penalty_percentage
        else:
            db.add(flag)
    db.flush()
    db.commit()

    total_exposure = sum((flag.exposure_amount for flag in flags), Decimal("0"))
    result = ComplianceScanResult(
        total_scanned_items=len(imported_items),
        matched_violations=len(flags),
        total_exposure=total_exposure,
        compliance_status="violations_found" if flags else "compliant",
        flags=flags,
    )
    _write_scan_audit_log(project_id, result)
    return result


def list_project_compliance_flags(
    db: Session,
    project_id: UUID,
    current_user: User,
) -> list[ComplianceFlag]:
    get_project(db, project_id, current_user)
    statement = (
        select(ComplianceFlag)
        .where(ComplianceFlag.project_id == project_id)
        .order_by(ComplianceFlag.created_at.desc())
    )
    return list(db.scalars(statement).all())


def enrich_compliance_flag(flag: ComplianceFlag) -> dict:
    return {
        "id": flag.id,
        "project_id": flag.project_id,
        "boq_item_id": flag.boq_item_id,
        "mandatory_item_id": flag.mandatory_item_id,
        "violation_type": flag.violation_type,
        "penalty_percentage": flag.penalty_percentage,
        "exposure_amount": flag.exposure_amount,
        "status": flag.status,
        "created_at": flag.created_at,
        "updated_at": getattr(flag, "updated_at", None),
        "waived_by": getattr(flag, "waived_by", None),
        "waived_at": getattr(flag, "waived_at", None),
        "waiver_reason": getattr(flag, "waiver_reason", None),
        "waiver_strategy_id": getattr(flag, "waiver_strategy_id", None),
        "boq_item_code": flag.boq_item.item_code if flag.boq_item else None,
        "boq_description": flag.boq_item.description if flag.boq_item else None,
        "mandatory_product_name": (
            flag.mandatory_item.product_name if flag.mandatory_item else None
        ),
    }


# Default cap: total waived exposure may not exceed 10% of the project's total BoQ value.
DEFAULT_WAIVER_CAP_PERCENTAGE = Decimal("0.10")


def update_flag_status(
    db: Session,
    flag_id: UUID,
    payload: FlagStatusUpdate,
    current_user: User,
) -> ComplianceFlag:
    """Waive or resolve a compliance flag with a full audit trail.

    Enforces the waiver cap: the sum of exposure_amount of all WAIVED flags for
    the project must not exceed waiver_cap_pct × project_budget. Resolving a flag
    does not count toward the cap.
    """
    flag = db.scalar(select(ComplianceFlag).where(ComplianceFlag.id == flag_id))
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance flag not found.")

    # Ownership: confirm the acting user owns the project the flag belongs to.
    get_project(db, flag.project_id, current_user)

    # Only allow transition out of OPEN (you cannot re-waive an already-waived flag
    # without first reopening it via an admin endpoint — not implemented here).
    if flag.status != ComplianceFlagStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Flag is already in status '{flag.status.value}'. Only OPEN flags can be waived/resolved.",
        )

    if payload.status == ComplianceFlagStatus.WAIVED:
        _enforce_waiver_cap(db, flag.project_id, flag.exposure_amount)

    flag.status = payload.status
    flag.waived_by = current_user.id
    flag.waived_at = datetime.now(UTC)
    flag.waiver_reason = payload.waiver_reason
    if payload.waiver_strategy_id is not None:
        flag.waiver_strategy_id = payload.waiver_strategy_id

    db.commit()
    db.refresh(flag)
    _write_flag_status_audit_log(flag, current_user, payload)
    return flag


def _enforce_waiver_cap(db: Session, project_id: UUID, additional_exposure: Decimal) -> None:
    """Raise 422 if waiving additional_exposure would exceed the project waiver cap."""
    already_waived = db.scalar(
        select(func.sum(ComplianceFlag.exposure_amount)).where(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == ComplianceFlagStatus.WAIVED,
        )
    ) or Decimal("0")
    project_budget = db.scalar(
        select(func.sum(BoQItem.total_price)).where(BoQItem.project_id == project_id)
    ) or Decimal("0")

    if project_budget <= 0:
        return  # cannot enforce a cap against an unknown budget

    cap_amount = project_budget * DEFAULT_WAIVER_CAP_PERCENTAGE
    projected_waived = already_waived + additional_exposure
    if projected_waived > cap_amount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Waiver cap exceeded. Project cap = {cap_amount:.2f} SAR "
                f"({DEFAULT_WAIVER_CAP_PERCENTAGE * 100:.0f}% of budget). "
                f"Already waived = {already_waived:.2f} SAR, this waiver = {additional_exposure:.2f} SAR, "
                f"total would be {projected_waived:.2f} SAR."
            ),
        )


def _write_flag_status_audit_log(
    flag: ComplianceFlag,
    actor: User,
    payload: FlagStatusUpdate,
) -> None:
    log_dir = Path(settings.compliance_scan_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "flag_status_changes.jsonl"
    entry = {
        "event": "compliance_flag_status_changed",
        "flag_id": str(flag.id),
        "project_id": str(flag.project_id),
        "actor_id": str(actor.id),
        "actor_email": actor.email,
        "new_status": payload.status.value,
        "waiver_reason": payload.waiver_reason,
        "waiver_strategy_id": str(payload.waiver_strategy_id) if payload.waiver_strategy_id else None,
        "exposure_amount": str(flag.exposure_amount),
        "changed_at": datetime.now(UTC).isoformat(),
    }
    with log_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry) + "\n")


def _upsert_mandatory_items(db: Session, parser_result: MandatoryListParserResult) -> None:
    bind = db.get_bind()
    values_by_code = {
        row.item_code: {
            "item_code": row.item_code,
            "product_name": row.product_name,
            "category": row.category,
            "local_manufacturer": row.local_manufacturer,
            "mandatory_status": row.mandatory_status,
        }
        for row in parser_result.rows
    }
    values = list(values_by_code.values())

    if bind.dialect.name == "postgresql":
        statement = postgresql_insert(MandatoryListItem).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=[MandatoryListItem.item_code],
            set_={
                "product_name": statement.excluded.product_name,
                "category": statement.excluded.category,
                "local_manufacturer": statement.excluded.local_manufacturer,
                "mandatory_status": statement.excluded.mandatory_status,
            },
        )
        db.execute(statement)
        db.commit()
        return

    for value in values:
        existing_item = db.scalar(
            select(MandatoryListItem).where(MandatoryListItem.item_code == value["item_code"])
        )
        if existing_item is None:
            db.add(MandatoryListItem(**value))
            continue

        existing_item.product_name = value["product_name"]
        existing_item.category = value["category"]
        existing_item.local_manufacturer = value["local_manufacturer"]
        existing_item.mandatory_status = value["mandatory_status"]

    db.commit()


def _write_scan_audit_log(project_id: UUID, result: ComplianceScanResult) -> None:
    log_dir = Path(settings.compliance_scan_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{project_id}.jsonl"
    payload = {
        "event": "compliance_scan_completed",
        "project_id": str(project_id),
        "total_scanned_items": result.total_scanned_items,
        "matched_violations": result.matched_violations,
        "total_exposure": str(result.total_exposure),
        "compliance_status": result.compliance_status,
        "created_at": datetime.now(UTC).isoformat(),
    }

    with log_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload) + "\n")


def _write_mandatory_upload_audit_log(filename: str, result: MandatoryListUploadResult) -> None:
    log_dir = Path(settings.compliance_scan_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "mandatory_list_uploads.jsonl"
    payload = {
        "event": "mandatory_list_upload_completed",
        "filename": filename,
        "imported_rows": result.imported_rows,
        "failed_rows": result.failed_rows,
        "validation_errors": result.validation_errors,
        "created_at": datetime.now(UTC).isoformat(),
    }

    with log_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload) + "\n")
