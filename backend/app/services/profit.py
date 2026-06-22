from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from app.database import get_db


DEFAULT_SETTINGS = {
    "product_cost_percent": 55.0,
    "marketplace_fee_percent": 15.0,
    "forward_shipping_per_order": 40.0,
    "return_shipping_per_order": 200.0,
    "ad_cost_percent": 8.0,
}


def _orders(seller_email: str | None = None) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT order_date, sku, product_name, status, discounted_price, listed_price, quantity
            FROM order_rows
            WHERE seller_email = ?
            ORDER BY date(order_date) ASC, id ASC
            """,
            (seller_email or "demo@seller-copilot.local",),
        ).fetchall()
    return [dict(row) for row in rows]


def _status_bucket(status: str) -> str:
    token = (status or "").strip().upper()
    if token in {"DELIVERED", "SUCCESS", "COMPLETED"}:
        return "delivered"
    if token in {"RTO", "RETURN TO ORIGIN"}:
        return "rto"
    if token in {"RETURNED", "RETURN"}:
        return "returned"
    if token in {"CANCELLED", "CANCELED", "CANCEL"}:
        return "cancelled"
    return "other"


def _load_settings(seller_email: str | None = None) -> dict[str, float]:
    settings = dict(DEFAULT_SETTINGS)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM profit_settings WHERE seller_email = ?",
            (seller_email or "demo@seller-copilot.local",),
        ).fetchall()
    for row in rows:
        settings[row["key"]] = float(row["value"])
    return settings


def save_settings(seller_email: str, values: dict) -> dict[str, float]:
    settings = _load_settings(seller_email)
    updated = dict(settings)
    with get_db() as conn:
        for key, default in DEFAULT_SETTINGS.items():
            if key in values:
                updated[key] = float(values[key])
                conn.execute(
                    """
                    INSERT INTO profit_settings (seller_email, key, value)
                    VALUES (?, ?, ?)
                    ON CONFLICT(seller_email, key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                    """,
                    (seller_email, key, float(values[key])),
                )
    return updated


def weekly_profit(seller_email: str | None = None) -> dict:
    seller_email = seller_email or "demo@seller-copilot.local"
    orders = _orders(seller_email)
    settings = _load_settings(seller_email)
    weeks: dict[str, dict] = defaultdict(lambda: {"sales": 0.0, "delivered_profit": 0.0, "return_loss": 0.0, "rto_loss": 0.0, "net_profit": 0.0})

    for row in orders:
        try:
            order_dt = datetime.fromisoformat(str(row["order_date"])).date()
        except ValueError:
            continue
        week_start = (order_dt - timedelta(days=order_dt.weekday())).isoformat()
        qty = max(1, int(row.get("quantity") or 1))
        sales = float(row.get("discounted_price") or 0) * qty
        cost = sales * (settings["product_cost_percent"] / 100.0)
        fee = sales * (settings["marketplace_fee_percent"] / 100.0)
        ads = sales * (settings["ad_cost_percent"] / 100.0)
        forward = settings["forward_shipping_per_order"] * qty
        status = _status_bucket(row.get("status"))
        delivered_profit = sales - cost - fee - ads - forward
        return_loss = settings["return_shipping_per_order"] * qty if status == "returned" else 0.0
        rto_loss = settings["return_shipping_per_order"] * qty if status == "rto" else 0.0
        net = delivered_profit - return_loss - rto_loss
        bucket = weeks[week_start]
        bucket["week_start"] = week_start
        bucket["sales"] += sales
        bucket["delivered_profit"] += max(0.0, delivered_profit) if status == "delivered" else 0.0
        bucket["return_loss"] += return_loss
        bucket["rto_loss"] += rto_loss
        bucket["net_profit"] += net

    week_rows = sorted(weeks.values(), key=lambda row: row["week_start"])
    for row in week_rows:
        row["status"] = "Profit" if row["net_profit"] >= 0 else "Loss"

    latest = week_rows[-1] if week_rows else None
    prev = week_rows[-2] if len(week_rows) >= 2 else None
    change_value = None if not latest or not prev else round(latest["net_profit"] - prev["net_profit"], 2)
    change_percent = None if change_value is None or prev["net_profit"] == 0 else round((change_value / abs(prev["net_profit"])) * 100, 1)
    trend = "Flat"
    if change_value is not None:
        trend = "Up" if change_value > 0 else "Down" if change_value < 0 else "Flat"

    sku_profit: dict[str, dict] = defaultdict(lambda: {"sales": 0.0, "return_loss": 0.0, "rto_loss": 0.0, "net_profit": 0.0, "returned_orders": 0, "rto_orders": 0})
    for row in orders:
        sku = (row.get("sku") or "UNKNOWN").strip() or "UNKNOWN"
        qty = max(1, int(row.get("quantity") or 1))
        sales = float(row.get("discounted_price") or 0) * qty
        cost = sales * (settings["product_cost_percent"] / 100.0)
        fee = sales * (settings["marketplace_fee_percent"] / 100.0)
        ads = sales * (settings["ad_cost_percent"] / 100.0)
        forward = settings["forward_shipping_per_order"] * qty
        delivered_profit = sales - cost - fee - ads - forward
        status = _status_bucket(row.get("status"))
        return_loss = settings["return_shipping_per_order"] * qty if status == "returned" else 0.0
        rto_loss = settings["return_shipping_per_order"] * qty if status == "rto" else 0.0
        bucket = sku_profit[sku]
        bucket["sku"] = sku
        bucket["product_name"] = row.get("product_name") or sku
        bucket["sales"] += sales
        bucket["return_loss"] += return_loss
        bucket["rto_loss"] += rto_loss
        bucket["net_profit"] += delivered_profit - return_loss - rto_loss
        bucket["returned_orders"] += qty if status == "returned" else 0
        bucket["rto_orders"] += qty if status == "rto" else 0

    sku_rows = sorted(sku_profit.values(), key=lambda row: row["net_profit"], reverse=True)
    return {
        "summary": {
            "sales": sum(row["sales"] for row in week_rows),
            "return_loss": sum(row["return_loss"] for row in week_rows),
            "rto_loss": sum(row["rto_loss"] for row in week_rows),
            "net_profit": sum(row["net_profit"] for row in week_rows),
            "profit_margin_percent": round((sum(row["net_profit"] for row in week_rows) / sum(row["sales"] for row in week_rows)) * 100, 1) if week_rows and sum(row["sales"] for row in week_rows) else 0.0,
            "status": "Healthy" if sum(row["net_profit"] for row in week_rows) >= 0 else "Needs attention",
        },
        "weeks": week_rows,
        "week_trend": week_rows,
        "latest_week_change": {"change_value": change_value, "change_percent": change_percent, "week_start": latest["week_start"] if latest else None, "trend": trend},
        "sku_profit": sku_rows,
        "settings": settings,
        "explanation": [
            "Use weekly profit to track whether sales are actually profitable after returns, shipping, fees, and ads.",
            "A positive net profit means the current mix is healthy enough to scale cautiously.",
        ],
    }
