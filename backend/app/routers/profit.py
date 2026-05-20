from fastapi import APIRouter

from app.database import log_usage
from app.schemas import ProfitSettingsUpdate
from app.services.profit import get_profit_settings, save_profit_settings, weekly_profit_report

router = APIRouter(prefix="/api", tags=["profit"])


@router.get("/weekly-profit")
def get_weekly_profit():
    log_usage("weekly_profit_viewed", "Weekly profit opened")
    return weekly_profit_report()


@router.get("/profit-settings")
def get_settings():
    return get_profit_settings()


@router.post("/profit-settings")
def post_settings(payload: ProfitSettingsUpdate):
    log_usage("profit_settings_updated", "Profit settings updated")
    return save_profit_settings(payload.model_dump(exclude_none=True))
