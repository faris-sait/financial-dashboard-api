from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.responses import success_response
from app.db.session import get_db
from app.dependencies.rate_limit import rate_limit_dependency
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserRead
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _auth_max_requests() -> int:
    return get_settings().auth_rate_limit_requests


def _auth_window_seconds() -> int:
    return get_settings().auth_rate_limit_window_seconds


register_rate_limiter = rate_limit_dependency(
    bucket="auth:register",
    max_requests=_auth_max_requests,
    window_seconds=_auth_window_seconds,
)

login_rate_limiter = rate_limit_dependency(
    bucket="auth:login",
    max_requests=_auth_max_requests,
    window_seconds=_auth_window_seconds,
)


@router.post(
    "/register",
    response_model=ApiResponse[UserRead],
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    status_code=status.HTTP_201_CREATED,
    summary="Register a new viewer account",
)
def register(
    payload: RegisterRequest,
    session: Session = Depends(get_db),
    _: None = Depends(register_rate_limiter),
):
    user = register_user(session, payload)
    return success_response(user)


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    summary="Authenticate and receive a JWT access token",
)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_db),
    _: None = Depends(login_rate_limiter),
):
    auth_payload = login_user(session, payload)
    return success_response(auth_payload)
