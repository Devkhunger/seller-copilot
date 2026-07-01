def compute_sku_score(orders: int, rto_count: int, net_margin_pct: float) -> float:
    rto_rate = rto_count / orders
    volume_component = min(40.0, orders * 0.8)
    delivery_component = (1.0 - rto_rate) * 40.0
    margin_component = max(0.0, min(20.0, net_margin_pct))
    return round(volume_component + delivery_component + margin_component, 2)
