
from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import log_usage
from app.services.ml_models import ml_business_insights

router = APIRouter(prefix="/api", tags=["ml"])


@router.get("/ml-insights")
def get_ml_insights(current_user: dict = Depends(get_current_user)):
    log_usage("growth_planner_viewed", "Growth planner opened", current_user["email"])
    return ml_business_insights()
