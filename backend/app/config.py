"""Load settings from environment (see auth.env.example / .env)."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str | None = None) -> str | None:
    v = os.getenv(key)
    if v is None or v.strip() == "":
        return default
    return v.strip()


JWT_SECRET_KEY: str = _get("JWT_SECRET_KEY") or "dev-only-change-me-use-long-random-string-in-production"
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(_get("JWT_EXPIRE_MINUTES") or "1440")
