from __future__ import annotations

from datetime import datetime
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType, User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListData,
    TransactionRead,
    TransactionUpdate,
)


def _get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def _get_transaction_or_404(
    session: Session,
    transaction_id: int,
    *,
    include_deleted: bool = False,
    scope_user_id: int | None = None,
) -> Transaction:
    statement = select(Transaction).where(Transaction.id == transaction_id)
    if scope_user_id is not None:
        statement = statement.where(Transaction.user_id == scope_user_id)
    if not include_deleted:
        statement = statement.where(Transaction.is_deleted.is_(False))

    transaction = session.scalar(statement)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )
    return transaction


def _apply_filters(
    statement: Select[tuple[Transaction]],
    *,
    start_date: datetime | None,
    end_date: datetime | None,
    category: str | None,
    transaction_type: TransactionType | None,
    search: str | None,
) -> Select[tuple[Transaction]]:
    if start_date is not None:
        statement = statement.where(Transaction.date >= start_date)
    if end_date is not None:
        statement = statement.where(Transaction.date <= end_date)
    if category:
        statement = statement.where(Transaction.category.ilike(category.strip()))
    if transaction_type is not None:
        statement = statement.where(Transaction.type == transaction_type)
    if search:
        wildcard = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Transaction.category.ilike(wildcard),
                Transaction.description.ilike(wildcard),
            )
        )
    return statement


def create_transaction(
    session: Session,
    payload: TransactionCreate,
    *,
    owner_user_id: int,
) -> TransactionRead:
    _get_user_or_404(session, owner_user_id)

    transaction = Transaction(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        description=payload.description,
        user_id=owner_user_id,
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return TransactionRead.model_validate(transaction)


def list_transactions(
    session: Session,
    *,
    start_date: datetime | None,
    end_date: datetime | None,
    category: str | None,
    transaction_type: TransactionType | None,
    search: str | None,
    page: int,
    limit: int,
    include_deleted: bool = False,
    scope_user_id: int | None = None,
) -> TransactionListData:
    base_statement = select(Transaction)
    if scope_user_id is not None:
        base_statement = base_statement.where(Transaction.user_id == scope_user_id)
    if not include_deleted:
        base_statement = base_statement.where(Transaction.is_deleted.is_(False))
    filtered_statement = _apply_filters(
        base_statement,
        start_date=start_date,
        end_date=end_date,
        category=category,
        transaction_type=transaction_type,
        search=search,
    )

    total = session.scalar(select(func.count()).select_from(filtered_statement.subquery())) or 0
    items_statement = (
        filtered_statement
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    transactions = session.scalars(items_statement).all()
    total_pages = ceil(total / limit) if total else 0

    return TransactionListData(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        items=[TransactionRead.model_validate(transaction) for transaction in transactions],
    )


def get_transaction_by_id(
    session: Session,
    transaction_id: int,
    *,
    include_deleted: bool = False,
    scope_user_id: int | None = None,
) -> TransactionRead:
    transaction = _get_transaction_or_404(
        session,
        transaction_id,
        include_deleted=include_deleted,
        scope_user_id=scope_user_id,
    )
    return TransactionRead.model_validate(transaction)


def update_transaction(
    session: Session,
    transaction_id: int,
    payload: TransactionUpdate,
) -> TransactionRead:
    transaction = _get_transaction_or_404(session, transaction_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "user_id" in update_data:
        _get_user_or_404(session, update_data["user_id"])

    for field_name, value in update_data.items():
        setattr(transaction, field_name, value)

    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return TransactionRead.model_validate(transaction)


def soft_delete_transaction(session: Session, transaction_id: int) -> TransactionRead:
    transaction = _get_transaction_or_404(session, transaction_id)
    transaction.is_deleted = True
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return TransactionRead.model_validate(transaction)


def restore_transaction(session: Session, transaction_id: int) -> TransactionRead:
    transaction = _get_transaction_or_404(
        session,
        transaction_id,
        include_deleted=True,
    )
    if not transaction.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not deleted.",
        )

    transaction.is_deleted = False
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return TransactionRead.model_validate(transaction)
