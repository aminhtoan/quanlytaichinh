from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    type: Literal["income", "expense"]
    parent_id: str | None = None
    icon: str | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    parent_id: str | None = None
    icon: str | None = None
    is_system: bool = False
    created_at: datetime
