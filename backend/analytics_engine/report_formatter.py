import math

def sanitize_float(value: float, default: float = 0.0) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    return num if math.isfinite(num) else default

def build_dashboard_summary(total_orders: int, rto_orders: int, net_profit: float, actions: list[dict]) -> dict:
    rto_pct = round((rto_orders / total_orders) * 100.0, 2) if total_orders > 0 else 0.0
    return {
        "total_orders": int(total_orders),
        "rto_orders": int(rto_orders),
        "rto_pct": sanitize_float(rto_pct),
        "net_profit_inr": round(sanitize_float(net_profit), 2),
        "top_actions": actions[:5],
    }
