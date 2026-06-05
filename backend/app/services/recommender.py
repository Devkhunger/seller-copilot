from app.services.analytics import calculate_sku_scores, rto_risk_analysis, safe_state_sku_combos


def generate_recommendations(seller_email: str | None = None) -> dict:
    sku_scores = calculate_sku_scores(seller_email=seller_email)
    risk = rto_risk_analysis(seller_email)
    promote = [sku for sku in sku_scores if sku["score"] >= 75 and sku["rto_rate"] < 10]
    pause = [sku for sku in sku_scores if sku["score"] < 45 or sku["rto_rate"] > 25]
    listing = [
        sku for sku in sku_scores
        if (sku["orders"] <= 5 and sku["delivered_rate"] >= 60) or sku["natural_orders"] <= max(1, sku["orders"] * 0.2)
    ]
    safe_combos = safe_state_sku_combos(seller_email)
    ad_recommendation = _build_ad_recommendation(promote, safe_combos)
    return {
        "promote_skus": promote[:5],
        "pause_skus": pause[:5],
        "listing_improvements": listing[:5],
        "safe_combos": safe_combos,
        "ad_recommendation": ad_recommendation,
        "insights": _insights(promote, pause, listing, risk),
    }


def today_actions(seller_email: str | None = None) -> list[str]:
    recs = generate_recommendations(seller_email)
    actions: list[str] = []
    if recs.get("ad_recommendation"):
        ad = recs["ad_recommendation"]
        actions.append(
            f"Run ads for {ad['product_name']} ({ad['sku']}) in {ad['recommended_state']}."
        )
    elif recs["promote_skus"]:
        actions.append(f"Push {recs['promote_skus'][0]['product_name']} in ads.")
    if recs["pause_skus"]:
        sku = recs["pause_skus"][0]
        actions.append(f"Pause {sku['product_name']} until RTO and cancellation improve.")
    if recs["listing_improvements"]:
        actions.append(f"Rewrite {recs['listing_improvements'][0]['product_name']} listing title and bullets.")
    if len(actions) < 3 and recs["safe_combos"]:
        combo = recs["safe_combos"][0]
        actions.append(f"Scale {combo['sku']} in {combo['customer_state']} because delivery quality is strong.")
    while len(actions) < 3:
        actions.append("Upload fresh orders tomorrow and review SKU scores before spending on ads.")
    return actions[:3]


def _build_ad_recommendation(promote: list[dict], safe_combos: list[dict]) -> dict | None:
    if not promote:
        return None

    top_sku = promote[0]
    matching_safe = next((combo for combo in safe_combos if combo["sku"] == top_sku["sku"]), None)
    if matching_safe:
        return {
            "sku": top_sku["sku"],
            "product_name": top_sku["product_name"],
            "recommended_state": matching_safe["customer_state"],
            "reason": "High score, low RTO, and strong delivery in this state.",
            "confidence": "High",
        }

    return {
        "sku": top_sku["sku"],
        "product_name": top_sku["product_name"],
        "recommended_state": "best-performing states",
        "reason": "High score and low RTO make it a good candidate for paid traffic.",
        "confidence": "Medium",
    }


def _insights(promote, pause, listing, risk) -> list[str]:
    insights = []
    if promote:
        insights.append(f"Promote {promote[0]['product_name']} because it has high score and low RTO.")
    if pause:
        insights.append(f"Pause or limit {pause[0]['product_name']} because losses are likely.")
    if listing:
        insights.append(f"Improve listing content for {listing[0]['product_name']} to increase natural orders.")
    if risk["high_risk_combos"]:
        combo = risk["high_risk_combos"][0]
        insights.append(f"{combo['customer_state']} has {combo['rto_rate']}% RTO for {combo['sku']}. Avoid paid ads there.")
    return insights

