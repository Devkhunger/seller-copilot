from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import log_usage
from app.schemas import ProfitSettingsUpdate
from app.services.profit import get_profit_settings, save_profit_settings, weekly_profit_report

router = APIRouter(prefix="/api", tags=["profit"])


@router.get("/weekly-profit")
def get_weekly_profit(current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    log_usage("weekly_profit_viewed", "Weekly profit opened", seller_email)
    return weekly_profit_report(seller_email)


@router.get("/profit-settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    return get_profit_settings(current_user["email"])


@router.post("/profit-settings")
def post_settings(payload: ProfitSettingsUpdate, current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    log_usage("profit_settings_updated", "Profit settings updated", seller_email)
    return save_profit_settings(payload.model_dump(exclude_none=True), seller_email)
