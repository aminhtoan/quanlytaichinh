from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category_id: str
    amount_limit: float = Field(gt=0)
    period: Literal["weekly", "monthly", "quarterly", "yearly"] = "monthly"
    start_date: datetime
    end_date: datetime


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    amount_limit: float
    period: str
    start_date: datetime
    end_date: datetime
    created_at: datetime


class BudgetProgressItem(BaseModel):
    budget_id: str
    category_name: str
    limit: float
    spent: float
    remaining: float
    warning: bool
