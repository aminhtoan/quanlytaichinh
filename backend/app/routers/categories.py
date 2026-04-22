from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import mongo
from app.dependencies import get_current_user
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter()

DEFAULT_CATEGORIES = [
    {"name": "Ăn uống", "type": "expense", "parent_id": None, "icon": "utensils"},
    {"name": "Di chuyển", "type": "expense", "parent_id": None, "icon": "car"},
    {"name": "Giải trí", "type": "expense", "parent_id": None, "icon": "film"},
    {"name": "Lương", "type": "income", "parent_id": None, "icon": "wallet"},
    {"name": "Thưởng", "type": "income", "parent_id": None, "icon": "gift"},
]


async def ensure_default_categories(user_id: str) -> None:
    now = datetime.now(timezone.utc)
    if mongo.using_memory():
        has_system = any(item.get("is_system") for item in mongo.memory_store["categories"])
        if not has_system:
            for item in DEFAULT_CATEGORIES:
                mongo.memory_store["categories"].append(
                    {
                        "id": uuid4().hex,
                        **item,
                        "is_system": True,
                        "user_id": None,
                        "created_at": now,
                    }
                )
        return

    has_system = await mongo.database.categories.count_documents({"is_system": True}, limit=1)
    if has_system:
        return

    await mongo.database.categories.insert_many(
        [
            {
                **item,
                "is_system": True,
                "user_id": None,
                "created_at": now,
            }
            for item in DEFAULT_CATEGORIES
        ]
    )


@router.get("", response_model=list[CategoryResponse])
async def get_categories(current_user=Depends(get_current_user)):
    await ensure_default_categories(current_user["id"])

    if mongo.using_memory():
        items = [
            item.copy()
            for item in mongo.memory_store["categories"]
            if item.get("is_system") or item.get("user_id") == current_user["id"]
        ]
        items.sort(key=lambda row: row["created_at"], reverse=True)
        return items

    cursor = mongo.database.categories.find(
        {"$or": [{"is_system": True}, {"user_id": current_user["id"]}]}
    ).sort("created_at", -1)
    rows = []
    async for item in cursor:
        rows.append(mongo.to_object_id(item))
    return rows


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def add_category(payload: CategoryCreate, current_user=Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    data = {
        **payload.model_dump(),
        "is_system": False,
        "user_id": current_user["id"],
        "created_at": now,
    }

    if mongo.using_memory():
        data["id"] = uuid4().hex
        mongo.memory_store["categories"].append(data)
        return data

    result = await mongo.database.categories.insert_one(data)
    data["_id"] = result.inserted_id
    return mongo.to_object_id(data)
