from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import mongo
from app.dependencies import get_current_user
from app.schemas.budget import BudgetCreate, BudgetProgressItem, BudgetResponse

router = APIRouter()


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def _find_category(category_id: str) -> dict | None:
    if mongo.using_memory():
        return next((item for item in mongo.memory_store["categories"] if item["id"] == category_id), None)

    from bson import ObjectId

    item = await mongo.database.categories.find_one({"_id": ObjectId(category_id)})
    return mongo.to_object_id(item) if item else None


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(payload: BudgetCreate, current_user=Depends(get_current_user)):
    if payload.start_date >= payload.end_date:
        raise HTTPException(status_code=400, detail="Khoảng thời gian ngân sách không hợp lệ")

    category = await _find_category(payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")

    if not category.get("is_system") and category.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền dùng danh mục này")

    data = {
        **payload.model_dump(),
        "user_id": current_user["id"],
        "start_date": _to_utc(payload.start_date),
        "end_date": _to_utc(payload.end_date),
        "created_at": datetime.now(timezone.utc),
    }

    if mongo.using_memory():
        data["id"] = uuid4().hex
        mongo.memory_store["budgets"].append(data)
        return data

    result = await mongo.database.budgets.insert_one(data)
    data["_id"] = result.inserted_id
    return mongo.to_object_id(data)


@router.get("/progress", response_model=list[BudgetProgressItem])
async def budget_progress(
    period: str = Query(default="monthly"),
    current_user=Depends(get_current_user),
):
    if mongo.using_memory():
        budgets = [
            item
            for item in mongo.memory_store["budgets"]
            if item["user_id"] == current_user["id"] and item["period"] == period
        ]
        transactions = [
            item for item in mongo.memory_store["transactions"] if item.get("user_id") == current_user["id"]
        ]
    else:
        budgets_cursor = mongo.database.budgets.find({"user_id": current_user["id"], "period": period})
        budgets = [mongo.to_object_id(item) async for item in budgets_cursor]
        transactions_cursor = mongo.database.transactions.find({"user_id": current_user["id"]})
        transactions = [mongo.to_object_id(item) async for item in transactions_cursor]

    result: list[BudgetProgressItem] = []
    for budget in budgets:
        category = await _find_category(budget["category_id"])
        category_name = category["name"] if category else "Khác"
        start = _to_utc(budget["start_date"])
        end = _to_utc(budget["end_date"])

        spent = 0.0
        for txn in transactions:
            if txn.get("type") != "expense":
                continue
            txn_date = txn.get("transaction_date")
            if not isinstance(txn_date, datetime):
                continue
            txn_date = _to_utc(txn_date)
            if not (start <= txn_date <= end):
                continue

            matched = txn.get("category_id") == budget["category_id"] or txn.get("category") == category_name
            if matched:
                spent += float(txn.get("amount", 0))

        limit = float(budget["amount_limit"])
        remaining = limit - spent
        result.append(
            BudgetProgressItem(
                budget_id=budget["id"],
                category_name=category_name,
                limit=round(limit, 2),
                spent=round(spent, 2),
                remaining=round(remaining, 2),
                warning=spent >= limit,
            )
        )

    return result
