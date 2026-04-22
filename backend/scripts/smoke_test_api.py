import json
import os
import random
import string
from datetime import datetime, timedelta, timezone

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")
TIMEOUT = 20


def random_suffix(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def call(method: str, path: str, expected_status: set[int] | None = None, **kwargs):
    url = f"{BASE_URL}{path}"
    response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = response.text

    print(f"[{method} {path}] -> {status}")

    if expected_status and status not in expected_status:
        raise AssertionError(
            f"Unexpected status for {method} {path}: {status}\n"
            f"Response: {json.dumps(body, ensure_ascii=False, indent=2) if isinstance(body, dict) else body}"
        )

    return status, body


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    suffix = random_suffix()
    username = f"user_{suffix}"
    email = f"{username}@example.com"
    password = "123456"

    # Auth register/login
    _, register_body = call(
        "POST",
        "/auth/register",
        expected_status={201},
        json={
            "username": username,
            "full_name": "Test User",
            "email": email,
            "password": password,
        },
    )
    assert register_body["email"] == email

    _, login_body = call(
        "POST",
        "/auth/login",
        expected_status={200},
        json={"username": username, "password": password},
    )
    access_token = login_body["access_token"]
    refresh_token = login_body["refresh_token"]

    # Auth me
    _, me_body = call("GET", "/auth/me", expected_status={200}, headers=bearer(access_token))
    assert me_body["email"] == email

    # Categories
    _, categories_body = call("GET", "/categories", expected_status={200}, headers=bearer(access_token))
    assert isinstance(categories_body, list)

    _, category_body = call(
        "POST",
        "/categories",
        expected_status={201},
        headers=bearer(access_token),
        json={"name": "Cafe test", "type": "expense", "icon": "coffee"},
    )
    category_id = category_body["id"]

    # Wallets
    _, wallet_1 = call(
        "POST",
        "/wallets",
        expected_status={201},
        headers=bearer(access_token),
        json={"name": "Vi Chinh", "type": "cash", "currency": "VND", "initial_balance": 1_000_000},
    )
    wallet_1_id = wallet_1["id"]

    _, wallet_2 = call(
        "POST",
        "/wallets",
        expected_status={201},
        headers=bearer(access_token),
        json={"name": "Vi Phu", "type": "ewallet", "currency": "VND", "initial_balance": 0},
    )
    wallet_2_id = wallet_2["id"]

    call("GET", "/wallets", expected_status={200}, headers=bearer(access_token))

    # Transactions + query + transfer + summary
    transaction_date = datetime.now(timezone.utc).isoformat()
    _, tx_body = call(
        "POST",
        "/transactions",
        expected_status={201},
        headers=bearer(access_token),
        json={
            "wallet_id": wallet_1_id,
            "category_id": category_id,
            "type": "expense",
            "amount": 100_000,
            "category": "Cafe test",
            "note": "Ca phe buoi sang",
            "transaction_date": transaction_date,
        },
    )
    tx_id = tx_body["id"]

    call(
        "GET",
        "/transactions/query?page=1&size=20&type=expense",
        expected_status={200},
        headers=bearer(access_token),
    )

    call(
        "POST",
        "/transactions/transfer",
        expected_status={200},
        headers=bearer(access_token),
        json={
            "source_wallet_id": wallet_1_id,
            "dest_wallet_id": wallet_2_id,
            "amount": 50_000,
            "note": "Chuyen test",
            "date": datetime.now().isoformat(),
        },
    )

    call("GET", "/transactions/summary/overview", expected_status={200}, headers=bearer(access_token))

    call(
        "PUT",
        f"/transactions/{tx_id}",
        expected_status={200},
        headers=bearer(access_token),
        json={"amount": 90_000, "note": "Cap nhat"},
    )

    # Debts
    _, debt_body = call(
        "POST",
        "/debts",
        expected_status={201},
        headers=bearer(access_token),
        json={
            "creditor_name": "Nguoi cho vay",
            "total_amount": 200_000,
            "type": "payable",
            "wallet_id": wallet_1_id,
        },
    )
    debt_id = debt_body["id"]

    call("GET", "/debts", expected_status={200}, headers=bearer(access_token))

    call(
        "POST",
        f"/debts/{debt_id}/repay",
        expected_status={200},
        headers=bearer(access_token),
        json={"amount": 50_000, "wallet_id": wallet_1_id},
    )

    # Subscriptions
    _, subscription_body = call(
        "POST",
        "/subscriptions",
        expected_status={201},
        headers=bearer(access_token),
        json={
            "name": "Netflix",
            "amount": 260_000,
            "frequency": "monthly",
            "default_wallet_id": wallet_1_id,
            "next_due_date": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
    )
    subscription_id = subscription_body["id"]

    call("GET", "/subscriptions", expected_status={200}, headers=bearer(access_token))
    call("GET", "/subscriptions/detect", expected_status={200}, headers=bearer(access_token))

    call(
        "PUT",
        f"/subscriptions/{subscription_id}",
        expected_status={200},
        headers=bearer(access_token),
        json={"amount": 300_000, "is_active": False},
    )

    # Investments
    _, investment_body = call(
        "POST",
        "/investments",
        expected_status={201},
        headers=bearer(access_token),
        json={
            "wallet_id": wallet_1_id,
            "name": "Vang test",
            "type": "gold",
            "principal_amount": 100_000,
        },
    )
    investment_id = investment_body["id"]

    call(
        "PUT",
        f"/investments/{investment_id}/update",
        expected_status={200},
        headers=bearer(access_token),
        json={"current_value": 120_000},
    )

    call(
        "POST",
        f"/investments/{investment_id}/transactions",
        expected_status={200},
        headers=bearer(access_token),
        json={"selling_price": 120_000, "wallet_id": wallet_1_id},
    )

    # Budgets + progress
    now = datetime.now(timezone.utc)
    call(
        "POST",
        "/budgets",
        expected_status={201},
        headers=bearer(access_token),
        json={
            "category_id": category_id,
            "amount_limit": 500_000,
            "period": "monthly",
            "start_date": now.replace(day=1).isoformat(),
            "end_date": (now.replace(day=1) + timedelta(days=30)).isoformat(),
        },
    )

    call("GET", "/budgets/progress?period=monthly", expected_status={200}, headers=bearer(access_token))

    # AI parse/chat/history + chat alias
    call(
        "POST",
        "/ai/parse",
        expected_status={200},
        headers=bearer(access_token),
        json={"text": "an pho 50k"},
    )

    _, chat_body = call(
        "POST",
        "/ai/chat",
        expected_status={200},
        headers=bearer(access_token),
        json={"message": "Thang nay toi da chi bao nhieu?"},
    )
    session_id = chat_body["session_id"]

    call("GET", f"/ai/chat/{session_id}", expected_status={200}, headers=bearer(access_token))

    call(
        "POST",
        "/chat/ask",
        expected_status={200},
        headers=bearer(access_token),
        json={"message": "Tu van tiet kiem", "session_id": session_id},
    )

    # OCR endpoints availability (use invalid content type -> expect 400)
    call(
        "POST",
        "/ai/ocr",
        expected_status={400},
        headers=bearer(access_token),
        files={"file": ("note.txt", b"not image", "text/plain")},
    )
    call(
        "POST",
        "/ocr/scan",
        expected_status={400},
        headers=bearer(access_token),
        files={"file": ("note.txt", b"not image", "text/plain")},
    )

    # Refresh token + logout
    _, refreshed = call(
        "POST",
        "/auth/refresh-token",
        expected_status={200},
        json={"refresh_token": refresh_token},
    )

    call(
        "POST",
        "/auth/logout",
        expected_status={200},
        headers=bearer(refreshed["access_token"]),
        json={"refresh_token": refreshed["refresh_token"]},
    )

    print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()
