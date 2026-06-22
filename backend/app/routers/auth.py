from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import authenticate_user, build_auth_response, create_user, get_current_user, revoke_session

router = APIRouter(prefix="/api", tags=["auth"])


class AuthPayload(BaseModel):
    email: str
    password: str
    full_name: str | None = ""


@router.post("/register")
@router.post("/auth/register")
def register(payload: AuthPayload):
    user = create_user(payload.email, payload.password, payload.full_name or "")
    return build_auth_response(user)


@router.post("/login")
@router.post("/auth/login")
def login(payload: AuthPayload):
    user = authenticate_user(payload.email, payload.password)
    return build_auth_response(user)


@router.get("/me")
@router.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/logout")
@router.post("/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    revoke_session(current_user["session_token"])
    return {"ok": True}
