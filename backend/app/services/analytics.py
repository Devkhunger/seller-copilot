from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from math import ceil

from app.database import get_db


def _fetch_orders(seller_email: str | None = None) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT order_date, sku, product_name, customer_state, status, order_source,
                   listed_price, discounted_price, quantity
            FROM order_rows
            WHERE seller_email = ?
            ORDER BY date(order_date) ASC, id ASC
            """,
            (seller_email or "demo@seller-copilot.local",),
        ).fetchall()
    return [dict(row) for row in rows]


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            return None


def _status_bucket(status: str) -> str:
    token = (status or "").strip().upper()
    if token in {"DELIVERED", "SUCCESS", "COMPLETED"}:
        return "delivered"
    if token in {"RTO", "RETURN TO ORIGIN", "RETURNED", "RETURN"}:
        return "rto"
    if token in {"CANCELLED", "CANCELED", "CANCEL"}:
        return "cancelled"
    return "other"


def _money(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def calculate_sku_scores(seller_email: str | None = None) -> list[dict]:
    orders = _fetch_orders(seller_email)
    if not orders:
        return []

    now = max((_parse_date(row["order_date"]) for row in orders if _parse_date(row["order_date"])), default=date.today())
    by_sku: dict[str, list[dict]] = defaultdict(list)
    for row in orders:
        sku = (row.get("sku") or "").strip() or "UNKNOWN"
        by_sku[sku].append(row)

    max_orders = max(sum(max(1, int(row.get("quantity") or 1)) for row in rows) for rows in by_sku.values()) or 1
    scores: list[dict] = []
    for sku, rows in by_sku.items():
        quantities = [max(1, int(row.get("quantity") or 1)) for row in rows]
        total_orders = sum(quantities)
        delivered = sum(q for row, q in zip(rows, quantities) if _status_bucket(row.get("status")) == "delivered")
        cancelled = sum(q for row, q in zip(rows, quantities) if _status_bucket(row.get("status")) == "cancelled")
        rto = sum(q for row, q in zip(rows, quantities) if _status_bucket(row.get("status")) == "rto")
        natural = sum(q for row, q in zip(rows, quantities) if "ad" not in str(row.get("order_source", "")).lower())
        ad = total_orders - natural
        discounts = []
        recency_days = []
        for row, qty in zip(rows, quantities):
            listed = _money(row.get("listed_price"))
            discounted = _money(row.get("discounted_price"))
            if listed > 0:
                discounts.append(max(0.0, min(100.0, ((listed - discounted) / listed) * 100.0)))
            order_dt = _parse_date(row.get("order_date"))
            if order_dt:
                recency_days.append((now - order_dt).days)

        recent_7 = sum(q for row, q in zip(rows, quantities) if _parse_date(row.get("order_date")) and (now - _parse_date(row.get("order_date"))).days <= 7)
        prev_7 = sum(
            q
            for row, q in zip(rows, quantities)
            if _parse_date(row.get("order_date"))
            and 7 < (now - _parse_date(row.get("order_date"))).days <= 14
        )

        delivered_rate = round((delivered / total_orders) * 100, 1) if total_orders else 0.0
        cancelled_rate = round((cancelled / total_orders) * 100, 1) if total_orders else 0.0
        rto_rate = round((rto / total_orders) * 100, 1) if total_orders else 0.0
        natural_share = round((natural / total_orders) * 100, 1) if total_orders else 0.0
        ad_share = round((ad / total_orders) * 100, 1) if total_orders else 0.0
        avg_discount = round(sum(discounts) / len(discounts), 1) if discounts else 0.0
        recency_score = max(0, 100 - (min(recency_days) if recency_days else 90) * 3)
        momentum_score = 50 + min(30, (recent_7 - prev_7) * 5)
        consistency_score = round(min(100.0, (total_orders / max_orders) * 100.0), 1)
        score = round(
            min(
                100.0,
                max(
                    0.0,
                    0.38 * delivered_rate
                    + 0.18 * natural_share
                    + 0.12 * recency_score
                    + 0.12 * momentum_score
                    + 0.10 * consistency_score
                    - 0.06 * rto_rate
                    - 0.04 * cancelled_rate
                    - 0.02 * avg_discount,
                ),
            ),
            1,
        )
        if score >= 75 and rto_rate < 10:
            action = "Scale"
        elif score < 45 or rto_rate > 25:
            action = "Fix"
        else:
            action = "Watch"
        scores.append(
            {
                "sku": sku,
                "product_name": rows[0].get("product_name") or sku,
                "orders": total_orders,
                "delivered_rate": delivered_rate,
                "cancelled_rate": cancelled_rate,
                "rto_rate": rto_rate,
                "natural_share_pct": natural_share,
                "ad_share_pct": ad_share,
                "avg_discount_pct": avg_discount,
                "recency_score": int(round(recency_score)),
                "momentum_score": int(round(momentum_score)),
                "consistency_score": consistency_score,
                "score": score,
                "action": action,
                "natural_orders": natural,
                "ad_orders": ad,
            }
        )

    scores.sort(key=lambda item: (item["score"], item["orders"]), reverse=True)
    return scores


def dashboard_metrics(seller_email: str | None = None) -> dict:
    orders = _fetch_orders(seller_email)
    sku_scores = calculate_sku_scores(seller_email)
    delivered_orders = sum(max(1, int(row.get("quantity") or 1)) for row in orders if _status_bucket(row.get("status")) == "delivered")
    total_orders = sum(max(1, int(row.get("quantity") or 1)) for row in orders)
    rto_orders = sum(max(1, int(row.get("quantity") or 1)) for row in orders if _status_bucket(row.get("status")) == "rto")
    cancelled_orders = sum(max(1, int(row.get("quantity") or 1)) for row in orders if _status_bucket(row.get("status")) == "cancelled")
    total_revenue = sum(_money(row.get("discounted_price")) * max(1, int(row.get("quantity") or 1)) for row in orders)
    top_sku = sku_scores[0] if sku_scores else None
    return {
        "summary": {
            "orders": total_orders,
            "skus": len(sku_scores),
            "delivered_rate": round((delivered_orders / total_orders) * 100, 1) if total_orders else 0.0,
            "rto_rate": round((rto_orders / total_orders) * 100, 1) if total_orders else 0.0,
            "cancelled_rate": round((cancelled_orders / total_orders) * 100, 1) if total_orders else 0.0,
            "revenue": round(total_revenue, 2),
        },
        "top_sku": top_sku,
        "recent_orders": orders[-10:][::-1],
    }


def rto_risk_analysis(seller_email: str | None = None) -> dict:
    orders = _fetch_orders(seller_email)
    rows: list[dict] = []
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in orders:
        grouped[((row.get("sku") or "UNKNOWN").strip() or "UNKNOWN", (row.get("customer_state") or "Unknown").strip() or "Unknown")].append(row)

    for (sku, state), items in grouped.items():
        quantities = [max(1, int(row.get("quantity") or 1)) for row in items]
        total = sum(quantities)
        rto = sum(q for row, q in zip(items, quantities) if _status_bucket(row.get("status")) == "rto")
        cancelled = sum(q for row, q in zip(items, quantities) if _status_bucket(row.get("status")) == "cancelled")
        risk = round(min(100.0, max(0.0, (rto / total) * 100.0 + (cancelled / total) * 25.0)), 1) if total else 0.0
        label = "High Risk" if risk >= 35 else "Low Risk" if risk <= 15 else "Medium Risk"
        rows.append(
            {
                "sku": sku,
                "customer_state": state,
                "orders": total,
                "rto_rate": risk,
                "risk_label": label,
                "confidence": "High" if total >= 10 else "Medium" if total >= 3 else "Low",
            }
        )

    rows.sort(key=lambda item: (item["rto_rate"], item["orders"]), reverse=True)
    high_risk = [row for row in rows if row["risk_label"] == "High Risk"]
    return {
        "items": rows,
        "high_risk_combos": high_risk,
        "summary": {
            "high_risk_count": len(high_risk),
            "total_combos": len(rows),
        },
    }


def safe_state_sku_combos(seller_email: str | None = None) -> list[dict]:
    items = rto_risk_analysis(seller_email)["items"]
    return [item for item in items if item["risk_label"] == "Low Risk"][:10]
