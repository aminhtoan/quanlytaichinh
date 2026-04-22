from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DebtCreate(BaseModel):
    creditor_name: str = Field(min_length=2, max_length=120)
    total_amount: float = Field(gt=0)
    type: Literal["receivable", "payable"]
    wallet_id: str


class DebtRepayRequest(BaseModel):
    amount: float = Field(gt=0)
    wallet_id: str
    date: datetime | None = None


class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creditor_name: str
    total_amount: float
    remaining_amount: float
    type: str
    wallet_id: str
    status: str
    created_at: datetime
