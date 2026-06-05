from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import log_usage
from app.schemas import AskRequest
from app.services.ai_service import answer_seller_question

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask")
def ask_seller_copilot(payload: AskRequest, current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    result = answer_seller_question(payload.question)
    log_usage("seller_question", payload.question[:200], seller_email)
    return result
