from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.mongo import close_db, connect_db, get_db_connection_error, get_storage_mode
from app.routers import (
    ai,
    auth,
    budgets,
    categories,
    chat,
    debts,
    investments,
    nlp,
    ocr,
    subscriptions,
    transactions,
    wallets,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="Quan Ly Tai Chinh API",
    description="API cho he thong quan ly tai chinh ca nhan thong minh",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(nlp.router, prefix="/api/nlp", tags=["nlp"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(wallets.router, prefix="/api/wallets", tags=["wallets"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(investments.router, prefix="/api/investments", tags=["investments"])
app.include_router(debts.router, prefix="/api/debts", tags=["debts"])


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "storage_mode": get_storage_mode(),
        "db_error": get_db_connection_error(),
    }
