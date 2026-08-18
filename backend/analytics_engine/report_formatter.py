def build_dashboard_summary(total_orders: int, rto_orders: int, net_profit: float, actions: list[dict]) -> dict:
    rto_pct = round((rto_orders / total_orders) * 100.0, 2) if total_orders > 0 else 0.0
    return {
        "total_orders": total_orders,
        "rto_orders": rto_orders,
        "rto_pct": rto_pct,
        "net_profit_inr": round(net_profit, 2),
        "top_actions": actions[:5],
    }
