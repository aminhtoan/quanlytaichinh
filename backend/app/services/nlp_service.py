import re
from datetime import datetime, timedelta, timezone

from app.schemas.nlp import NlpParsedTransaction

CATEGORY_MAP = {
    "an": "An uong",
    "sang": "An uong",
    "ca phe": "An uong",
    "xang": "Di chuyen",
    "grab": "Di chuyen",
    "taxi": "Di chuyen",
    "xem phim": "Giai tri",
    "netflix": "Giai tri",
    "luong": "Luong",
    "thuong": "Thuong",
    "tiet kiem": "Tiet kiem",
}


def normalize_amount(raw_text: str) -> float | None:
    text = raw_text.lower().strip().replace(" ", "")
    pattern = r"^(\d[\d\.,]*)(k|tr|m)?$"
    match = re.match(pattern, text)
    if not match:
        return None

    number_part = match.group(1)
    # 54,000 or 54.000 -> 54000
    if re.fullmatch(r"\d{1,3}(?:[\.,]\d{3})+", number_part):
        normalized_number = number_part.replace(".", "").replace(",", "")
    # 1,234.56 or 1.234,56
    elif "," in number_part and "." in number_part:
        decimal_sep = "," if number_part.rfind(",") > number_part.rfind(".") else "."
        thousand_sep = "." if decimal_sep == "," else ","
        normalized_number = number_part.replace(thousand_sep, "").replace(decimal_sep, ".")
    # 123,45 (decimal) or 12,345 (thousand)
    elif "," in number_part:
        normalized_number = (
            number_part.replace(",", "")
            if re.fullmatch(r"\d+(?:,\d{3})+", number_part)
            else number_part.replace(",", ".")
        )
    # 123.45 (decimal) or 12.345 (thousand)
    elif "." in number_part:
        normalized_number = (
            number_part.replace(".", "")
            if re.fullmatch(r"\d+(?:\.\d{3})+", number_part)
            else number_part
        )
    else:
        normalized_number = number_part

    try:
        value = float(normalized_number)
    except ValueError:
        return None
    unit = match.group(2)

    if unit == "k":
        return value * 1_000
    if unit == "tr":
        return value * 1_000_000
    if unit == "m":
        return value * 1_000_000
    return value


def detect_amount(text: str) -> float:
    lowered = text.lower()
    amount_tokens = re.findall(r"\d[\d\.,]*\s?(?:k|tr|m)?", lowered)
    if not amount_tokens:
        return 0

    def _filter_candidates(values: list[float]) -> list[float]:
        # Ignore tiny values from table indexes and huge values from phone numbers.
        return [value for value in values if 1_000 <= value <= 200_000_000]

    # Prefer values on lines that contain "tong/total/thanh tien".
    total_keywords = ["tong", "total", "thanh tien", "cong", "phai tra"]
    for line in lowered.splitlines():
        line = line.strip()
        if not line or not any(keyword in line for keyword in total_keywords):
            continue
        line_values = [normalize_amount(token) for token in re.findall(r"\d[\d\.,]*\s?(?:k|tr|m)?", line)]
        numeric_values = [value for value in line_values if value is not None]
        filtered_line_values = _filter_candidates(numeric_values)
        if filtered_line_values:
            return max(filtered_line_values)

    normalized_values = [normalize_amount(token) for token in amount_tokens]
    numeric_values = [value for value in normalized_values if value is not None]
    filtered_values = _filter_candidates(numeric_values)
    if filtered_values:
        return max(filtered_values)

    return max(numeric_values) if numeric_values else 0


def detect_type(text: str) -> str:
    lowered = text.lower()
    income_keywords = ["thu", "nhan", "duoc", "luong", "thuong"]
    if any(keyword in lowered for keyword in income_keywords):
        return "income"
    return "expense"


def detect_category(text: str) -> str:
    lowered = text.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in lowered:
            return category
    return "Khac"


def detect_date(text: str) -> datetime:
    lowered = text.lower()
    now = datetime.now(timezone.utc)
    if "hom qua" in lowered:
        return now - timedelta(days=1)
    if "hom nay" in lowered:
        return now
    return now


def parse_natural_transaction(text: str) -> NlpParsedTransaction:
    amount = detect_amount(text)
    if amount <= 0:
        amount = 10_000
        confidence = 0.45
    else:
        confidence = 0.88

    transaction_type = detect_type(text)
    category = detect_category(text)
    date_value = detect_date(text)

    return NlpParsedTransaction(
        type=transaction_type,
        amount=amount,
        category=category,
        note=text.strip(),
        transaction_date=date_value,
        confidence=confidence,
    )
