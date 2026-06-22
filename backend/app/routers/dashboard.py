from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.services.analytics import calculate_sku_scores, dashboard_metrics, rto_risk_analysis
from app.services.recommender import generate_recommendations, today_actions

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    log_usage("dashboard_viewed", "Dashboard opened", current_user["email"])
    metrics = dashboard_metrics(current_user["email"])
    summary = metrics["summary"]
    top_sku = metrics["top_sku"]
    sku_scores = calculate_sku_scores(current_user["email"])
    worst_sku = sku_scores[-1] if sku_scores else None
    total_orders = summary["orders"]
    delivered_orders = round(total_orders * (summary["delivered_rate"] / 100)) if total_orders else 0
    cancelled_orders = round(total_orders * (summary["cancelled_rate"] / 100)) if total_orders else 0
    rto_orders = round(total_orders * (summary["rto_rate"] / 100)) if total_orders else 0
    unknown_orders = max(0, total_orders - delivered_orders - cancelled_orders - rto_orders)

    return {
        "summary": summary,
        "metrics": {
            "total_orders": total_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "rto_orders": rto_orders,
            "unknown_orders": unknown_orders,
            "revenue_estimate": summary["revenue"],
            "top_selling_sku": top_sku["product_name"] if top_sku else "No data",
            "worst_performing_sku": worst_sku["product_name"] if worst_sku else "No data",
            "ad_orders": top_sku.get("ad_orders", 0) if top_sku else 0,
            "natural_orders": top_sku.get("natural_orders", 0) if top_sku else 0,
        },
        "top_sku": top_sku,
        "worst_sku": worst_sku,
        "recent_orders": metrics["recent_orders"],
        "recommendations": generate_recommendations(current_user["email"]),
        "actions": today_actions(current_user["email"]),
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
