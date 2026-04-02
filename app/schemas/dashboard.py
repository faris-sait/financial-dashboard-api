from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TrendGroupBy(str, Enum):
    month = "month"
    week = "week"


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float


class CategoryTotal(BaseModel):
    category: str
    total: float


class TrendPoint(BaseModel):
    period_start: datetime
    total_income: float
    total_expense: float
    net_balance: float
