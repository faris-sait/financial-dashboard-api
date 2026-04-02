from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.transaction import TransactionType


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class TransactionCreate(BaseModel):
    # Ignore unexpected fields like legacy "user_id" from clients.
    model_config = ConfigDict(extra="ignore")

    amount: Decimal = Field(gt=0)
    type: TransactionType
    category: str = Field(min_length=1, max_length=100)
    date: datetime
    description: str | None = Field(default=None, max_length=500)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return _normalize_text(value)


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    type: TransactionType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    date: datetime | None = None
    description: str | None = Field(default=None, max_length=500)
    user_id: int | None = Field(default=None, gt=0)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return _normalize_text(value)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: TransactionType
    category: str
    date: datetime
    description: str | None
    user_id: int
    is_deleted: bool
    created_at: datetime


class TransactionListData(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    items: list[TransactionRead]
