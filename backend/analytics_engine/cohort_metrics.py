def aggregate_weekly_series(weekly_rows: list[dict]) -> list[dict]:
    output = []
    for row in weekly_rows:
        orders = int(row.get("orders", 0))
        rtos = int(row.get("rtos", 0))
        rto_rate = round(rtos / orders, 4) if orders > 0 else 0.0
        output.append({"week": row["week"], "orders": orders, "rto_rate": rto_rate})
    return output
