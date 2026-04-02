from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models import User, UserRole
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.dashboard import CategoryTotal, DashboardSummary, TrendGroupBy, TrendPoint
from app.schemas.transaction import TransactionRead
from app.services.dashboard_service import (
    get_category_totals,
    get_dashboard_summary,
    get_dashboard_trends,
    get_recent_transactions,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.get(
    "/summary",
    response_model=ApiResponse[DashboardSummary],
    summary="Get overall income, expense, and balance totals",
)
def dashboard_summary(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
):
    return success_response(get_dashboard_summary(session, user_id=current_user.id))


@router.get(
    "/categories",
    response_model=ApiResponse[list[CategoryTotal]],
    summary="Get category-wise transaction totals",
)
def dashboard_categories(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
):
    return success_response(get_category_totals(session, user_id=current_user.id))


@router.get(
    "/trends",
    response_model=ApiResponse[list[TrendPoint]],
    summary="Get aggregated transaction trends by month or week",
)
def dashboard_trends(
    group_by: TrendGroupBy = Query(default=TrendGroupBy.month),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
):
    return success_response(get_dashboard_trends(session, group_by, user_id=current_user.id))


@router.get(
    "/recent",
    response_model=ApiResponse[list[TransactionRead]],
    summary="Get the five most recent non-deleted transactions",
)
def dashboard_recent(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.viewer, UserRole.analyst, UserRole.admin)),
):
    return success_response(get_recent_transactions(session, user_id=current_user.id))
