from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.services.ai_service import generate_ai_summary
from app.services.analytics import calculate_sku_scores, dashboard_metrics, rto_risk_analysis
from app.services.recommender import generate_recommendations

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    metrics = dashboard_metrics(seller_email)
    sku_scores = calculate_sku_scores(seller_email=seller_email)
    risk = rto_risk_analysis(seller_email)
    with get_db() as conn:
        actions = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM actions WHERE seller_email = ? ORDER BY id DESC LIMIT 3",
                (seller_email,),
            ).fetchall()
        ]
    log_usage("dashboard_viewed", "Dashboard opened", seller_email)
    return {
        "metrics": metrics,
        "summary": generate_ai_summary(metrics, sku_scores, risk),
        "actions": actions,
    }


@router.get("/sku-scores")
def get_sku_scores(current_user: dict = Depends(get_current_user)):
    return {"items": calculate_sku_scores(seller_email=current_user["email"])}


@router.get("/rto-risk")
def get_rto_risk(current_user: dict = Depends(get_current_user)):
    return rto_risk_analysis(current_user["email"])


@router.get("/recommendations")
def get_recommendations(current_user: dict = Depends(get_current_user)):
    return generate_recommendations(current_user["email"])


@router.post("/actions/{action_id}/done")
def mark_action_done(action_id: int, current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE actions SET done = 1, done_at = CURRENT_TIMESTAMP WHERE id = ? AND seller_email = ?",
            (action_id, seller_email),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Action not found.")
    log_usage("action_done", f"Action {action_id} marked done", seller_email)
    return {"ok": True}
