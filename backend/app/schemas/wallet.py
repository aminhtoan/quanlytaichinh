from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WalletCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    type: Literal["cash", "bank", "ewallet", "credit", "other"] = "cash"
    currency: str = "VND"
    initial_balance: float = Field(default=0, ge=0)


class WalletUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    type: Literal["cash", "bank", "ewallet", "credit", "other"] | None = None
    currency: str | None = None


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    currency: str
    balance: float
    created_at: datetime
    updated_at: datetime
