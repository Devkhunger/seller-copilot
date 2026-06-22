from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.services.ai_service import generate_ai_summary
from app.services.analytics import calculate_sku_scores, dashboard_metrics, rto_risk_analysis
from app.services.recommender import generate_recommendations

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    log_usage("dashboard_viewed", "Dashboard opened", current_user["email"])
    metrics = dashboard_metrics(current_user["email"])
    return {
        "summary": metrics["summary"],
        "top_sku": metrics["top_sku"],
        "recent_orders": metrics["recent_orders"],
        "recommendations": generate_recommendations(current_user["email"]),
    }


@router.get("/sku-scores")
def get_sku_scores(current_user: dict = Depends(get_current_user)):
    log_usage("sku_scores_viewed", "SKU score table opened", current_user["email"])
    return {"items": calculate_sku_scores(current_user["email"])}


@router.get("/rto-risk")
def get_rto_risk(current_user: dict = Depends(get_current_user)):
    log_usage("rto_risk_viewed", "RTO risk screen opened", current_user["email"])
    return rto_risk_analysis(current_user["email"])


@router.get("/recommendations")
def get_recommendations(current_user: dict = Depends(get_current_user)):
    log_usage("recommendations_viewed", "Recommendations opened", current_user["email"])
    return generate_recommendations(current_user["email"])


@router.post("/actions/{action_id}/done")
def mark_action_done(action_id: int, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM actions WHERE id = ? AND seller_email = ?",
            (action_id, current_user["email"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Action not found.")
        conn.execute("UPDATE actions SET done = 1, done_at = CURRENT_TIMESTAMP WHERE id = ?", (action_id,))
    return {"ok": True}
