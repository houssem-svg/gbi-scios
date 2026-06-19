from __future__ import annotations

import json
import logging
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import WaiverStrategy
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus
from app.models.user import User, UserRole
from app.services.ai_service import ai_client
from app.services.prompt_builder import build_waiver_prompt

logger = logging.getLogger(__name__)


async def generate_and_save_waiver(
    db: Session,
    project_id: UUID,
    flag_id: UUID,
    actor: User,
) -> WaiverStrategy:
    """Generate a waiver strategy for a specific compliance flag.

    The waiver is bound to a real ComplianceFlag (flag_id) and the actor must be
    a compliance officer (Admin/Consultant). The flag must belong to the given
    project and be OPEN. The generated strategy is persisted in PENDING approval
    status; applying it (setting the flag to WAIVED) is a separate explicit call
    to PATCH /compliance/flags/{flag_id}.
    """
    if actor.role not in (UserRole.ADMIN, UserRole.CONSULTANT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only compliance officers (Admin/Consultant) may generate waiver strategies.",
        )

    flag = db.scalar(select(ComplianceFlag).where(ComplianceFlag.id == flag_id))
    if flag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance flag not found.")
    if flag.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compliance flag does not belong to the specified project.",
        )
    if flag.status != ComplianceFlagStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Flag is already '{flag.status.value}'. Only OPEN flags may receive a waiver strategy.",
        )

    # Build the prompt from REAL flag data (not the previous canned mock).
    flag_data = {
        "issue": f"Imported mandatory item violation — {flag.violation_type.value}",
        "penalty": f"{float(flag.penalty_percentage) * 100:.1f}% deduction",
        "exposure_amount": str(flag.exposure_amount),
        "boq_item_id": str(flag.boq_item_id),
        "mandatory_item_id": str(flag.mandatory_item_id),
    }
    prompt = build_waiver_prompt(flag_data)

    try:
        ai_response = await ai_client.generate_text(prompt)
        parsed = json.loads(ai_response)
    except json.JSONDecodeError as exc:
        logger.warning("AI waiver response was not valid JSON; using fallback template. %s", exc)
        parsed = {
            "justification": "Local market constraints require this exception pending supplier development.",
            "control": "Quarterly compliance audits and a supplier localization plan will be enforced.",
            "probability": "75%",
        }
    except Exception as exc:  # network/LLM failure
        logger.warning("AI waiver generation failed; using fallback template. %s", exc)
        parsed = {
            "justification": "Local market constraints require this exception pending supplier development.",
            "control": "Quarterly compliance audits and a supplier localization plan will be enforced.",
            "probability": "75%",
        }

    waiver = WaiverStrategy(
        project_id=project_id,
        compliance_flag_id=flag.id,
        justification=parsed.get("justification", ""),
        compensating_control=parsed.get("control", ""),
        approval_probability=parsed.get("probability", ""),
        approval_status="PENDING",
        waiver_amount=Decimal(flag.exposure_amount),
    )
    db.add(waiver)
    db.commit()
    db.refresh(waiver)
    return waiver
