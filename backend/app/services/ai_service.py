from __future__ import annotations

import re

from app.services.analytics import calculate_sku_scores, rto_risk_analysis
from app.services.profit import _load_settings, _orders, _row_financials
from app.services.recommender import generate_recommendations, today_actions


def generate_ai_summary(question: str, seller_email: str | None = None) -> dict:
    q = (question or "").lower()
    recs = generate_recommendations(seller_email)
    sku_scores = calculate_sku_scores(seller_email)
    rto = rto_risk_analysis(seller_email)

    sku_answer = _answer_sku_question(question, seller_email, sku_scores)
    if sku_answer:
        return {
            "answer": sku_answer,
            "mode": "rules",
            "context": {
                "recommendations": recs,
                "sku_count": len(sku_scores),
                "risk_count": len(rto["items"]),
            },
        }

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


def _answer_sku_question(question: str, seller_email: str | None, sku_scores: list[dict]) -> str | None:
    """Answer questions about a named SKU using stored order and profit data."""
    sku = _find_sku(question, sku_scores, seller_email)
    if not sku:
        return None

    orders = [row for row in _orders(seller_email) if str(row.get("sku") or "").strip().lower() == sku.lower()]
    if not orders:
        return f"I could not find order data for {sku}. Check the SKU spelling or upload the relevant orders."

    settings = _load_settings(seller_email)
    financials = [_row_financials(row, settings) for row in orders]
    quantities = sum(item["qty"] for item in financials)
    delivered = sum(item["qty"] for item in financials if item["status"] == "delivered")
    rto = sum(item["qty"] for item in financials if item["status"] == "rto")
    returned = sum(item["qty"] for item in financials if item["status"] == "returned")
    cancelled = sum(item["qty"] for item in financials if item["status"] == "cancelled")
    revenue = sum(item["revenue"] for item in financials)
    profit = sum(item["net_profit"] for item in financials)
    rto_rate = round((rto / quantities) * 100, 1) if quantities else 0
    delivered_rate = round((delivered / quantities) * 100, 1) if quantities else 0
    score_row = next((item for item in sku_scores if item.get("sku", "").lower() == sku.lower()), None)
    display_name = (score_row or {}).get("product_name") or orders[0].get("product_name") or sku
    money = lambda value: f"₹{round(value):,}"

    if any(word in question.lower() for word in ("rto", "return", "risk")):
        return f"{sku} ({display_name}) has {rto_rate}% RTO risk, with {rto} RTO units and {returned} returned units out of {quantities} total."
    if any(word in question.lower() for word in ("profit", "margin", "revenue", "sales")):
        margin = round((profit / revenue) * 100, 1) if revenue else 0
        return f"{sku} generated {money(revenue)} in delivered revenue and {money(profit)} net profit, with an estimated {margin}% margin."
    if any(word in question.lower() for word in ("promote", "scale", "advert")):
        recommendation = "promote" if rto_rate < 15 and profit >= 0 else "avoid scaling until returns and profit improve"
        return f"For {sku}, I recommend you {recommendation}. It has a {delivered_rate}% delivered rate, {rto_rate}% RTO rate, and {money(profit)} net profit."
    if any(word in question.lower() for word in ("pause", "stop")):
        recommendation = "pause it for now" if profit < 0 or rto_rate >= 25 else "keep it active and monitor it"
        return f"For {sku}, I recommend you {recommendation}. Current net profit is {money(profit)} and RTO is {rto_rate}%."

    return f"{sku} ({display_name}) has {quantities} orders: {delivered} delivered, {cancelled} cancelled, {returned} returned, and {rto} RTO. Revenue is {money(revenue)} and net profit is {money(profit)}."


def _find_sku(question: str, sku_scores: list[dict], seller_email: str | None = None) -> str | None:
    question_lower = question.lower()
    known_skus = [str(item.get("sku") or "").strip() for item in sku_scores if item.get("sku")]
    known_skus.extend(str(row.get("sku") or "").strip() for row in _orders(seller_email) if row.get("sku"))
    for sku in sorted(known_skus, key=len, reverse=True):
        if sku.lower() in question_lower:
            return sku

    # Also support a new SKU that is present in orders but not yet scored.
    match = re.search(r"\bsku[-_ ]?[a-z0-9]+(?:[-_][a-z0-9]+)*\b", question_lower, re.IGNORECASE)
    return match.group(0).replace(" ", "-").upper() if match else None
