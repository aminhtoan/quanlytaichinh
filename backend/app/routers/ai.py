from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi import File, Form, HTTPException, UploadFile

from app.db import mongo
from app.db.mongo import create_transaction, list_transactions
from app.dependencies import get_current_user
from app.schemas.ai import (
    AiInsightResponse,
    AiParseRequest,
    AiParseResponse,
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
)
from app.services.ai_service import (
    ask_gemini,
    build_recommendations,
    build_spending_ratio,
    detect_anomalies,
    generate_local_finance_answer,
)
from app.services.nlp_service import parse_natural_transaction
from app.services.ocr_service import extract_text_from_image_bytes
from app.services.ocr_service import OcrServiceError
from app.services.wallet_service import adjust_wallet_balance, list_wallets_by_user

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


async def _get_chat_messages(user_id: str, session_id: str) -> list[dict] | None:
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
            return None
        return row.get("messages", [])

    row = await mongo.database.chat_sessions.find_one({"session_id": session_id, "user_id": user_id})
    if not row:
        return None
    return row.get("messages", [])


@router.get("/insights", response_model=AiInsightResponse)
async def insights(current_user=Depends(get_current_user)):
    records = await list_transactions(current_user["id"])
    ratio = build_spending_ratio(records)
    anomalies = detect_anomalies(records)
    recommendations = build_recommendations(ratio)

    return AiInsightResponse(
        spending_ratio=ratio,
        anomalies=anomalies,
        recommendations=recommendations,
    )


@router.post("/parse", response_model=AiParseResponse)
async def ai_parse(payload: AiParseRequest, current_user=Depends(get_current_user)):
    _ = current_user
    parsed = parse_natural_transaction(payload.text)
    return AiParseResponse(
        amount=parsed.amount,
        transaction_type=parsed.type,
        category=parsed.category,
        note=parsed.note,
    )


@router.post("/ocr")
async def ai_ocr(
    file: UploadFile = File(...),
    wallet_id: str | None = Form(default=None),
    auto_save: bool = Form(default=True),
    current_user=Depends(get_current_user),
):
    _ = current_user
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File không hợp lệ")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="File rỗng")

    try:
        text = extract_text_from_image_bytes(image_bytes)
    except OcrServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    parsed = parse_natural_transaction(text if text else "chi 0")
    safe_note = (parsed.note or text or "OCR hoa don").strip()
    if len(safe_note) > 280:
        safe_note = f"{safe_note[:277]}..."

    selected_wallet_id = wallet_id
    if not selected_wallet_id:
        wallets = await list_wallets_by_user(current_user["id"])
        selected_wallet_id = wallets[0]["id"] if wallets else None

    created_transaction = None
    auto_saved = False
    auto_save_reason = None

    if auto_save:
        if not selected_wallet_id:
            auto_save_reason = "Chua co vi. Vui long tao vi truoc khi OCR tu dong luu giao dich"
        else:
            delta = -parsed.amount if parsed.type == "expense" else parsed.amount
            try:
                await adjust_wallet_balance(current_user["id"], selected_wallet_id, delta)
                created_transaction = await create_transaction(
                    {
                        "user_id": current_user["id"],
                        "wallet_id": selected_wallet_id,
                        "type": parsed.type,
                        "amount": parsed.amount,
                        "category": parsed.category if len(parsed.category) >= 2 else "Khac",
                        "note": safe_note,
                        "transaction_date": parsed.transaction_date,
                    }
                )
                auto_saved = True
            except ValueError as exc:
                if str(exc) == "Insufficient balance":
                    auto_save_reason = "Vi da chon khong du so du de luu giao dich OCR"
                elif str(exc) == "Wallet not found":
                    auto_save_reason = "Khong tim thay vi de luu giao dich OCR"
                else:
                    auto_save_reason = f"Khong the luu giao dich OCR: {exc}"

    return {
        "merchant": safe_note[:80] if safe_note else "Khong xac dinh",
        "total": parsed.amount,
        "date": parsed.transaction_date,
        "items": [],
        "ocr_data": {"raw_text": text},
        "suggested_transaction": {
            "type": parsed.type,
            "amount": parsed.amount,
            "category": parsed.category,
            "note": safe_note,
            "wallet_id": selected_wallet_id,
            "transaction_date": parsed.transaction_date,
        },
        "auto_saved": auto_saved,
        "auto_save_reason": auto_save_reason,
        "created_transaction": created_transaction,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, current_user=Depends(get_current_user)):
    question = (payload.question or payload.message or "").strip()
    if not question:
        raise HTTPException(status_code=422, detail="Thiếu nội dung câu hỏi")

    records = await list_transactions(current_user["id"])
    ratio = build_spending_ratio(records)
    context = f"Spending ratio: {ratio}"

    ai_answer = ask_gemini(question, context)
    if ai_answer:
        answer = ai_answer
    else:
        answer = generate_local_finance_answer(question, ratio, records)

    session_id = payload.session_id or str(uuid4())
    await _append_chat_message(current_user["id"], session_id, "user", question)
    await _append_chat_message(current_user["id"], session_id, "bot", answer)

    return ChatResponse(answer=answer, session_id=session_id)


@router.get("/chat/{session_id}", response_model=list[ChatHistoryItem])
async def chat_history(session_id: str, current_user=Depends(get_current_user)):
    messages = await _get_chat_messages(current_user["id"], session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy session")

    return [ChatHistoryItem(sender=item.get("sender", "bot"), text=item.get("text", "")) for item in messages]
