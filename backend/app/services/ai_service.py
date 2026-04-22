from collections import defaultdict
from statistics import mean, pstdev
import unicodedata

import google.generativeai as genai

from app.core.config import settings


DISPLAY_CATEGORY_MAP = {
    "An uong": "Ăn uống",
    "Di chuyen": "Di chuyển",
    "Giai tri": "Giải trí",
    "Khac": "Khác",
    "Luong": "Lương",
    "Thuong": "Thưởng",
    "Tiet kiem": "Tiết kiệm",
}


def pretty_category(category: str) -> str:
    return DISPLAY_CATEGORY_MAP.get(category, category)


def normalize_question(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    without_accents = without_accents.replace("đ", "d").replace("Đ", "D")
    return without_accents.lower().strip()


def build_totals(transactions: list[dict]) -> tuple[float, float, float]:
    total_income = sum(float(item["amount"]) for item in transactions if item["type"] == "income")
    total_expense = sum(float(item["amount"]) for item in transactions if item["type"] == "expense")
    balance = total_income - total_expense
    return total_income, total_expense, balance


def format_money(amount: float) -> str:
    return f"{amount:,.0f}".replace(",", ".") + "₫"


def build_spending_ratio(transactions: list[dict]) -> dict[str, float]:
    expense_by_category: dict[str, float] = defaultdict(float)
    total_expense = 0.0

    for item in transactions:
        if item["type"] != "expense":
            continue
        amount = float(item["amount"])
        total_expense += amount
        expense_by_category[item["category"]] += amount

    if total_expense == 0:
        return {}

    return {
        key: round((value / total_expense) * 100, 2)
        for key, value in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
    }


def detect_anomalies(transactions: list[dict]) -> list[dict]:
    expenses = [float(item["amount"]) for item in transactions if item["type"] == "expense"]
    if len(expenses) < 5:
        return []

    avg = mean(expenses)
    deviation = pstdev(expenses)
    if deviation == 0:
        return []

    threshold = avg + 2 * deviation
    anomalies = [
        item
        for item in transactions
        if item["type"] == "expense" and float(item["amount"]) > threshold
    ]
    return anomalies[:10]


def build_recommendations(spending_ratio: dict[str, float]) -> list[str]:
    recommendations: list[str] = []

    food_ratio = spending_ratio.get("An uong", 0)
    transport_ratio = spending_ratio.get("Di chuyen", 0)
    entertainment_ratio = spending_ratio.get("Giai tri", 0)

    if food_ratio > 35:
        recommendations.append("Chi tiêu ăn uống đang cao, bạn nên đặt ngân sách theo tuần.")
    if transport_ratio > 20:
        recommendations.append("Thử nghiệm gom chuyến đi để giảm chi phí di chuyển.")
    if entertainment_ratio > 15:
        recommendations.append("Cân nhắc giới hạn mức giải trí theo tháng để đạt mức tích lũy.")

    if not recommendations:
        recommendations.append("Chi tiêu đang cân bằng, tiếp tục duy trì kế hoạch ngân sách hiện tại.")

    return recommendations


def generate_local_finance_answer(
    question: str,
    spending_ratio: dict[str, float],
    transactions: list[dict],
) -> str:
    if not transactions:
        return "Bạn chưa có dữ liệu giao dịch. Hãy thêm vài giao dịch để mình phân tích chính xác hơn nhé."

    normalized_question = normalize_question(question)
    total_income, total_expense, balance = build_totals(transactions)

    if any(keyword in normalized_question for keyword in ["tổng chi", "chi bao nhieu", "chi bao nhiêu", "đã chi"]):
        return f"Tổng chi hiện tại của bạn là {format_money(total_expense)}."

    if any(keyword in normalized_question for keyword in ["tổng thu", "thu bao nhieu", "thu bao nhiêu", "đã thu"]):
        return f"Tổng thu hiện tại của bạn là {format_money(total_income)}."

    if any(keyword in normalized_question for keyword in ["số dư", "so du", "còn bao nhiêu", "con bao nhieu"]):
        return (
            f"Số dư hiện tại là {format_money(balance)} "
            f"(Thu: {format_money(total_income)} | Chi: {format_money(total_expense)})."
        )

    if any(keyword in normalized_question for keyword in ["gần đây", "gan day", "mới đây", "moi day"]):
        latest_transactions = sorted(
            transactions,
            key=lambda item: item.get("transaction_date") or item.get("created_at"),
            reverse=True,
        )[:5]
        transaction_lines = [
            f"- {pretty_category(item['category'])}: {format_money(float(item['amount']))} ({'thu' if item['type'] == 'income' else 'chi'})"
            for item in latest_transactions
        ]
        return "5 giao dịch gần nhất của bạn:\n" + "\n".join(transaction_lines)

    if any(keyword in normalized_question for keyword in ["tiết kiệm", "tiet kiem", "gợi ý", "goi y"]):
        recommendations = build_recommendations(spending_ratio)
        return "Gợi ý tiết kiệm dành cho bạn:\n" + "\n".join(f"- {item}" for item in recommendations)

    for category, ratio in spending_ratio.items():
        category_normalized = category.lower().replace(" ", "")
        if category_normalized in normalized_question.replace(" ", ""):
            category_expense = sum(
                float(item["amount"])
                for item in transactions
                if item["type"] == "expense" and item["category"] == category
            )
            return (
                f"Bạn đã chi cho {pretty_category(category)} khoảng {format_money(category_expense)} "
                f"(~{ratio}% tổng chi)."
            )

    if not spending_ratio:
        return (
            f"Hiện tại bạn có thu {format_money(total_income)} và chi {format_money(total_expense)}. "
            "Bạn có thể hỏi mình về tổng chi, số dư, giao dịch gần đây hoặc gợi ý tiết kiệm."
        )

    top_categories = sorted(spending_ratio.items(), key=lambda item: item[1], reverse=True)[:3]
    category_text = ", ".join(
        f"{pretty_category(category)} ({ratio}%)" for category, ratio in top_categories
    )
    return (
        f"Tổng quan nhanh: Thu {format_money(total_income)}, Chi {format_money(total_expense)}, "
        f"Số dư {format_money(balance)}. Nhóm chi chính: {category_text}."
    )


def ask_gemini(question: str, context: str) -> str | None:
    if not settings.gemini_api_key:
        return None

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            "Bạn là trợ lý tài chính cá nhân. Trả lời ngắn gọn, dễ hiểu và an toàn.\n"
            f"Ngữ cảnh dữ liệu: {context}\n"
            f"Câu hỏi: {question}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None
