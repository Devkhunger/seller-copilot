from __future__ import annotations

from app.services.analytics import calculate_sku_scores, rto_risk_analysis
from app.services.profit import weekly_profit


def ml_business_insights(seller_email: str | None = None) -> dict:
    sku_scores = calculate_sku_scores(seller_email)
    rto = rto_risk_analysis(seller_email)
    profit = weekly_profit(seller_email)
    top_sku = sku_scores[0] if sku_scores else None
    top_risk = rto["items"][0] if rto["items"] else None
    top_profit = profit["sku_profit"][0] if profit["sku_profit"] else None

    return {
        "engine": {
            "sklearn_available": False,
            "mode": "rules",
        },
        "demand_forecast": [
            {
                "sku": item["sku"],
                "forecast_units": item["orders"] + 2,
                "avg_daily_forecast": round(item["orders"] / 14.0, 1) if item["orders"] else 0,
                "trend": "Up" if item["momentum_score"] >= 55 else "Flat" if item["momentum_score"] >= 45 else "Down",
                "confidence": "High" if item["orders"] >= 10 else "Medium" if item["orders"] >= 4 else "Low",
            }
            for item in sku_scores[:5]
        ],
        "rto_predictions": [
            {
                "sku": item["sku"],
                "customer_state": item["customer_state"],
                "rto_probability": item["rto_rate"],
                "risk_label": item["risk_label"],
                "confidence": item["confidence"],
            }
            for item in rto["items"][:8]
        ],
        "profit_opportunities": [
            {
                "sku": item["sku"],
                "forecast_units": max(1, int(item["orders"])),
                "revenue": item["orders"] * 1000.0,
                "rto_probability": item["rto_rate"] if "rto_rate" in item else 0.0,
                "opportunity_score": item["score"] if "score" in item else 50.0,
                "decision": "Scale Ads and Stock" if item.get("score", 0) >= 75 else "Test Carefully" if item.get("score", 0) >= 45 else "Fix RTO Before Scaling",
            }
            for item in sku_scores[:5]
        ],
        "model_notes": [
            "This local build uses transparent rule-based signals when ML services are unavailable.",
            "Trend, return risk, and profit recommendations are derived from uploaded order rows.",
        ],
    }
