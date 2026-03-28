from fastapi import APIRouter, Depends, HTTPException

from app.auth_accounts import ACCOUNTS, authenticate
from app.deps import CurrentUser, create_access_token
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    role: str
    hospital_id: str | None = None


class MeResponse(BaseModel):
    email: str
    role: str
    hospital_id: str | None = None


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    if not ACCOUNTS:
        raise HTTPException(
            status_code=503,
            detail="No accounts configured. Set AUTH_ADMIN_EMAIL and AUTH_ADMIN_PASSWORD in .env",
        )
    acc = authenticate(body.email, body.password)
    if not acc:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(acc)
    return LoginResponse(
        access_token=token,
        email=acc.email,
        role=acc.role,
        hospital_id=acc.hospital_id,
    )


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser):
    return MeResponse(email=user.email, role=user.role, hospital_id=user.hospital_id)
