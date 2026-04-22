from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    amount: float = Field(gt=0)
    frequency: Literal["weekly", "monthly", "yearly"] = "monthly"
    default_wallet_id: str | None = None
    next_due_date: datetime | None = None


class SubscriptionUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    is_active: bool | None = None
    next_due_date: datetime | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    amount: float
    frequency: str
    default_wallet_id: str | None = None
    next_due_date: datetime | None = None
    is_active: bool
    created_at: datetime


class SubscriptionDetectResponse(BaseModel):
    name: str
    amount: float
    confidence: float
