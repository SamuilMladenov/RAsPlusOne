"""Demo accounts from environment variables (see auth.env.example)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.config import _get

Role = Literal["admin", "hospital", "triager"]


@dataclass(frozen=True)
class Account:
    email: str
    password: str
    role: Role
    hospital_id: str | None = None


def _load_accounts() -> dict[str, Account]:
    """email (lowercase) -> Account"""
    accounts: dict[str, Account] = {}

    admin_email = _get("AUTH_ADMIN_EMAIL")
    admin_password = _get("AUTH_ADMIN_PASSWORD")
    if admin_email and admin_password:
        e = admin_email.lower()
        accounts[e] = Account(email=admin_email, password=admin_password, role="admin")

    triager_email = _get("AUTH_TRIAGER_EMAIL")
    triager_password = _get("AUTH_TRIAGER_PASSWORD")
    if triager_email and triager_password:
        e = triager_email.lower()
        accounts[e] = Account(
            email=triager_email,
            password=triager_password,
            role="triager",
        )

    for i in range(1, 10):
        prefix = f"AUTH_HOSPITAL_{i}_"
        he = _get(f"{prefix}EMAIL")
        hp = _get(f"{prefix}PASSWORD")
        hid = _get(f"{prefix}HOSPITAL_ID")
        if he and hp and hid:
            e = he.lower()
            accounts[e] = Account(
                email=he,
                password=hp,
                role="hospital",
                hospital_id=hid,
            )

    return accounts


ACCOUNTS: dict[str, Account] = _load_accounts()


def authenticate(email: str, password: str) -> Account | None:
    key = email.strip().lower()
    acc = ACCOUNTS.get(key)
    if not acc:
        return None
    if not secrets_compare(acc.password, password):
        return None
    return acc


def secrets_compare(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
