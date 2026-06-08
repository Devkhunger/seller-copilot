
from __future__ import annotations

import pandas as pd

from app.database import get_db


def load_orders_df(seller_email: str | None = None) -> pd.DataFrame:
    with get_db() as conn:
        if seller_email:
            rows = conn.execute("SELECT * FROM order_rows WHERE seller_email = ?", (seller_email,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM order_rows").fetchall()
    df = pd.DataFrame([dict(row) for row in rows])
    if df.empty:
        return pd.DataFrame(
            columns=[
                "order_date",
                "sku",
                "product_name",
                "customer_state",
                "status",
                "order_source",
                "listed_price",
                "discounted_price",
                "quantity",
                "seller_email",
            ]
        )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1)
    df["discounted_price"] = pd.to_numeric(df["discounted_price"], errors="coerce").fillna(0)
    df["listed_price"] = pd.to_numeric(df["listed_price"], errors="coerce").fillna(0)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    sort_cols = ["order_date"]
    if "id" in df.columns:
        sort_cols.append("id")
    return df.sort_values(sort_cols, kind="mergesort", na_position="last").reset_index(drop=True)


def status_mask(df: pd.DataFrame, kind: str) -> pd.Series:
    status = df["status"].fillna("").astype(str).str.upper()
    if kind == "delivered":
        return status.str.contains("DELIVERED", na=False)
    if kind == "cancelled":
        return status.str.contains("CANCELLED", na=False)
    if kind == "rto":
        return status.str.contains("RTO", na=False)
    if kind == "return":
        return status.str.contains("RETURN", na=False) & ~status.str.contains("RTO", na=False)
    known = (
        status.str.contains("DELIVERED", na=False)
        | status.str.contains("CANCELLED", na=False)
        | status.str.contains("RTO", na=False)
        | (status.str.contains("RETURN", na=False) & ~status.str.contains("RTO", na=False))
    )
    return ~known


def dashboard_metrics(seller_email: str | None = None) -> dict:
    df = load_orders_df(seller_email)
    if df.empty:
        return _empty_dashboard()

    total = int(df["quantity"].sum())
    delivered = int(df.loc[status_mask(df, "delivered"), "quantity"].sum())
    cancelled = int(df.loc[status_mask(df, "cancelled"), "quantity"].sum())
    rto = int(df.loc[status_mask(df, "rto"), "quantity"].sum())
    unknown = int(df.loc[status_mask(df, "unknown"), "quantity"].sum())
    revenue = float((df.loc[status_mask(df, "delivered"), "discounted_price"] * df.loc[status_mask(df, "delivered"), "quantity"]).sum())
    sku_scores = calculate_sku_scores(df)
    source_counts = df.groupby("order_source")["quantity"].sum().sort_values(ascending=False).to_dict()
    ad_orders = int(df[df["order_source"].astype(str).str.lower().str.contains("ad|paid|sponsored", na=False)]["quantity"].sum())
    natural_orders = int(total - ad_orders)

    return {
        "total_orders": total,
        "delivered_orders": delivered,
        "cancelled_orders": cancelled,
        "rto_orders": rto,
        "unknown_orders": unknown,
        "revenue_estimate": round(revenue, 2),
        "top_selling_sku": _top_by_quantity(df, "sku"),
        "worst_performing_sku": sku_scores[-1]["sku"] if sku_scores else "",
        "ad_orders": ad_orders,
        "natural_orders": natural_orders,
        "order_source_breakdown": source_counts,
    }


def calculate_sku_scores(df: pd.DataFrame | None = None, seller_email: str | None = None) -> list[dict]:
    df = load_orders_df(seller_email) if df is None else df
    if df.empty:
        return []

    work = df.copy()
    work["order_date"] = pd.to_datetime(work["order_date"], errors="coerce")
    work["discount_pct"] = work.apply(_discount_pct, axis=1)
    work["is_paid_source"] = _paid_source_mask(work).astype(int)

    max_volume = max(float(work.groupby("sku")["quantity"].sum().max()), 1)
    latest_day = work["order_date"].dropna().max()
    rows: list[dict] = []

    for sku, group in work.groupby("sku"):
        orders = int(group["quantity"].sum())
        delivered = int(group.loc[status_mask(group, "delivered"), "quantity"].sum())
        cancelled = int(group.loc[status_mask(group, "cancelled"), "quantity"].sum())
        rto = int(group.loc[status_mask(group, "rto"), "quantity"].sum())
        delivered_rate = delivered / max(orders, 1)
        cancellation_rate = cancelled / max(orders, 1)
        rto_rate = rto / max(orders, 1)
        normalized_order_volume = orders / max_volume

        ad_orders = int(group.loc[group["is_paid_source"].astype(bool), "quantity"].sum())
        natural_orders = orders - ad_orders
        ad_share_pct = (ad_orders / max(orders, 1)) * 100
        natural_share_pct = 100 - ad_share_pct

        discount_mean = group["discount_pct"].mean()
        avg_discount_pct = float(discount_mean) if not pd.isna(discount_mean) else 0.0
        recency_score = _recency_score(latest_day, group["order_date"].dropna().max())
        momentum_score = _momentum_score(group, latest_day)
        consistency_score = _consistency_score(group)
        state_diversity = _state_diversity_score(group)
        discount_pressure = min(100.0, max(0.0, avg_discount_pct))

        score = (
            18
            + (delivered_rate * 22)
            + (normalized_order_volume * 12)
            + (natural_share_pct * 0.08)
            + (recency_score * 0.10)
            + (momentum_score * 0.10)
            + (consistency_score * 0.06)
            + (state_diversity * 4)
            - (rto_rate * 0.18)
            - (cancellation_rate * 0.10)
            - (ad_share_pct * 0.04)
            - (discount_pressure * 0.05)
        )
        score = max(0, min(100, round(score)))

        rows.append(
            {
                "sku": sku,
                "product_name": str(group["product_name"].mode().iloc[0]) if not group["product_name"].mode().empty else sku,
                "orders": orders,
                "delivered_rate": round(delivered_rate * 100, 1),
                "cancelled_rate": round(cancellation_rate * 100, 1),
                "rto_rate": round(rto_rate * 100, 1),
                "natural_orders": natural_orders,
                "ad_orders": ad_orders,
                "natural_share_pct": round(natural_share_pct, 1),
                "ad_share_pct": round(ad_share_pct, 1),
                "avg_discount_pct": round(avg_discount_pct, 1),
                "recency_score": round(recency_score, 1),
                "momentum_score": round(momentum_score, 1),
                "consistency_score": round(consistency_score, 1),
                "state_diversity_score": round(state_diversity, 1),
                "score": score,
                "action": "Push" if score >= 75 else "Watch" if score >= 45 else "Pause",
            }
        )
    return sorted(rows, key=lambda item: item["score"], reverse=True)


def _paid_source_mask(df: pd.DataFrame) -> pd.Series:
    return df["order_source"].fillna("").astype(str).str.lower().str.contains("ad|paid|sponsored", na=False)


def _discount_pct(row) -> float:
    listed = float(row.get("listed_price") or 0)
    discounted = float(row.get("discounted_price") or 0)
    if listed <= 0:
        return 0.0
    return max(0.0, min(100.0, ((listed - discounted) / listed) * 100))


def _recency_score(latest_day, last_order_day) -> float:
    if pd.isna(latest_day) or pd.isna(last_order_day):
        return 50.0
    days_since = max(0, int((latest_day.normalize() - last_order_day.normalize()).days))
    return max(0.0, min(100.0, 100.0 / (1.0 + (days_since / 14.0))))


def _momentum_score(group: pd.DataFrame, latest_day) -> float:
    dated = group.dropna(subset=["order_date"]).copy()
    if dated.empty or pd.isna(latest_day):
        return 50.0
    recent_start = latest_day.normalize() - pd.Timedelta(days=13)
    previous_start = latest_day.normalize() - pd.Timedelta(days=27)
    recent_orders = float(dated.loc[dated["order_date"] >= recent_start, "quantity"].sum())
    previous_orders = float(dated.loc[(dated["order_date"] < recent_start) & (dated["order_date"] >= previous_start), "quantity"].sum())
    if recent_orders <= 0 and previous_orders <= 0:
        return 50.0
    if previous_orders <= 0:
        return 75.0 if recent_orders > 0 else 50.0
    change = (recent_orders - previous_orders) / max(previous_orders, recent_orders, 1.0)
    return max(0.0, min(100.0, 50.0 + (change * 50.0)))


def _consistency_score(group: pd.DataFrame) -> float:
    dated = group.dropna(subset=["order_date"]).copy()
    if dated.empty:
        return 50.0
    daily = dated.groupby(dated["order_date"].dt.normalize())["quantity"].sum()
    if len(daily) < 2:
        return 60.0 if len(daily) == 1 else 50.0
    mean = float(daily.mean())
    if mean <= 0:
        return 50.0
    cv = float(daily.std(ddof=0)) / mean
    return max(0.0, min(100.0, 100.0 / (1.0 + cv)))


def _state_diversity_score(group: pd.DataFrame) -> float:
    states = group["customer_state"].fillna("").astype(str).str.strip()
    states = states[states != ""]
    if states.empty:
        return 50.0
    unique_states = states.nunique()
    return max(0.0, min(100.0, (unique_states / 5.0) * 100.0))


def rto_risk_analysis(seller_email: str | None = None) -> dict:
    df = load_orders_df(seller_email)
    if df.empty:
        return {"high_risk_states": [], "high_risk_skus": [], "high_risk_combos": [], "source_rto": []}
    return {
        "high_risk_states": _risk_table(df, ["customer_state"]),
        "high_risk_skus": _risk_table(df, ["sku"]),
        "high_risk_combos": _risk_table(df, ["customer_state", "sku"]),
        "source_rto": _risk_table(df, ["order_source"], minimum_orders=1, high_risk_only=False),
    }


def _risk_table(df: pd.DataFrame, group_cols: list[str], minimum_orders: int = 5, high_risk_only: bool = True) -> list[dict]:
    rows = []
    for keys, group in df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        orders = int(group["quantity"].sum())
        rto = int(group.loc[status_mask(group, "rto"), "quantity"].sum())
        delivered = int(group.loc[status_mask(group, "delivered"), "quantity"].sum())
        rto_rate = rto / max(orders, 1)
        if orders < minimum_orders:
            continue
        if high_risk_only and rto_rate < 0.2:
            continue
        row = {column: key for column, key in zip(group_cols, keys)}
        row.update(
            {
                "orders": orders,
                "rto_orders": rto,
                "delivered_rate": round((delivered / max(orders, 1)) * 100, 1),
                "rto_rate": round(rto_rate * 100, 1),
                "risk_label": "High Risk" if rto_rate >= 0.2 else "Low Risk",
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda item: item["rto_rate"], reverse=True)


def safe_state_sku_combos(seller_email: str | None = None) -> list[dict]:
    df = load_orders_df(seller_email)
    if df.empty:
        return []
    combos = _risk_table(df, ["customer_state", "sku"], minimum_orders=3, high_risk_only=False)
    return [
        combo for combo in combos
        if combo["delivered_rate"] >= 80 and combo["rto_rate"] <= 10
    ][:5]


def average_daily_orders_by_sku(seller_email: str | None = None) -> dict[str, float]:
    df = load_orders_df(seller_email)
    if df.empty:
        return {}
    result = {}
    for sku, group in df.groupby("sku"):
        dates = group["order_date"].dropna()
        days = max(1, int((dates.max() - dates.min()).days) + 1) if not dates.empty else 1
        result[sku] = round(float(group["quantity"].sum()) / days, 2)
    return result


def _top_by_quantity(df: pd.DataFrame, column: str) -> str:
    grouped = df.groupby(column)["quantity"].sum().sort_values(ascending=False)
    return str(grouped.index[0]) if not grouped.empty else ""


def _empty_dashboard() -> dict:
    return {
        "total_orders": 0,
        "delivered_orders": 0,
        "cancelled_orders": 0,
        "rto_orders": 0,
        "unknown_orders": 0,
        "revenue_estimate": 0,
        "top_selling_sku": "",
        "worst_performing_sku": "",
        "ad_orders": 0,
        "natural_orders": 0,
        "order_source_breakdown": {},
    }
