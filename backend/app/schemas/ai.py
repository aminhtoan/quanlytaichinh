from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str | None = None
    message: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str | None = None


class AiInsightResponse(BaseModel):
    spending_ratio: dict[str, float]
    anomalies: list[dict]
    recommendations: list[str]


class AiParseRequest(BaseModel):
    text: str


class AiParseResponse(BaseModel):
    amount: float
    transaction_type: str
    category: str
    note: str


class ChatHistoryItem(BaseModel):
    sender: str
    text: str
