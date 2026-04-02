from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserRead


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(session: Session, payload: RegisterRequest) -> UserRead:
    normalized_email = _normalize_email(str(payload.email))
    existing_user = session.scalar(select(User).where(User.email == normalized_email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=UserRole.viewer,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)


def login_user(session: Session, payload: LoginRequest) -> LoginResponse:
    normalized_email = _normalize_email(str(payload.email))
    user = session.scalar(select(User).where(User.email == normalized_email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    settings = get_settings()
    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_expire_minutes,
    )
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


def seed_admin_user(session: Session) -> None:
    settings = get_settings()
    admin_email = _normalize_email(str(settings.admin_email))
    existing_user = session.scalar(select(User).where(User.email == admin_email))

    if existing_user is None:
        session.add(
            User(
                email=admin_email,
                password_hash=hash_password(settings.admin_password),
                role=UserRole.admin,
                is_active=True,
            )
        )
        session.commit()
        return

    updated = False
    if existing_user.role != UserRole.admin:
        existing_user.role = UserRole.admin
        updated = True
    if not existing_user.is_active:
        existing_user.is_active = True
        updated = True

    if updated:
        session.add(existing_user)
        session.commit()
