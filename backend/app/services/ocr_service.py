from io import BytesIO

import pytesseract
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


class OcrServiceError(Exception):
    pass


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    try:
        image = Image.open(BytesIO(image_bytes))
    except UnidentifiedImageError as exc:
        raise OcrServiceError("Khong doc duoc file anh hop le") from exc

    try:
        text = pytesseract.image_to_string(image, lang="vie+eng")
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrServiceError(
            "Chua cai dat Tesseract OCR tren server. Vui long cai Tesseract hoac cau hinh TESSERACT_CMD"
        ) from exc
    except pytesseract.TesseractError as exc:
        # Fallback to English when Vietnamese language data is missing.
        message = str(exc).lower()
        if "failed loading language" in message or "vie.traineddata" in message:
            try:
                text = pytesseract.image_to_string(image, lang="eng")
            except Exception as inner_exc:  # pragma: no cover - defensive branch
                raise OcrServiceError(f"Khong the OCR anh: {inner_exc}") from inner_exc
        else:
            raise OcrServiceError(f"Khong the OCR anh: {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive branch
        raise OcrServiceError(f"Khong the OCR anh: {exc}") from exc

    return text.strip()
