from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import mongo
from app.db.mongo import create_transaction
from app.dependencies import get_current_user
from app.schemas.debt import DebtCreate, DebtRepayRequest, DebtResponse
from app.services.wallet_service import adjust_wallet_balance

router = APIRouter()


@router.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
async def create_debt(payload: DebtCreate, current_user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)

    if payload.type == "receivable":
        try:
            await adjust_wallet_balance(current_user["id"], payload.wallet_id, -payload.total_amount)
        except ValueError as exc:
            message = str(exc)
            if message == "Insufficient balance":
                raise HTTPException(status_code=400, detail="Ví không đủ tiền để cho vay") from exc
            raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

        transaction_type = "expense"
        transaction_category = "Cho vay"
    else:
        try:
            await adjust_wallet_balance(current_user["id"], payload.wallet_id, payload.total_amount, allow_negative=True)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

        transaction_type = "income"
        transaction_category = "Đi vay"

    debt_data = {
        **payload.model_dump(),
        "user_id": current_user["id"],
        "remaining_amount": payload.total_amount,
        "status": "active",
        "created_at": now,
    }

    if mongo.using_memory():
        debt_data["id"] = uuid4().hex
        mongo.memory_store["debts"].append(debt_data)
        created = debt_data
    else:
        result = await mongo.database.debts.insert_one(debt_data)
        debt_data["_id"] = result.inserted_id
        created = mongo.to_object_id(debt_data)

    await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": payload.wallet_id,
            "type": transaction_type,
            "amount": payload.total_amount,
            "category": transaction_category,
            "note": f"{transaction_category}: {payload.creditor_name}",
            "transaction_date": now,
        }
    )

    return created


@router.post("/{debt_id}/repay")
async def repay_debt(debt_id: str, payload: DebtRepayRequest, current_user=Depends(get_current_user)):
    if mongo.using_memory():
        debt = next(
            (
                item
                for item in mongo.memory_store["debts"]
                if item["id"] == debt_id and item["user_id"] == current_user["id"]
            ),
            None,
        )
    else:
        from bson import ObjectId

        item = await mongo.database.debts.find_one({"_id": ObjectId(debt_id), "user_id": current_user["id"]})
        debt = mongo.to_object_id(item) if item else None

    if not debt:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản nợ")

    if payload.amount > float(debt["remaining_amount"]):
        raise HTTPException(status_code=400, detail="Số tiền trả vượt quá số nợ còn lại")

    repayment_date = payload.date or datetime.now(timezone.utc)

    if debt["type"] == "payable":
        try:
            await adjust_wallet_balance(current_user["id"], payload.wallet_id, -payload.amount)
        except ValueError as exc:
            message = str(exc)
            if message == "Insufficient balance":
                raise HTTPException(status_code=400, detail="Ví không đủ tiền để trả nợ") from exc
            raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

        txn_type = "expense"
        txn_category = "Trả nợ"
    else:
        try:
            await adjust_wallet_balance(current_user["id"], payload.wallet_id, payload.amount, allow_negative=True)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

        txn_type = "income"
        txn_category = "Thu nợ"

    remaining = round(float(debt["remaining_amount"]) - payload.amount, 2)
    status_value = "closed" if remaining <= 0 else "active"

    if mongo.using_memory():
        debt["remaining_amount"] = remaining
        debt["status"] = status_value
        mongo.memory_store["debt_repayments"].append(
            {
                "id": uuid4().hex,
                "debt_id": debt_id,
                "amount": payload.amount,
                "wallet_id": payload.wallet_id,
                "created_at": repayment_date,
            }
        )
    else:
        from bson import ObjectId

        await mongo.database.debts.update_one(
            {"_id": ObjectId(debt_id), "user_id": current_user["id"]},
            {"$set": {"remaining_amount": remaining, "status": status_value}},
        )
        await mongo.database.debt_repayments.insert_one(
            {
                "debt_id": debt_id,
                "user_id": current_user["id"],
                "amount": payload.amount,
                "wallet_id": payload.wallet_id,
                "created_at": repayment_date,
            }
        )

    transaction = await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": payload.wallet_id,
            "type": txn_type,
            "amount": payload.amount,
            "category": txn_category,
            "note": f"{txn_category}: {debt['creditor_name']}",
            "transaction_date": repayment_date,
        }
    )

    return {
        "remaining_amount": remaining,
        "status": status_value,
        "transaction_id": transaction["id"],
    }


@router.get("", response_model=list[DebtResponse])
async def list_debts(
    status: str | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    if mongo.using_memory():
        rows = [item for item in mongo.memory_store["debts"] if item["user_id"] == current_user["id"]]
        if status:
            rows = [item for item in rows if item["status"] == status]
        rows.sort(key=lambda item: item["created_at"], reverse=True)
        return rows

    query: dict = {"user_id": current_user["id"]}
    if status:
        query["status"] = status

    cursor = mongo.database.debts.find(query).sort("created_at", -1)
    return [mongo.to_object_id(item) async for item in cursor]
