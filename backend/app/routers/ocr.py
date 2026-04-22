from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_current_user
from app.services.nlp_service import parse_natural_transaction
from app.services.ocr_service import OcrServiceError, extract_text_from_image_bytes

router = APIRouter()


@router.post("/receipt", response_model=dict)
async def extract_receipt(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    _ = current_user
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Chi chap nhan file anh")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="File rong")

    try:
        text = extract_text_from_image_bytes(image_bytes)
    except OcrServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    parsed = parse_natural_transaction(text if text else "chi 0")

    return {
        "ocr_text": text,
        "suggested_transaction": parsed.model_dump(),
    }


@router.post("/scan", response_model=dict)
async def scan_receipt(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    return await extract_receipt(file=file, current_user=current_user)
