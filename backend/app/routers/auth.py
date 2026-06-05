from fastapi import APIRouter, Depends

from app.auth import authenticate_user, build_auth_response, create_user, get_current_user, revoke_session
from app.schemas import AuthRequest


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(payload: AuthRequest):
    user = create_user(payload.email, payload.password, payload.full_name)
    return build_auth_response(user)


@router.post("/login")
def login(payload: AuthRequest):
    user = authenticate_user(payload.email, payload.password)
    return build_auth_response(user)


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "session_token"}


@router.post("/logout")
def logout(current_user=Depends(get_current_user)):
    revoke_session(current_user["session_token"])
    return {"ok": True}
