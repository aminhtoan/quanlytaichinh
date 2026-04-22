from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.db import mongo
from app.db.mongo import list_transactions
from app.dependencies import get_current_user
from app.schemas.ai import ChatRequest
from app.services.ai_service import ask_gemini, build_spending_ratio, generate_local_finance_answer

router = APIRouter()


async def _append_chat_message(user_id: str, session_id: str, sender: str, text: str) -> None:
    message = {"sender": sender, "text": text, "created_at": datetime.now(timezone.utc)}
    if mongo.using_memory():
        row = next(
            (
                item
                for item in mongo.memory_store["chat_sessions"]
                if item["session_id"] == session_id and item["user_id"] == user_id
            ),
            None,
        )
        if not row:
            mongo.memory_store["chat_sessions"].append(
                {
                    "id": uuid4().hex,
                    "session_id": session_id,
                    "user_id": user_id,
                    "messages": [message],
                    "created_at": datetime.now(timezone.utc),
                }
            )
            return

        row.setdefault("messages", []).append(message)
        return

    await mongo.database.chat_sessions.update_one(
        {"session_id": session_id, "user_id": user_id},
        {
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            "$push": {"messages": message},
        },
        upsert=True,
    )


@router.post("/ask")
async def ask_chatbot(payload: ChatRequest, current_user=Depends(get_current_user)):
    message = (payload.message or payload.question or "").strip()
    if not message:
        raise HTTPException(status_code=422, detail="Thiếu nội dung câu hỏi")

    records = await list_transactions(current_user["id"])
    ratio = build_spending_ratio(records)
    context = f"Spending ratio: {ratio}"

    answer = ask_gemini(message, context)
    if not answer:
        answer = generate_local_finance_answer(message, ratio, records)

    session_id = payload.session_id or str(uuid4())
    await _append_chat_message(current_user["id"], session_id, "user", message)
    await _append_chat_message(current_user["id"], session_id, "bot", answer)

    return {
        "reply": answer,
        "chart_data": {"spending_ratio": ratio},
        "session_id": session_id,
    }
