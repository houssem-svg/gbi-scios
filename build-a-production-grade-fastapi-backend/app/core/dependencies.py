from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        user_id = UUID(subject)
    except (TypeError, ValueError):
        raise credentials_exception from None

    user = get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency: only Admin role may proceed."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required for this operation.",
        )
    return user


def require_compliance_officer(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency: Admin or Consultant (compliance officer) may proceed.

    Used for waiver approval / flag status changes where CLIENT users are
    not permitted.
    """
    if user.role not in (UserRole.ADMIN, UserRole.CONSULTANT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compliance officer privileges (Admin or Consultant) are required.",
        )
    return user
