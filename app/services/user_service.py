from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.user import UserRole
from app.schemas.user import UserRead


def _get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def list_users(session: Session) -> list[UserRead]:
    statement = select(User).order_by(User.created_at.desc(), User.id.desc())
    users = session.scalars(statement).all()
    return [UserRead.model_validate(user) for user in users]


def update_user_role(session: Session, user_id: int, role: UserRole) -> UserRead:
    user = _get_user_or_404(session, user_id)
    user.role = role
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)


def update_user_status(session: Session, user_id: int, is_active: bool) -> UserRead:
    user = _get_user_or_404(session, user_id)
    user.is_active = is_active
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead.model_validate(user)
