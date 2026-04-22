from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NlpInput(BaseModel):
    text: str
    auto_save: bool = True


class NlpParsedTransaction(BaseModel):
    type: Literal["income", "expense"]
    amount: float
    category: str
    note: str
    transaction_date: datetime
    confidence: float
