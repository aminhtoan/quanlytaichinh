from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import mongo
from app.dependencies import get_current_user
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionDetectResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
)

router = APIRouter()


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(payload: SubscriptionCreate, current_user=Depends(get_current_user)):
    if payload.next_due_date and payload.next_due_date < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="next_due_date không được trong quá khứ")

    now = datetime.now(timezone.utc)
    data = {
        **payload.model_dump(),
        "user_id": current_user["id"],
        "is_active": True,
        "created_at": now,
    }

    if mongo.using_memory():
        data["id"] = uuid4().hex
        mongo.memory_store["subscriptions"].append(data)
        return data

    result = await mongo.database.subscriptions.insert_one(data)
    data["_id"] = result.inserted_id
    return mongo.to_object_id(data)


@router.get("/detect", response_model=list[SubscriptionDetectResponse])
async def detect_subscriptions(current_user=Depends(get_current_user)):
    if mongo.using_memory():
        transactions = [
            item for item in mongo.memory_store["transactions"] if item.get("user_id") == current_user["id"]
        ]
    else:
        cursor = mongo.database.transactions.find({"user_id": current_user["id"], "type": "expense"})
        transactions = [mongo.to_object_id(item) async for item in cursor]

    frequency_map: dict[tuple[str, float], int] = {}
    for item in transactions:
        if item.get("type") != "expense":
            continue
        key = (item.get("note") or item.get("category") or "Khoản định kỳ", float(item.get("amount", 0)))
        frequency_map[key] = frequency_map.get(key, 0) + 1

    suggestions = [
        SubscriptionDetectResponse(name=name, amount=amount, confidence=min(0.99, count / 5))
        for (name, amount), count in sorted(frequency_map.items(), key=lambda row: row[1], reverse=True)
        if count >= 2 and amount > 0
    ]

    return suggestions[:10]


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    active: bool | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    if mongo.using_memory():
        rows = [item for item in mongo.memory_store["subscriptions"] if item["user_id"] == current_user["id"]]
        if active is not None:
            rows = [item for item in rows if item.get("is_active") == active]
        rows.sort(key=lambda item: item["created_at"], reverse=True)
        return rows

    query: dict = {"user_id": current_user["id"]}
    if active is not None:
        query["is_active"] = active

    cursor = mongo.database.subscriptions.find(query).sort("created_at", -1)
    return [mongo.to_object_id(item) async for item in cursor]


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    payload: SubscriptionUpdate,
    current_user=Depends(get_current_user),
):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="Không có dữ liệu cập nhật")

    if mongo.using_memory():
        for item in mongo.memory_store["subscriptions"]:
            if item["id"] == subscription_id and item["user_id"] == current_user["id"]:
                item.update(data)
                return item
        raise HTTPException(status_code=404, detail="Không tìm thấy subscription")

    from bson import ObjectId

    await mongo.database.subscriptions.update_one(
        {"_id": ObjectId(subscription_id), "user_id": current_user["id"]},
        {"$set": data},
    )
    item = await mongo.database.subscriptions.find_one(
        {"_id": ObjectId(subscription_id), "user_id": current_user["id"]}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy subscription")
    return mongo.to_object_id(item)


@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: str, current_user=Depends(get_current_user)):
    if mongo.using_memory():
        for item in mongo.memory_store["subscriptions"]:
            if item["id"] == subscription_id and item["user_id"] == current_user["id"]:
                item["is_active"] = False
                return {"message": "Deleted"}
        raise HTTPException(status_code=404, detail="Không tìm thấy subscription")

    from bson import ObjectId

    result = await mongo.database.subscriptions.update_one(
        {"_id": ObjectId(subscription_id), "user_id": current_user["id"]},
        {"$set": {"is_active": False}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy subscription")

    return {"message": "Deleted"}
