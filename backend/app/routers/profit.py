from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import log_usage
from app.services.profit import save_settings, weekly_profit

router = APIRouter(prefix="/api", tags=["profit"])


class ProfitSettingsPayload(BaseModel):
    product_cost_percent: float | None = None
    marketplace_fee_percent: float | None = None
    forward_shipping_per_order: float | None = None
    return_shipping_per_order: float | None = None
    ad_cost_percent: float | None = None


@router.get("/weekly-profit")
def get_weekly_profit(current_user: dict = Depends(get_current_user)):
    log_usage("weekly_profit_viewed", "Weekly profit opened", current_user["email"])
    return weekly_profit(current_user["email"])


@router.post("/weekly-profit/settings")
@router.post("/profit-settings")
def update_weekly_profit_settings(payload: ProfitSettingsPayload, current_user: dict = Depends(get_current_user)):
    settings = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = save_settings(current_user["email"], settings)
    log_usage("profit_settings_saved", "Weekly profit settings updated", current_user["email"])
    return {"settings": updated}
