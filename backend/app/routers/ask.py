from fastapi import APIRouter

from app.database import log_usage
from app.schemas import AskRequest
from app.services.ai_service import answer_seller_question

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask")
def ask_seller_copilot(payload: AskRequest):
    result = answer_seller_question(payload.question)
    log_usage("seller_question", payload.question[:200])
    return result

