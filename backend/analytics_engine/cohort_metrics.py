def wow_delta_pct(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100.0, 2)

def rolling_average(values: list[float], window: int = 3) -> list[float]:
    if window <= 0:
        return []
    result = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1):i + 1]
        result.append(round(sum(chunk) / len(chunk), 2))
    return result

def aggregate_weekly_series(weekly_rows: list[dict]) -> list[dict]:
    output = []
    prev_orders = 0
    order_vals = [int(r.get("orders", 0)) for r in weekly_rows]
    smoothed = rolling_average(order_vals, window=3)
    for idx, row in enumerate(weekly_rows):
        orders = order_vals[idx]
        rtos = int(row.get("rtos", 0))
        rto_rate = round(rtos / orders, 4) if orders > 0 else 0.0
        delta = wow_delta_pct(orders, prev_orders) if idx > 0 else None
        output.append({
            "week": row["week"],
            "orders": orders,
            "orders_ma3": smoothed[idx],
            "rto_rate": rto_rate,
            "orders_wow_pct": delta,
        })
        prev_orders = orders
    return output
