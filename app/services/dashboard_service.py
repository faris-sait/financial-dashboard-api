from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType
from app.schemas.dashboard import CategoryTotal, DashboardSummary, TrendGroupBy, TrendPoint
from app.schemas.transaction import TransactionRead


def _as_float(value: Decimal | int | float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def get_dashboard_summary(session: Session, *, user_id: int) -> DashboardSummary:
    income_case = case((Transaction.type == TransactionType.income, Transaction.amount), else_=0)
    expense_case = case((Transaction.type == TransactionType.expense, Transaction.amount), else_=0)

    statement = select(
        func.coalesce(func.sum(income_case), 0).label("total_income"),
        func.coalesce(func.sum(expense_case), 0).label("total_expense"),
    ).where(
        Transaction.is_deleted.is_(False),
        Transaction.user_id == user_id,
    )

    result = session.execute(statement).one()
    total_income = _as_float(result.total_income)
    total_expense = _as_float(result.total_expense)

    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
    )


def get_category_totals(session: Session, *, user_id: int) -> list[CategoryTotal]:
    statement = (
        select(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(
            Transaction.is_deleted.is_(False),
            Transaction.user_id == user_id,
        )
        .group_by(Transaction.category)
        .order_by(desc("total"), Transaction.category.asc())
    )

    rows = session.execute(statement).all()
    return [CategoryTotal(category=row.category, total=_as_float(row.total)) for row in rows]


def _get_bucket_expression(session: Session, group_by: TrendGroupBy):
    dialect = session.bind.dialect.name if session.bind is not None else ""
    if dialect == "postgresql":
        return func.date_trunc(group_by.value, Transaction.date)
    if group_by == TrendGroupBy.month:
        return func.strftime("%Y-%m-01T00:00:00", Transaction.date)
    return func.strftime("%Y-%W", Transaction.date)


def _normalize_period_start(value: datetime | date | str, group_by: TrendGroupBy) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    if group_by == TrendGroupBy.month:
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    return datetime.strptime(f"{value}-1", "%Y-%W-%w").replace(tzinfo=timezone.utc)


def get_dashboard_trends(session: Session, group_by: TrendGroupBy, *, user_id: int) -> list[TrendPoint]:
    bucket = _get_bucket_expression(session, group_by).label("period_start")
    income_case = case((Transaction.type == TransactionType.income, Transaction.amount), else_=0)
    expense_case = case((Transaction.type == TransactionType.expense, Transaction.amount), else_=0)

    statement = (
        select(
            bucket,
            func.coalesce(func.sum(income_case), 0).label("total_income"),
            func.coalesce(func.sum(expense_case), 0).label("total_expense"),
        )
        .where(
            Transaction.is_deleted.is_(False),
            Transaction.user_id == user_id,
        )
        .group_by(bucket)
        .order_by(bucket.asc())
    )

    rows = session.execute(statement).all()
    trend_points: list[TrendPoint] = []
    for row in rows:
        total_income = _as_float(row.total_income)
        total_expense = _as_float(row.total_expense)
        trend_points.append(
            TrendPoint(
                period_start=_normalize_period_start(row.period_start, group_by),
                total_income=total_income,
                total_expense=total_expense,
                net_balance=total_income - total_expense,
            )
        )
    return trend_points


def get_recent_transactions(session: Session, *, user_id: int) -> list[TransactionRead]:
    statement = (
        select(Transaction)
        .where(
            Transaction.is_deleted.is_(False),
            Transaction.user_id == user_id,
        )
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(5)
    )
    transactions = session.scalars(statement).all()
    return [TransactionRead.model_validate(transaction) for transaction in transactions]
