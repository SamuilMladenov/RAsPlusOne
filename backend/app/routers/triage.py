"""Triage card photo uploads from field devices."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import _get
from app.deps import TriagerUser

router = APIRouter(prefix="/triage", tags=["Triage"])

MAX_BYTES = 15 * 1024 * 1024
ALLOWED_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }
)
EXT_FOR_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def _upload_root() -> Path:
    raw = _get("TRIAGE_UPLOAD_DIR")
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "data" / "triage_photos"


@router.post("/photos")
async def upload_triage_photo(
    _user: TriagerUser,
    file: UploadFile = File(...),
) -> dict[str, str]:
    ct = (file.content_type or "").split(";")[0].strip().lower()
    if ct not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use a JPEG, PNG, WebP, or HEIC image.",
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 15 MB).")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    root = _upload_root()
    root.mkdir(parents=True, exist_ok=True)
    ext = EXT_FOR_TYPE.get(ct, ".jpg")
    name = f"{uuid.uuid4().hex}{ext}"
    path = root / name
    path.write_bytes(data)

    return {"status": "ok", "id": name}
