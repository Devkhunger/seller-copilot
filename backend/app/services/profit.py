
from __future__ import annotations

import pandas as pd

from app.database import get_db
from app.services.analytics import load_orders_df, status_mask


DEFAULT_SETTINGS = {
    "product_cost_percent": 55.0,
    "marketplace_fee_percent": 15.0,
    "forward_shipping_per_order": 40.0,
    "return_shipping_per_order": 200.0,
    "ad_cost_percent": 8.0,
}


def get_profit_settings(seller_email: str | None = None) -> dict:
    settings = DEFAULT_SETTINGS.copy()
    if not seller_email:
        return settings
    with get_db() as conn:
        rows = conn.execute("SELECT key, value FROM profit_settings WHERE seller_email = ?", (seller_email,)).fetchall()
    for row in rows:
        if row["key"] in settings:
            settings[row["key"]] = float(row["value"])
    return settings


def save_profit_settings(payload: dict, seller_email: str | None = None) -> dict:
    settings = get_profit_settings(seller_email)
    for key in settings:
        if key in payload and payload[key] is not None:
            settings[key] = max(0, float(payload[key]))
    if not seller_email:
        return settings
    with get_db() as conn:
        for key, value in settings.items():
            conn.execute(
                """
                INSERT INTO profit_settings (seller_email, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(seller_email, key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (seller_email, key, value),
            )
    return settings


def weekly_profit_report(seller_email: str | None = None) -> dict:
    df = load_orders_df(seller_email)
    settings = get_profit_settings(seller_email)
    if df.empty:
        return {"settings": settings, "summary": _empty_summary(), "weeks": [], "sku_profit": []}

    work = df.copy()
    work["order_date"] = pd.to_datetime(work["order_date"], errors="coerce")
    work = work.dropna(subset=["order_date"])
    if work.empty:
        return {"settings": settings, "summary": _empty_summary(), "weeks": [], "sku_profit": []}

    work["week_start"] = work["order_date"].dt.to_period("W-MON").apply(lambda item: item.start_time.date().isoformat())
    financials = _row_financials(work, settings)
    merged = pd.concat([work.reset_index(drop=True), financials], axis=1)

    weeks = []
    for week, group in merged.groupby("week_start"):
        row = _group_profit_row(group, "week_start", week)
        weeks.append(row)
    weeks = sorted(weeks, key=lambda item: item["week_start"], reverse=True)

    sku_profit = []
    for sku, group in merged.groupby("sku"):
        row = _group_profit_row(group, "sku", sku)
        row["product_name"] = str(group["product_name"].mode().iloc[0]) if not group["product_name"].mode().empty else sku
        sku_profit.append(row)
    sku_profit = sorted(sku_profit, key=lambda item: item["net_profit"], reverse=True)[:15]

    summary = _group_profit_row(merged, "summary", "All Orders")
    summary["status"] = "Profit" if summary["net_profit"] >= 0 else "Loss"
    summary["profit_margin_percent"] = _percent(summary["net_profit"], summary["sales"])

    return {
        "settings": settings,
        "summary": summary,
        "weeks": weeks[:12],
        "sku_profit": sku_profit,
        "explanation": [
            "Delivered orders count sales after estimated product cost, marketplace fee, shipping, and ad cost.",
            "Customer returns count as lost expected profit plus return shipping, because the item comes back and the seller pays the return shipment.",
            "RTO stays separate and is treated as a delivery failure without return-shipping deduction.",
            "Use real cost values here for accurate profit/loss tracking.",
        ],
    }


def _row_financials(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    quantity = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).clip(lower=1)
    sale_value = pd.to_numeric(df["discounted_price"], errors="coerce").fillna(0) * quantity
    product_cost = sale_value * (settings["product_cost_percent"] / 100)
    marketplace_fee = sale_value * (settings["marketplace_fee_percent"] / 100)
    forward_shipping = quantity * settings["forward_shipping_per_order"]
    ad_cost = sale_value * (settings["ad_cost_percent"] / 100) * _paid_source_mask(df).astype(float)
    expected_profit = sale_value - product_cost - marketplace_fee - forward_shipping - ad_cost
    return_shipping = quantity * settings["return_shipping_per_order"]

    delivered = status_mask(df, "delivered")
    rto = status_mask(df, "rto")
    customer_return = status_mask(df, "return")
    cancelled = status_mask(df, "cancelled")

    sales = sale_value.where(delivered, 0)
    delivered_profit = expected_profit.where(delivered, 0)
    return_loss = (expected_profit.clip(lower=0) + return_shipping).where(customer_return, 0)
    rto_loss = expected_profit.clip(lower=0).where(rto, 0)
    cancellation_loss = (forward_shipping * 0.25).where(cancelled, 0)
    net_profit = delivered_profit - return_loss - rto_loss - cancellation_loss

    return pd.DataFrame(
        {
            "sales": sales,
            "delivered_profit": delivered_profit,
            "return_loss": return_loss,
            "rto_loss": rto_loss,
            "cancellation_loss": cancellation_loss,
            "net_profit": net_profit,
            "delivered_qty": quantity.where(delivered, 0),
            "returned_qty": quantity.where(customer_return, 0),
            "rto_qty": quantity.where(rto, 0),
            "cancelled_qty": quantity.where(cancelled, 0),
        }
    )


def _group_profit_row(group: pd.DataFrame, key_name: str, key_value: str) -> dict:
    row = {
        key_name: key_value,
        "sales": round(float(group["sales"].sum()), 2),
        "delivered_profit": round(float(group["delivered_profit"].sum()), 2),
        "return_loss": round(float(group["return_loss"].sum()), 2),
        "rto_loss": round(float(group["rto_loss"].sum()), 2),
        "cancellation_loss": round(float(group["cancellation_loss"].sum()), 2),
        "net_profit": round(float(group["net_profit"].sum()), 2),
        "delivered_orders": int(group["delivered_qty"].sum()),
        "returned_orders": int(group["returned_qty"].sum()),
        "rto_orders": int(group["rto_qty"].sum()),
        "cancelled_orders": int(group["cancelled_qty"].sum()),
    }
    row["profit_margin_percent"] = _percent(row["net_profit"], row["sales"])
    row["status"] = "Profit" if row["net_profit"] >= 0 else "Loss"
    return row


def _paid_source_mask(df: pd.DataFrame) -> pd.Series:
    return df["order_source"].fillna("").astype(str).str.lower().str.contains("ad|paid|sponsored", na=False)


def _percent(value: float, total: float) -> float:
    if not total:
        return 0.0
    return round((float(value) / float(total)) * 100, 1)


def _empty_summary() -> dict:
    return {
        "summary": "All Orders",
        "sales": 0,
        "delivered_profit": 0,
        "return_loss": 0,
        "rto_loss": 0,
        "cancellation_loss": 0,
        "net_profit": 0,
        "delivered_orders": 0,
        "returned_orders": 0,
        "rto_orders": 0,
        "cancelled_orders": 0,
        "profit_margin_percent": 0,
        "status": "No Data",
    }
