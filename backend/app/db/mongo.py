from collections.abc import MutableMapping
from datetime import datetime, timezone
import logging
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
database: Any = None
db_connection_error: str | None = None

memory_store: dict[str, list[dict[str, Any]]] = {
    "users": [],
    "transactions": [],
    "refresh_tokens": [],
    "wallets": [],
    "debts": [],
    "debt_repayments": [],
    "subscriptions": [],
    "investments": [],
    "categories": [],
    "budgets": [],
    "chat_sessions": [],
}


async def connect_db() -> None:
    global client
    global database
    global db_connection_error
    try:
        client = AsyncIOMotorClient(settings.database_url, serverSelectionTimeoutMS=1500)
        await client.admin.command("ping")
        database = client[settings.database_name]
        db_connection_error = None
        logger.info("Connected MongoDB successfully")
    except Exception as exc:
        client = None
        database = None
        db_connection_error = str(exc)
        logger.warning("Cannot connect MongoDB, using in-memory fallback: %s", exc)


async def close_db() -> None:
    if client is not None:
        client.close()


def using_memory() -> bool:
    return database is None


def get_storage_mode() -> str:
    return "memory" if using_memory() else "mongo"


def get_db_connection_error() -> str | None:
    return db_connection_error


def to_object_id(document: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    if "_id" in document:
        document["id"] = str(document.pop("_id"))
    return document


async def create_user(data: dict[str, Any]) -> dict[str, Any]:
    if using_memory():
        record = {
            "id": str(uuid4()),
            **data,
            "created_at": data.get("created_at") or datetime.now(timezone.utc),
        }
        memory_store["users"].append(record)
        return record.copy()

    payload = data.copy()
    payload["created_at"] = payload.get("created_at") or datetime.now(timezone.utc)
    result = await database.users.insert_one(payload)
    payload["_id"] = result.inserted_id
    return to_object_id(payload)


async def find_user_by_email(email: str) -> dict[str, Any] | None:
    if using_memory():
        user = next((u for u in memory_store["users"] if u["email"] == email), None)
        return user.copy() if user else None

    user = await database.users.find_one({"email": email})
    if not user:
        return None
    return to_object_id(user)


async def find_user_by_username(username: str) -> dict[str, Any] | None:
    if using_memory():
        user = next((u for u in memory_store["users"] if u.get("username") == username), None)
        return user.copy() if user else None

    user = await database.users.find_one({"username": username})
    if not user:
        return None
    return to_object_id(user)


async def find_user_by_id(user_id: str) -> dict[str, Any] | None:
    if using_memory():
        user = next((u for u in memory_store["users"] if u["id"] == user_id), None)
        return user.copy() if user else None

    from bson import ObjectId

    user = await database.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    return to_object_id(user)


async def create_transaction(data: dict[str, Any]) -> dict[str, Any]:
    if using_memory():
        record = {
            "id": str(uuid4()),
            **data,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        memory_store["transactions"].append(record)
        return record

    payload = data.copy()
    payload["created_at"] = datetime.now(timezone.utc)
    payload["updated_at"] = datetime.now(timezone.utc)
    result = await database.transactions.insert_one(payload)
    payload["_id"] = result.inserted_id
    return to_object_id(payload)


async def list_transactions(user_id: str) -> list[dict[str, Any]]:
    if using_memory():
        records = [t for t in memory_store["transactions"] if t["user_id"] == user_id]
        return sorted(records, key=lambda item: item["transaction_date"], reverse=True)

    cursor = (
        database.transactions.find({"user_id": user_id})
        .sort("transaction_date", -1)
        .sort("created_at", -1)
    )
    result = []
    async for item in cursor:
        result.append(to_object_id(item))
    return result


async def update_transaction(
    user_id: str, transaction_id: str, data: dict[str, Any]
) -> dict[str, Any] | None:
    if using_memory():
        for item in memory_store["transactions"]:
            if item["id"] == transaction_id and item["user_id"] == user_id:
                item.update(data)
                item["updated_at"] = datetime.now(timezone.utc)
                return item
        return None

    from bson import ObjectId

    data["updated_at"] = datetime.now(timezone.utc)
    await database.transactions.update_one(
        {"_id": ObjectId(transaction_id), "user_id": user_id}, {"$set": data}
    )
    item = await database.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": user_id}
    )
    if not item:
        return None
    return to_object_id(item)


async def delete_transaction(user_id: str, transaction_id: str) -> bool:
    if using_memory():
        initial_len = len(memory_store["transactions"])
        memory_store["transactions"] = [
            t
            for t in memory_store["transactions"]
            if not (t["id"] == transaction_id and t["user_id"] == user_id)
        ]
        return len(memory_store["transactions"]) < initial_len

    from bson import ObjectId

    result = await database.transactions.delete_one(
        {"_id": ObjectId(transaction_id), "user_id": user_id}
    )
    return result.deleted_count > 0


async def save_refresh_token(token: str, user_id: str, expires_at: datetime) -> None:
    payload = {
        "token": token,
        "user_id": user_id,
        "expires_at": expires_at,
        "revoked": False,
        "created_at": datetime.now(timezone.utc),
    }
    if using_memory():
        memory_store["refresh_tokens"].append(payload)
        return

    await database.refresh_tokens.insert_one(payload)


async def find_refresh_token(token: str) -> dict[str, Any] | None:
    if using_memory():
        record = next((item for item in memory_store["refresh_tokens"] if item["token"] == token), None)
        return record.copy() if record else None

    record = await database.refresh_tokens.find_one({"token": token})
    return to_object_id(record) if record else None


async def revoke_refresh_token(token: str) -> None:
    if using_memory():
        for item in memory_store["refresh_tokens"]:
            if item["token"] == token:
                item["revoked"] = True
        return

    await database.refresh_tokens.update_one({"token": token}, {"$set": {"revoked": True}})
