from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InvestmentCreate(BaseModel):
    wallet_id: str
    name: str = Field(min_length=2, max_length=120)
    type: Literal["gold", "stock", "fund", "crypto", "other"]
    principal_amount: float = Field(gt=0)


class InvestmentSellRequest(BaseModel):
    selling_price: float = Field(gt=0)
    wallet_id: str
    date: datetime | None = None


class InvestmentUpdateValueRequest(BaseModel):
    current_value: float = Field(gt=0)


class InvestmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    wallet_id: str
    name: str
    type: str
    principal_amount: float
    current_value: float
    status: str
    created_at: datetime
