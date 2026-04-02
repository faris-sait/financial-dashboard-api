from __future__ import annotations

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models import UserRole
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserRead, UserRoleUpdate, UserStatusUpdate
from app.services.user_service import list_users, update_user_role, update_user_status

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get(
    "",
    response_model=ApiResponse[list[UserRead]],
    summary="List all registered users",
)
def list_users_endpoint(
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(list_users(session))


@router.patch(
    "/{user_id}/role",
    response_model=ApiResponse[UserRead],
    responses={404: {"model": ErrorResponse}},
    summary="Update a user's role",
)
def update_user_role_endpoint(
    payload: UserRoleUpdate,
    user_id: int = Path(ge=1),
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(update_user_role(session, user_id, payload.role))


@router.patch(
    "/{user_id}/status",
    response_model=ApiResponse[UserRead],
    responses={404: {"model": ErrorResponse}},
    summary="Activate or deactivate a user account",
)
def update_user_status_endpoint(
    payload: UserStatusUpdate,
    user_id: int = Path(ge=1),
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(update_user_status(session, user_id, payload.is_active))
