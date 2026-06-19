"""Audit trail service.

Writes immutable records of state-changing actions to the system_audit_logs
table. Read-heavy operations do NOT log here (only writes).
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditAction, SystemAuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    *,
    action: AuditAction,
    target_table: str,
    target_id: str | UUID | None = None,
    project_id: UUID | None = None,
    actor: User | None = None,
    changes: dict[str, Any] | None = None,
    request: Request | None = None,
) -> SystemAuditLog:
    """Append an audit-log entry. Commits immediately so the record survives
    even if the enclosing transaction rolls back.

    NOTE: callers that are mid-transaction should pass a fresh session if they
    want the audit record to be independent of the transaction outcome.
    """
    ip: str | None = None
    if request is not None:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        elif request.client:
            ip = request.client.host

    entry = SystemAuditLog(
        user_id=actor.id if actor else None,
        action=action,
        target_table=target_table,
        target_id=str(target_id) if target_id else None,
        project_id=project_id,
        changes_json=json.dumps(changes, default=str, ensure_ascii=False)
        if changes
        else None,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
