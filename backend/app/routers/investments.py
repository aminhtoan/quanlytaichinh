from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import mongo
from app.db.mongo import create_transaction
from app.dependencies import get_current_user
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentResponse,
    InvestmentSellRequest,
    InvestmentUpdateValueRequest,
)
from app.services.wallet_service import adjust_wallet_balance

router = APIRouter()


@router.post("", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(payload: InvestmentCreate, current_user=Depends(get_current_user)):
    try:
        await adjust_wallet_balance(current_user["id"], payload.wallet_id, -payload.principal_amount)
    except ValueError as exc:
        message = str(exc)
        if message == "Insufficient balance":
            raise HTTPException(status_code=400, detail="Ví không đủ tiền") from exc
        raise HTTPException(status_code=404, detail="Không tìm thấy ví") from exc

    now = datetime.now(timezone.utc)
    data = {
        **payload.model_dump(),
        "user_id": current_user["id"],
        "current_value": payload.principal_amount,
        "status": "active",
        "created_at": now,
    }

    if mongo.using_memory():
        data["id"] = uuid4().hex
        mongo.memory_store["investments"].append(data)
        created = data
    else:
        result = await mongo.database.investments.insert_one(data)
        data["_id"] = result.inserted_id
        created = mongo.to_object_id(data)

    await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": payload.wallet_id,
            "type": "expense",
            "amount": payload.principal_amount,
            "category": "Đầu tư",
            "note": f"Mua đầu tư: {payload.name}",
            "transaction_date": now,
        }
    )

    return created


@router.post("/{investment_id}/transactions")
async def sell_investment(
    investment_id: str,
    payload: InvestmentSellRequest,
    current_user=Depends(get_current_user),
):
    if mongo.using_memory():
        investment = next(
            (
                item
                for item in mongo.memory_store["investments"]
                if item["id"] == investment_id and item["user_id"] == current_user["id"]
            ),
            None,
        )
    else:
        from bson import ObjectId

        item = await mongo.database.investments.find_one(
            {"_id": ObjectId(investment_id), "user_id": current_user["id"]}
        )
        investment = mongo.to_object_id(item) if item else None

    if not investment:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản đầu tư")

    if investment.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Khoản đầu tư đã đóng")

    profit = payload.selling_price - float(investment["principal_amount"])
    roi = (profit / float(investment["principal_amount"])) * 100

    try:
        await adjust_wallet_balance(current_user["id"], payload.wallet_id, payload.selling_price)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Không tìm thấy ví nhận") from exc

    sold_at = payload.date or datetime.now(timezone.utc)

    update_data = {
        "wallet_id": payload.wallet_id,
        "current_value": payload.selling_price,
        "status": "closed",
        "closed_at": sold_at,
        "profit": round(profit, 2),
        "roi": round(roi, 2),
    }

    if mongo.using_memory():
        investment.update(update_data)
    else:
        from bson import ObjectId

        await mongo.database.investments.update_one(
            {"_id": ObjectId(investment_id), "user_id": current_user["id"]},
            {"$set": update_data},
        )

    transaction = await create_transaction(
        {
            "user_id": current_user["id"],
            "wallet_id": payload.wallet_id,
            "type": "income",
            "amount": payload.selling_price,
            "category": "Hoàn vốn đầu tư",
            "note": f"Bán đầu tư: {investment['name']}",
            "transaction_date": sold_at,
        }
    )

    return {
        "profit": round(profit, 2),
        "roi": round(roi, 2),
        "transaction_id": transaction["id"],
    }


@router.put("/{investment_id}/update")
async def update_investment_value(
    investment_id: str,
    payload: InvestmentUpdateValueRequest,
    current_user=Depends(get_current_user),
):
    if mongo.using_memory():
        investment = next(
            (
                item
                for item in mongo.memory_store["investments"]
                if item["id"] == investment_id and item["user_id"] == current_user["id"]
            ),
            None,
        )
    else:
        from bson import ObjectId

        item = await mongo.database.investments.find_one(
            {"_id": ObjectId(investment_id), "user_id": current_user["id"]}
        )
        investment = mongo.to_object_id(item) if item else None

    if not investment:
        raise HTTPException(status_code=404, detail="Không tìm thấy khoản đầu tư")

    principal = float(investment["principal_amount"])
    profit = payload.current_value - principal
    profit_percent = (profit / principal) * 100

    if mongo.using_memory():
        investment["current_value"] = payload.current_value
        investment["updated_at"] = datetime.now(timezone.utc)
    else:
        from bson import ObjectId

        await mongo.database.investments.update_one(
            {"_id": ObjectId(investment_id), "user_id": current_user["id"]},
            {"$set": {"current_value": payload.current_value, "updated_at": datetime.now(timezone.utc)}},
        )

    return {
        "profit": round(profit, 2),
        "profit_percent": round(profit_percent, 2),
    }
