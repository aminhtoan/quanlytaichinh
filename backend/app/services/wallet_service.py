from datetime import datetime, timezone
from uuid import uuid4

from app.db import mongo


def _to_utc(value: datetime | None = None) -> datetime:
    return value or datetime.now(timezone.utc)


async def list_wallets_by_user(user_id: str) -> list[dict]:
    if mongo.using_memory():
        wallets = [item.copy() for item in mongo.memory_store["wallets"] if item["user_id"] == user_id]
        wallets.sort(key=lambda item: item["created_at"], reverse=True)
        return wallets

    cursor = mongo.database.wallets.find({"user_id": user_id}).sort("created_at", -1)
    result: list[dict] = []
    async for item in cursor:
        result.append(mongo.to_object_id(item))
    return result


async def get_wallet_by_id(user_id: str, wallet_id: str) -> dict | None:
    if mongo.using_memory():
        wallet = next(
            (item for item in mongo.memory_store["wallets"] if item["id"] == wallet_id and item["user_id"] == user_id),
            None,
        )
        return wallet.copy() if wallet else None

    from bson import ObjectId

    wallet = await mongo.database.wallets.find_one({"_id": ObjectId(wallet_id), "user_id": user_id})
    return mongo.to_object_id(wallet) if wallet else None


async def create_wallet(user_id: str, payload: dict) -> dict:
    now = _to_utc()
    data = {
        "user_id": user_id,
        "name": payload["name"],
        "type": payload["type"],
        "currency": payload.get("currency", "VND"),
        "balance": float(payload.get("initial_balance", 0)),
        "created_at": now,
        "updated_at": now,
    }

    if mongo.using_memory():
        data["id"] = uuid4().hex
        mongo.memory_store["wallets"].append(data)
        return data.copy()

    result = await mongo.database.wallets.insert_one(data)
    data["_id"] = result.inserted_id
    return mongo.to_object_id(data)


async def update_wallet(user_id: str, wallet_id: str, update_data: dict) -> dict | None:
    if not update_data:
        return await get_wallet_by_id(user_id, wallet_id)

    update_data["updated_at"] = _to_utc()

    if mongo.using_memory():
        for wallet in mongo.memory_store["wallets"]:
            if wallet["id"] == wallet_id and wallet["user_id"] == user_id:
                wallet.update(update_data)
                return wallet.copy()
        return None

    from bson import ObjectId

    await mongo.database.wallets.update_one(
        {"_id": ObjectId(wallet_id), "user_id": user_id},
        {"$set": update_data},
    )
    return await get_wallet_by_id(user_id, wallet_id)


async def delete_wallet(user_id: str, wallet_id: str) -> bool:
    if mongo.using_memory():
        initial_len = len(mongo.memory_store["wallets"])
        mongo.memory_store["wallets"] = [
            item
            for item in mongo.memory_store["wallets"]
            if not (item["id"] == wallet_id and item["user_id"] == user_id)
        ]
        return len(mongo.memory_store["wallets"]) < initial_len

    from bson import ObjectId

    result = await mongo.database.wallets.delete_one({"_id": ObjectId(wallet_id), "user_id": user_id})
    return result.deleted_count > 0


async def adjust_wallet_balance(
    user_id: str,
    wallet_id: str,
    delta: float,
    *,
    allow_negative: bool = False,
) -> dict:
    wallet = await get_wallet_by_id(user_id, wallet_id)
    if not wallet:
        raise ValueError("Wallet not found")

    new_balance = float(wallet.get("balance", 0)) + float(delta)
    if not allow_negative and new_balance < 0:
        raise ValueError("Insufficient balance")

    updated = await update_wallet(user_id, wallet_id, {"balance": new_balance})
    if not updated:
        raise ValueError("Wallet update failed")
    return updated
