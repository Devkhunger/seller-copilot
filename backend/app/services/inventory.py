
from app.database import get_db
from app.services.analytics import average_daily_orders_by_sku


def upsert_inventory(sku: str, current_stock: int, seller_email: str | None = None) -> dict:
    if not seller_email:
        return {"sku": sku, "current_stock": current_stock}
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO inventory (seller_email, sku, current_stock, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(seller_email, sku) DO UPDATE SET
              current_stock = excluded.current_stock,
              updated_at = CURRENT_TIMESTAMP
            """,
            (seller_email, sku, current_stock),
        )
    return {"sku": sku, "current_stock": current_stock}


def inventory_report(seller_email: str | None = None) -> list[dict]:
    avg_daily = average_daily_orders_by_sku(seller_email)
    with get_db() as conn:
        if seller_email:
            rows = conn.execute("SELECT * FROM inventory WHERE seller_email = ? ORDER BY sku", (seller_email,)).fetchall()
        else:
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
