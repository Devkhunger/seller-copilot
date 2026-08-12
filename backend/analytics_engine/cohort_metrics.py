def wow_delta_pct(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100.0, 2)

def aggregate_weekly_series(weekly_rows: list[dict]) -> list[dict]:
    output = []
    prev_orders = 0
    for idx, row in enumerate(weekly_rows):
        orders = int(row.get("orders", 0))
        rtos = int(row.get("rtos", 0))
        rto_rate = round(rtos / orders, 4) if orders > 0 else 0.0
        delta = wow_delta_pct(orders, prev_orders) if idx > 0 else None
        output.append({
            "week": row["week"],
            "orders": orders,
            "rto_rate": rto_rate,
            "orders_wow_pct": delta,
        })
        prev_orders = orders
    return output
