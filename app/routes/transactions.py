from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.db.session import get_db
from app.dependencies.auth import enforce_deleted_transaction_access, require_roles
from app.models import TransactionType, User, UserRole
from app.schemas.common import ApiResponse, ErrorResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListData,
    TransactionRead,
    TransactionUpdate,
)
from app.services.transaction_service import (
    create_transaction,
    get_transaction_by_id,
    list_transactions,
    restore_transaction,
    soft_delete_transaction,
    update_transaction,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)


@router.post(
    "",
    response_model=ApiResponse[TransactionRead],
    responses={404: {"model": ErrorResponse}},
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial transaction",
)
def create_transaction_endpoint(
    payload: TransactionCreate,
    user_id: int | None = Query(
        default=None,
        ge=1,
        description="Admin-only override: create a transaction for another user id.",
    ),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    owner_user_id = user_id if current_user.role == UserRole.admin and user_id is not None else current_user.id
    return success_response(
        create_transaction(
            session,
            payload,
            owner_user_id=owner_user_id,
        )
    )


@router.get(
    "",
    response_model=ApiResponse[TransactionListData],
    summary="List transactions with filters, search, and pagination",
)
def list_transactions_endpoint(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    category: str | None = Query(default=None, min_length=1, max_length=100),
    transaction_type: TransactionType | None = Query(default=None, alias="type"),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    include_deleted: bool = Query(
        default=False,
        description="Admins can set this to true to include soft-deleted transactions.",
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.analyst, UserRole.admin)),
):
    enforce_deleted_transaction_access(
        include_deleted=include_deleted,
        current_user=current_user,
    )
    scope_user_id = None if current_user.role == UserRole.admin else current_user.id
    transactions = list_transactions(
        session,
        start_date=start_date,
        end_date=end_date,
        category=category,
        transaction_type=transaction_type,
        search=search,
        page=page,
        limit=limit,
        include_deleted=include_deleted,
        scope_user_id=scope_user_id,
    )
    return success_response(transactions)


@router.get(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionRead],
    responses={404: {"model": ErrorResponse}},
    summary="Get a transaction by id",
)
def get_transaction_endpoint(
    transaction_id: int = Path(ge=1),
    include_deleted: bool = Query(
        default=False,
        description="Admins can set this to true to retrieve a soft-deleted transaction.",
    ),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.analyst, UserRole.admin)),
):
    enforce_deleted_transaction_access(
        include_deleted=include_deleted,
        current_user=current_user,
    )
    scope_user_id = None if current_user.role == UserRole.admin else current_user.id
    return success_response(
        get_transaction_by_id(
            session,
            transaction_id,
            include_deleted=include_deleted,
            scope_user_id=scope_user_id,
        )
    )


@router.put(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionRead],
    responses={404: {"model": ErrorResponse}},
    summary="Update an existing transaction",
)
def update_transaction_endpoint(
    payload: TransactionUpdate,
    transaction_id: int = Path(ge=1),
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(update_transaction(session, transaction_id, payload))


@router.delete(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionRead],
    responses={404: {"model": ErrorResponse}},
    summary="Soft delete a transaction",
)
def delete_transaction_endpoint(
    transaction_id: int = Path(ge=1),
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(soft_delete_transaction(session, transaction_id))


@router.patch(
    "/{transaction_id}/restore",
    response_model=ApiResponse[TransactionRead],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Restore a soft-deleted transaction",
)
def restore_transaction_endpoint(
    transaction_id: int = Path(ge=1),
    session: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.admin)),
):
    return success_response(restore_transaction(session, transaction_id))
