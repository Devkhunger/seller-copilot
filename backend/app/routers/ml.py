from fastapi import APIRouter

from app.database import log_usage
from app.services.ml_models import ml_business_insights

router = APIRouter(prefix="/api", tags=["ml"])


@router.get("/ml-insights")
def get_ml_insights():
    log_usage("growth_planner_viewed", "Growth planner opened")
    return ml_business_insights()
