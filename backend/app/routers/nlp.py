from fastapi import APIRouter, Depends

from app.db.mongo import create_transaction
from app.dependencies import get_current_user
from app.schemas.nlp import NlpInput, NlpParsedTransaction
from app.services.nlp_service import parse_natural_transaction

router = APIRouter()


@router.post("/parse", response_model=NlpParsedTransaction)
async def parse_text(payload: NlpInput, current_user=Depends(get_current_user)):
    _ = current_user
    return parse_natural_transaction(payload.text)


@router.post("/parse-and-save", response_model=dict)
async def parse_and_save(payload: NlpInput, current_user=Depends(get_current_user)):
    parsed = parse_natural_transaction(payload.text)

    if payload.auto_save:
        created = await create_transaction(
            {
                "user_id": current_user["id"],
                "type": parsed.type,
                "amount": parsed.amount,
                "category": parsed.category,
                "note": parsed.note,
                "transaction_date": parsed.transaction_date,
            }
        )
        return {"parsed": parsed.model_dump(), "saved": created}

    return {"parsed": parsed.model_dump(), "saved": None}
