from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import log_usage
from app.services.ai_service import generate_ai_summary

router = APIRouter(prefix="/api", tags=["ask"])


class AskPayload(BaseModel):
    question: str


@router.post("/ask")
def ask_copilot(payload: AskPayload, current_user: dict = Depends(get_current_user)):
    log_usage("copilot_asked", payload.question, current_user["email"])
    return generate_ai_summary(payload.question, current_user["email"])
