from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.db.mongo import (
    create_user,
    find_refresh_token,
    find_user_by_email,
    find_user_by_username,
    revoke_refresh_token,
    save_refresh_token,
)
from app.dependencies import get_current_user
from app.schemas.auth import RefreshTokenRequest, TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter()


def to_public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    existing_user = await find_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email da duoc su dung")

    user = await create_user(
        {
            "full_name": payload.full_name,
            "email": payload.email,
            "username": payload.username or payload.email.split("@")[0],
            "hashed_password": hash_password(payload.password),
        }
    )
    return to_public_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user = None
    if payload.email:
        user = await find_user_by_email(payload.email)
    elif payload.username:
        user = await find_user_by_username(payload.username)

    hashed_password = user.get("hashed_password") if user else None
    if not user or not hashed_password or not verify_password(payload.password, hashed_password):
        raise HTTPException(status_code=401, detail="Thong tin dang nhap khong dung")

    access_token = create_access_token(user["id"])
    refresh_token, refresh_expire = create_refresh_token(user["id"])
    await save_refresh_token(refresh_token, user["id"], refresh_expire)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest):
    token_payload = decode_token(payload.refresh_token)
    if not token_payload or token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token khong hop le")

    stored_token = await find_refresh_token(payload.refresh_token)
    if not stored_token or stored_token.get("revoked"):
        raise HTTPException(status_code=401, detail="Refresh token da bi thu hoi")

    expires_at = stored_token.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token da het han")

    await revoke_refresh_token(payload.refresh_token)
    new_access_token = create_access_token(token_payload["sub"])
    new_refresh_token, refresh_expire = create_refresh_token(token_payload["sub"])
    await save_refresh_token(new_refresh_token, token_payload["sub"], refresh_expire)

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.post("/logout")
async def logout(payload: RefreshTokenRequest, current_user=Depends(get_current_user)):
    _ = current_user
    await revoke_refresh_token(payload.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return to_public_user(current_user)
