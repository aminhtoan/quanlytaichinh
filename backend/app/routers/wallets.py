from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import mongo
from app.db.mongo import create_transaction
from app.dependencies import get_current_user
from app.schemas.wallet import WalletCreate, WalletResponse, WalletUpdate
from app.services.wallet_service import (
    create_wallet,
    delete_wallet,
    list_wallets_by_user,
    update_wallet,
)

router = APIRouter()


@router.get("", response_model=list[WalletResponse])
async def get_wallets(current_user=Depends(get_current_user)):
    return await list_wallets_by_user(current_user["id"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def add_wallet(payload: WalletCreate, current_user=Depends(get_current_user)):
    wallet = await create_wallet(current_user["id"], payload.model_dump())

    if payload.initial_balance > 0:
        await create_transaction(
            {
                "user_id": current_user["id"],
                "wallet_id": wallet["id"],
                "type": "income",
                "amount": payload.initial_balance,
                "category": "Số dư đầu kỳ",
                "note": f"Khởi tạo ví {payload.name}",
                "transaction_date": datetime.now(timezone.utc),
            }
        )

    return wallet


@router.put("/{wallet_id}", response_model=WalletResponse)
async def edit_wallet(wallet_id: str, payload: WalletUpdate, current_user=Depends(get_current_user)):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    wallet = await update_wallet(current_user["id"], wallet_id, data)
    if not wallet:
        raise HTTPException(status_code=404, detail="Không tìm thấy ví")
    return wallet


@router.delete("/{wallet_id}")
async def remove_wallet(wallet_id: str, current_user=Depends(get_current_user)):
    if mongo.using_memory():
        has_transactions = any(
            item.get("wallet_id") == wallet_id and item.get("user_id") == current_user["id"]
            for item in mongo.memory_store["transactions"]
        )
    else:
        has_transactions = (
            await mongo.database.transactions.count_documents(
                {"wallet_id": wallet_id, "user_id": current_user["id"]}, limit=1
            )
            > 0
        )

    if has_transactions:
        raise HTTPException(status_code=400, detail="Ví đang có giao dịch, không thể xóa")

    deleted = await delete_wallet(current_user["id"], wallet_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy ví")

    return {"message": "Deleted"}
