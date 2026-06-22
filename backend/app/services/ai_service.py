from __future__ import annotations

from app.services.analytics import calculate_sku_scores, rto_risk_analysis
from app.services.recommender import generate_recommendations, today_actions


def generate_ai_summary(question: str, seller_email: str | None = None) -> dict:
    q = (question or "").lower()
    recs = generate_recommendations(seller_email)
    sku_scores = calculate_sku_scores(seller_email)
    rto = rto_risk_analysis(seller_email)

    if "pause" in q or "stop" in q:
        answer = today_actions(seller_email)[1] if len(today_actions(seller_email)) > 1 else "Pause weak SKUs and review returns first."
    elif "promote" in q or "scale" in q:
        answer = today_actions(seller_email)[0] if today_actions(seller_email) else "Promote the highest scoring SKU."
    elif "rto" in q or "return" in q:
        top = rto["items"][0] if rto["items"] else None
        answer = f"Highest return risk is {top['sku']} in {top['customer_state']} at {top['rto_rate']}%." if top else "No return-risk data yet."
    elif "top 3" in q or "action" in q:
        answer = "\n".join(today_actions(seller_email))
    elif "sku" in q or "score" in q:
        top = sku_scores[0] if sku_scores else None
        answer = f"Top SKU is {top['product_name']} with score {top['score']}." if top else "No SKU scores yet."
    else:
        answer = "Upload orders first, then I can summarize promotions, risk, and next actions."

    return {
        "answer": answer,
        "mode": "rules",
        "context": {
            "recommendations": recs,
            "sku_count": len(sku_scores),
            "risk_count": len(rto["items"]),
        },
    }
