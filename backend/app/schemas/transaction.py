from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["income", "expense"]


class TransactionBase(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0)
    category: str = Field(min_length=2, max_length=100)
    wallet_id: str | None = None
    category_id: str | None = None
    note: str = Field(default="", max_length=300)
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: float | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    note: str | None = Field(default=None, max_length=300)
    transaction_date: datetime | None = None


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class SummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    by_category: dict[str, float]


class TransactionQueryResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    size: int
