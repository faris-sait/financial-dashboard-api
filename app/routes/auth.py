from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.user import UserRead
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[UserRead],
    responses={400: {"model": ErrorResponse}},
    status_code=status.HTTP_201_CREATED,
    summary="Register a new viewer account",
)
def register(payload: RegisterRequest, session: Session = Depends(get_db)):
    user = register_user(session, payload)
    return success_response(user)


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponse],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Authenticate and receive a JWT access token",
)
def login(payload: LoginRequest, session: Session = Depends(get_db)):
    auth_payload = login_user(session, payload)
    return success_response(auth_payload)
