from app.database import get_db
from app.services.analytics import average_daily_orders_by_sku


def upsert_inventory(sku: str, current_stock: int) -> dict:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO inventory (sku, current_stock, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sku) DO UPDATE SET
              current_stock = excluded.current_stock,
              updated_at = CURRENT_TIMESTAMP
            """,
            (sku, current_stock),
        )
    return {"sku": sku, "current_stock": current_stock}


def inventory_report() -> list[dict]:
    avg_daily = average_daily_orders_by_sku()
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM inventory ORDER BY sku").fetchall()
    stored = {row["sku"]: row["current_stock"] for row in rows}
    all_skus = sorted(set(avg_daily) | set(stored))
    report = []
    for sku in all_skus:
        avg = avg_daily.get(sku, 0)
        stock = int(stored.get(sku, 0))
        days_left = round(stock / avg, 1) if avg > 0 else None
        if days_left is not None and days_left <= 7:
            alert = "Stockout Risk"
        elif avg < 0.3:
            alert = "Slow Moving"
        else:
            alert = "Healthy"
        report.append(
            {
                "sku": sku,
                "current_stock": stock,
                "avg_daily_orders": avg,
                "days_left": days_left,
                "alert": alert,
            }
        )
    return report

