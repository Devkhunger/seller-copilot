from fastapi import APIRouter, HTTPException

from app.database import get_db, log_usage
from app.services.ai_service import generate_ai_summary
from app.services.analytics import calculate_sku_scores, dashboard_metrics, rto_risk_analysis
from app.services.recommender import generate_recommendations

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard():
    metrics = dashboard_metrics()
    sku_scores = calculate_sku_scores()
    risk = rto_risk_analysis()
    with get_db() as conn:
        actions = [dict(row) for row in conn.execute("SELECT * FROM actions ORDER BY id DESC LIMIT 3").fetchall()]
    log_usage("dashboard_viewed", "Dashboard opened")
    return {
        "metrics": metrics,
        "summary": generate_ai_summary(metrics, sku_scores, risk),
        "actions": actions,
    }


@router.get("/sku-scores")
def get_sku_scores():
    return {"items": calculate_sku_scores()}


@router.get("/rto-risk")
def get_rto_risk():
    return rto_risk_analysis()


@router.get("/recommendations")
def get_recommendations():
    return generate_recommendations()


@router.post("/actions/{action_id}/done")
def mark_action_done(action_id: int):
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE actions SET done = 1, done_at = CURRENT_TIMESTAMP WHERE id = ?",
            (action_id,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Action not found.")
    log_usage("action_done", f"Action {action_id} marked done")
    return {"ok": True}

