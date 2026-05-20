from app.services.analytics import calculate_sku_scores, rto_risk_analysis, safe_state_sku_combos


def generate_recommendations() -> dict:
    sku_scores = calculate_sku_scores()
    risk = rto_risk_analysis()
    promote = [sku for sku in sku_scores if sku["score"] >= 75 and sku["rto_rate"] < 10]
    pause = [sku for sku in sku_scores if sku["score"] < 45 or sku["rto_rate"] > 25]
    listing = [
        sku for sku in sku_scores
        if (sku["orders"] <= 5 and sku["delivered_rate"] >= 60) or sku["natural_orders"] <= max(1, sku["orders"] * 0.2)
    ]
    return {
        "promote_skus": promote[:5],
        "pause_skus": pause[:5],
        "listing_improvements": listing[:5],
        "safe_combos": safe_state_sku_combos(),
        "insights": _insights(promote, pause, listing, risk),
    }


def today_actions() -> list[str]:
    recs = generate_recommendations()
    actions: list[str] = []
    if recs["promote_skus"]:
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

