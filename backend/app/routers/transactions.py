from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import mongo
from app.db.mongo import (
    create_transaction,
    delete_transaction,
    list_transactions,
    update_transaction,
)
from app.dependencies import get_current_user
from app.services.wallet_service import adjust_wallet_balance
from app.schemas.transaction import (
    SummaryResponse,
    TransactionCreate,
    TransactionQueryResponse,
    TransactionResponse,
    TransactionUpdate,
)

router = APIRouter()


async def _get_transaction_by_id(user_id: str, transaction_id: str) -> dict | None:
    if mongo.using_memory():
        return next(
            (
                item
                for item in mongo.memory_store["transactions"]
                if item["id"] == transaction_id and item["user_id"] == user_id
            ),
            None,
        )

    from bson import ObjectId

    item = await mongo.database.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": user_id}
    )
    return mongo.to_object_id(item) if item else None


async def _apply_wallet_effect(user_id: str, transaction: dict, *, reverse: bool = False) -> None:
    wallet_id = transaction.get("wallet_id")
    if not wallet_id:
        return

    amount = float(transaction.get("amount", 0))
    if amount <= 0:
        return

    transaction_type = transaction.get("type")
    if transaction_type == "expense":
        delta = amount if reverse else -amount
    else:
        delta = -amount if reverse else amount

    try:
        await adjust_wallet_balance(user_id, wallet_id, delta)
    except ValueError as exc:
        message = str(exc)
        if message == "Insufficient balance":
            raise HTTPException(status_code=400, detail="Ví không đủ tiền") from exc
        raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc


@router.get("", response_model=list[TransactionResponse])
async def get_transactions(current_user=Depends(get_current_user)):
    return await list_transactions(current_user["id"])


@router.get("/query", response_model=TransactionQueryResponse)
async def query_transactions(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    wallet_id: str | None = Query(default=None),
    type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    current_user=Depends(get_current_user),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date phải nhỏ hơn end_date")

    records = await list_transactions(current_user["id"])

    filtered = records
    if start_date:
        filtered = [item for item in filtered if item.get("transaction_date") >= start_date]
    if end_date:
        filtered = [item for item in filtered if item.get("transaction_date") <= end_date]
    if wallet_id:
        filtered = [item for item in filtered if item.get("wallet_id") == wallet_id]
    if type:
        filtered = [item for item in filtered if item.get("type") == type]

    total = len(filtered)
    start_index = (page - 1) * size
    end_index = start_index + size

    return TransactionQueryResponse(items=filtered[start_index:end_index], total=total, page=page, size=size)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_transaction(payload: TransactionCreate, current_user=Depends(get_current_user)):
    await _apply_wallet_effect(current_user["id"], payload.model_dump(), reverse=False)
    return await create_transaction({**payload.model_dump(), "user_id": current_user["id"]})


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def edit_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user=Depends(get_current_user),
):
    old_transaction = await _get_transaction_by_id(current_user["id"], transaction_id)
    if not old_transaction:
        raise HTTPException(status_code=404, detail="Khong tim thay giao dich")

    await _apply_wallet_effect(current_user["id"], old_transaction, reverse=True)

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    new_transaction = {**old_transaction, **update_data}
    await _apply_wallet_effect(current_user["id"], new_transaction, reverse=False)

    updated = await update_transaction(
        current_user["id"],
        transaction_id,
        update_data,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Khong tim thay giao dich")
    return updated


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_transaction(transaction_id: str, current_user=Depends(get_current_user)):
    old_transaction = await _get_transaction_by_id(current_user["id"], transaction_id)
    if not old_transaction:
        raise HTTPException(status_code=404, detail="Khong tim thay giao dich")

    await _apply_wallet_effect(current_user["id"], old_transaction, reverse=True)

    deleted = await delete_transaction(current_user["id"], transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Khong tim thay giao dich")
    return None


@router.post("/transfer")
async def transfer_between_wallets(payload: dict, current_user=Depends(get_current_user)):
    source_wallet_id = payload.get("source_wallet_id")
    dest_wallet_id = payload.get("dest_wallet_id")
    amount = float(payload.get("amount", 0))
    note = payload.get("note", "Chuyển tiền")
    date_value = payload.get("date")

    if not source_wallet_id or not dest_wallet_id:
        raise HTTPException(status_code=400, detail="Thiếu source_wallet_id hoặc dest_wallet_id")
    if source_wallet_id == dest_wallet_id:
        raise HTTPException(status_code=400, detail="Không thể chuyển cùng một ví")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền chuyển phải lớn hơn 0")

    transaction_date = datetime.fromisoformat(date_value) if date_value else datetime.utcnow()

    try:
        await adjust_wallet_balance(current_user["id"], source_wallet_id, -amount)
        await adjust_wallet_balance(current_user["id"], dest_wallet_id, amount, allow_negative=True)
    except ValueError as exc:
        message = str(exc)
        if message == "Insufficient balance":
            raise HTTPException(status_code=400, detail="Ví nguồn không đủ tiền") from exc
        raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

    outgoing = await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": source_wallet_id,
            "type": "expense",
            "amount": amount,
            "category": "Chuyển tiền",
            "note": f"{note} (đến ví {dest_wallet_id})",
            "transaction_date": transaction_date,
        }
    )

    incoming = await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": dest_wallet_id,
            "type": "income",
            "amount": amount,
            "category": "Nhận chuyển tiền",
            "note": f"{note} (từ ví {source_wallet_id})",
            "transaction_date": transaction_date,
        }
    )

    return {"transaction_ids": [outgoing["id"], incoming["id"]], "message": "Success"}


@router.get("/summary/overview", response_model=SummaryResponse)
async def summary(current_user=Depends(get_current_user)):
    records = await list_transactions(current_user["id"])
    total_income = sum(float(item["amount"]) for item in records if item["type"] == "income")
    total_expense = sum(float(item["amount"]) for item in records if item["type"] == "expense")

    by_category: dict[str, float] = {}
    for item in records:
        key = item["category"]
        by_category[key] = by_category.get(key, 0) + float(item["amount"])

    return SummaryResponse(
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        balance=round(total_income - total_expense, 2),
        by_category=by_category,
    )
