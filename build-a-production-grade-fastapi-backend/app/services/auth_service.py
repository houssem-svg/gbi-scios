# app/services/auth_service.py

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    needs_rehash,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.user_service import get_user_by_email


def register_user(db: Session, payload: RegisterRequest) -> TokenResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # SECURITY: self-registration is always CLIENT — no privilege escalation.
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        hashed_password=get_password_hash(payload.password),
        role=UserRole.CLIENT,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        ) from exc

    db.refresh(user)
    return _build_token_response(user)


def authenticate_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Transparent upgrade: if the stored hash is a legacy unsalted SHA-256,
    # re-hash with bcrypt now that we have the plaintext password in memory.
    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(payload.password)
        db.commit()

    return _build_token_response(user)


def _build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token, user=user)
