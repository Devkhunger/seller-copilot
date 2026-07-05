def compute_sku_score(orders: int, rto_count: int, net_margin_pct: float) -> float:
    if orders <= 0:
        return 0.0
    rto_rate = min(1.0, max(0.0, rto_count / orders))
    volume_component = min(35.0, (orders ** 0.7) * 2.5)
    delivery_component = (1.0 - rto_rate) * 40.0
    margin_component = max(0.0, min(25.0, net_margin_pct * 0.85))
    return round(min(100.0, volume_component + delivery_component + margin_component), 2)

def classify_sku_tier(score: float, rto_rate: float) -> str:
    if rto_rate >= 0.35 or score < 40.0:
        return "at_risk"
    if score >= 75.0 and rto_rate <= 0.12:
        return "star"
    if score >= 55.0:
        return "stable"
    return "watch"
