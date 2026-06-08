from __future__ import annotations

import math

import pandas as pd

from app.services.analytics import load_orders_df, status_mask

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, precision_score, r2_score, recall_score
    from sklearn.preprocessing import OneHotEncoder
except Exception:  # pragma: no cover - keeps local MVP usable without sklearn installed.
    RandomForestClassifier = None
    RandomForestRegressor = None
    accuracy_score = None
    f1_score = None
    mean_absolute_error = None
    precision_score = None
    r2_score = None
    recall_score = None
    OneHotEncoder = None


MIN_ROWS_FOR_RTO_MODEL = 30
MIN_DAILY_ROWS_FOR_DEMAND_MODEL = 14
FORECAST_DAYS = 14
MIN_WATCHLIST_ORDERS = 3


def ml_business_insights() -> dict:
    df = load_orders_df()
    if df.empty:
        return {
            "engine": _engine_status(),
            "demand_forecast": [],
            "rto_predictions": [],
            "profit_opportunities": [],
            "model_notes": ["Upload order data to prepare a growth plan."],
        }

    demand = demand_forecast(df)
    rto = rto_predictions(df)
    opportunities = profit_opportunities(df, demand, rto)
    notes = [*demand["notes"], *rto["notes"]]

    return {
        "engine": _engine_status(),
        "demand_forecast": demand["items"][:25],
        "rto_predictions": rto["items"],
        "profit_opportunities": opportunities,
        "model_notes": notes,
        "quality": {
            "sales_plan": demand.get("quality", {}),
            "return_risk": rto.get("quality", {}),
        },
    }


def demand_forecast(df: pd.DataFrame | None = None) -> dict:
    df = load_orders_df() if df is None else df
    if df.empty:
        return {"items": [], "notes": ["No orders found for sales planning."], "quality": {}}

    daily = _daily_sku_orders(df)
    if daily.empty:
        return {"items": [], "notes": ["Order dates are missing, so sales planning cannot run yet."], "quality": {}}

    if RandomForestRegressor is None:
        return {
            "items": _fallback_demand_forecast(daily),
            "notes": ["Using basic sales average because the advanced planner is not installed."],
            "quality": {"method": "Basic average"},
        }

    if len(daily) < MIN_DAILY_ROWS_FOR_DEMAND_MODEL:
        return {
            "items": _fallback_demand_forecast(daily),
            "notes": [f"Need at least {MIN_DAILY_ROWS_FOR_DEMAND_MODEL} SKU-day rows for a stronger sales plan."],
            "quality": {"method": "Basic average"},
        }

    feature_cols = [
        "sku",
        "day_of_week",
        "day_of_month",
        "month",
        "quarter",
        "week_of_year",
        "days_to_month_end",
        "sale_context",
        "sale_intensity",
        "is_festive_season",
        "is_peak_sale_season",
        "source_paid_share",
        "natural_share",
        "avg_price",
        "avg_discount_pct",
        "days_since_last_order",
        "orders_lag_1",
        "orders_lag_7",
        "rolling_7_orders",
        "rolling_14_orders",
        "sku_total_orders",
        "sku_active_days",
    ]
    train_df, test_df = _time_train_test_split(daily, "order_day")
    quality = {}

    if not test_df.empty and train_df["quantity"].nunique() > 1:
        eval_encoder, x_train = _encode_features(train_df, feature_cols)
        x_test = eval_encoder.transform(test_df[feature_cols])
        eval_model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=2)
        eval_model.fit(x_train, train_df["quantity"].astype(float))
        predictions = eval_model.predict(x_test).clip(min=0)
        quality = {
            "method": "Advanced sales planner",
            "test_rows": int(len(test_df)),
            "avg_error_orders": round(float(mean_absolute_error(test_df["quantity"], predictions)), 2),
            "r2": round(float(r2_score(test_df["quantity"], predictions)), 3),
        }

    encoder, encoded_features = _encode_features(daily, feature_cols)
    model = RandomForestRegressor(n_estimators=120, random_state=42, min_samples_leaf=2)
    model.fit(encoded_features, daily["quantity"].astype(float))

    future = _future_sku_days(daily)
    future_encoded = encoder.transform(future[feature_cols])
    future["prediction"] = model.predict(future_encoded).clip(min=0)

    items = []
    for sku, group in future.groupby("sku"):
        forecast_units = float(group["prediction"].sum())
        sku_daily = daily[daily["sku"] == sku]
        historical_daily = float(sku_daily["quantity"].mean())
        items.append(
            {
                "sku": sku,
                "model": "advanced_sales_planner",
                "forecast_days": FORECAST_DAYS,
                "forecast_units": round(forecast_units, 1),
                "avg_daily_forecast": round(forecast_units / FORECAST_DAYS, 2),
                "historical_avg_daily": round(historical_daily, 2),
                "trend": _trend_label(forecast_units / FORECAST_DAYS, historical_daily),
                "confidence": _confidence_from_rows(len(sku_daily)),
                "avg_error_orders": quality.get("avg_error_orders"),
            }
        )

    return {
        "items": sorted(items, key=lambda item: item["forecast_units"], reverse=True),
        "notes": ["Sales plan now uses recent sales speed, weekday, price, ad-share, discount, freshness, festive-season, and sale-context signals."],
        "quality": quality,
    }


def rto_predictions(df: pd.DataFrame | None = None) -> dict:
    df = load_orders_df() if df is None else df
    if df.empty:
        return {"items": [], "notes": ["No orders found for return-risk planning."], "quality": {}}

    model_df = _rto_training_rows(df)
    if model_df.empty:
        return {"items": [], "notes": ["No valid return-risk rows found."], "quality": {}}

    if RandomForestClassifier is None:
        return {
            "items": _fallback_rto_predictions(model_df),
            "notes": ["Using historical return rate because the advanced planner is not installed."],
            "quality": {"method": "Historical return rate"},
        }

    if len(model_df) < MIN_ROWS_FOR_RTO_MODEL or model_df["is_rto"].nunique() < 2:
        return {
            "items": _fallback_rto_predictions(model_df),
            "notes": [f"Need at least {MIN_ROWS_FOR_RTO_MODEL} rows with returned and delivered orders for stronger return-risk planning."],
            "quality": {"method": "Historical return rate"},
        }

    feature_cols = [
        "sku",
        "customer_state",
        "order_source",
        "price",
        "quantity",
        "discount_pct",
        "sku_order_count",
        "state_order_count",
        "sku_historical_rto_rate",
        "state_historical_rto_rate",
        "sku_state_historical_rto_rate",
        "is_paid_source",
    ]
    train_df, test_df = _time_train_test_split(model_df, "order_date")
    quality = {}
    alert_threshold = 0.55

    if not test_df.empty and train_df["is_rto"].nunique() > 1 and test_df["is_rto"].nunique() > 1:
        eval_encoder, x_train = _encode_features(train_df, feature_cols)
        x_test = eval_encoder.transform(test_df[feature_cols])
        eval_model = RandomForestClassifier(n_estimators=120, random_state=42, min_samples_leaf=4, class_weight="balanced_subsample")
        eval_model.fit(x_train, train_df["is_rto"].astype(int))
        probabilities = eval_model.predict_proba(x_test)[:, 1]
        alert_threshold, metrics = _best_alert_threshold(test_df["is_rto"].astype(int), probabilities)
        quality = {"method": "Advanced return planner", "test_rows": int(len(test_df)), "alert_cutoff": round(alert_threshold * 100, 1), **metrics}

    encoder, encoded_features = _encode_features(model_df, feature_cols)
    model = RandomForestClassifier(n_estimators=140, random_state=42, min_samples_leaf=4, class_weight="balanced_subsample")
    model.fit(encoded_features, model_df["is_rto"].astype(int))
    model_df["rto_probability"] = model.predict_proba(encoded_features)[:, 1]

    items = []
    for (sku, state), group in model_df.groupby(["sku", "customer_state"]):
        orders = int(group["quantity"].sum())
        row_count = len(group)
        probability = float(group["rto_probability"].mean())
        historical_rate = float(group["is_rto"].mean())
        if row_count < MIN_WATCHLIST_ORDERS:
            continue
        items.append(
            {
                "sku": sku,
                "customer_state": state,
                "model": "advanced_return_planner",
                "orders": orders,
                "rto_probability": round(probability * 100, 1),
                "historical_rto_rate": round(historical_rate * 100, 1),
                "risk_label": _probability_label(probability, alert_threshold),
                "confidence": _confidence_from_rows(row_count),
                "accuracy": quality.get("accuracy"),
                "precision": quality.get("precision"),
                "recall": quality.get("recall"),
                "alert_cutoff": quality.get("alert_cutoff"),
            }
        )

    high_first = sorted(items, key=lambda item: (item["risk_label"] != "High Risk", -item["rto_probability"], -item["orders"]))
    return {
        "items": high_first[:15],
        "notes": ["Return risk now uses past SKU, state, price, discount, and ad-source signals with a stricter alert cutoff."],
        "quality": quality,
    }


def profit_opportunities(df: pd.DataFrame, demand: dict, rto: dict) -> list[dict]:
    delivered = df[status_mask(df, "delivered")].copy()
    if delivered.empty:
        return []

    demand_by_sku = {item["sku"]: item for item in demand.get("items", [])}
    rto_by_sku = {}
    for item in rto.get("items", []):
        rto_by_sku.setdefault(item["sku"], []).append(item["rto_probability"])

    rows = []
    for sku, group in df.groupby("sku"):
        sku_delivered = group[status_mask(group, "delivered")]
        revenue = float((sku_delivered["discounted_price"] * sku_delivered["quantity"]).sum())
        orders = int(group["quantity"].sum())
        avg_price = float(group["discounted_price"].replace(0, pd.NA).dropna().mean() or 0)
        forecast = demand_by_sku.get(sku, {})
        rto_probability = sum(rto_by_sku.get(sku, [])) / max(len(rto_by_sku.get(sku, [])), 1)
        opportunity_score = (
            min(float(forecast.get("forecast_units", 0)), 50) * 1.6
            + min(revenue / 1000, 30)
            + max(0, 25 - rto_probability)
            + min(orders, 20) * 0.5
        )
        rows.append(
            {
                "sku": sku,
                "orders": orders,
                "revenue": round(revenue, 2),
                "avg_price": round(avg_price, 2),
                "forecast_units": forecast.get("forecast_units", 0),
                "rto_probability": round(rto_probability, 1),
                "opportunity_score": round(max(0, min(100, opportunity_score)), 1),
                "decision": _opportunity_decision(opportunity_score, rto_probability),
            }
        )
    return sorted(rows, key=lambda item: item["opportunity_score"], reverse=True)[:10]


def _engine_status() -> dict:
    return {
        "sklearn_available": RandomForestClassifier is not None,
        "models": ["sales_planner", "return_planner"] if RandomForestClassifier is not None else [],
    }


def _sale_context_for_day(day: pd.Timestamp) -> tuple[str, float, int, int]:
    month = int(day.month)
    day_of_month = int(day.day)
    if month in [10, 11] or (month == 12 and day_of_month >= 15) or month == 1:
        return "platform_sale", 1.0, 1, 1
    if month in [8, 9]:
        return "festive_preheat", 0.7, 1, 0
    if month in [2, 3, 4, 5, 6, 7]:
        return "normal", 0.0, 0, 0
    return "normal", 0.0, 0, 0


def _daily_sku_orders(df: pd.DataFrame) -> pd.DataFrame:
    work = df.dropna(subset=["order_date"]).copy()
    if work.empty:
        return pd.DataFrame()
    work["order_day"] = work["order_date"].dt.floor("D")
    work["is_paid"] = work["order_source"].fillna("").astype(str).str.lower().str.contains("ad|paid|sponsored", na=False).astype(float)
    work["discount_pct"] = work.apply(_discount_pct, axis=1)
    grouped = work.groupby(["sku", "order_day"]).agg(
        quantity=("quantity", "sum"),
        source_paid_share=("is_paid", "mean"),
        avg_price=("discounted_price", "mean"),
        avg_discount_pct=("discount_pct", "mean"),
    ).reset_index()
    grouped = grouped.sort_values(["sku", "order_day"])
    grouped["day_of_week"] = grouped["order_day"].dt.dayofweek
    grouped["day_of_month"] = grouped["order_day"].dt.day
    grouped["month"] = grouped["order_day"].dt.month
    grouped["quarter"] = grouped["order_day"].dt.quarter
    grouped["week_of_year"] = grouped["order_day"].dt.isocalendar().week.astype(int)
    grouped["days_to_month_end"] = (grouped["order_day"].dt.days_in_month - grouped["day_of_month"]).astype(int)
    sale_context = grouped["order_day"].apply(_sale_context_for_day)
    grouped["sale_context"] = sale_context.apply(lambda item: item[0])
    grouped["sale_intensity"] = sale_context.apply(lambda item: float(item[1]))
    grouped["is_festive_season"] = sale_context.apply(lambda item: int(item[2]))
    grouped["is_peak_sale_season"] = sale_context.apply(lambda item: int(item[3]))
    grouped["avg_price"] = grouped["avg_price"].fillna(0)
    grouped["avg_discount_pct"] = grouped["avg_discount_pct"].fillna(0)
    grouped["natural_share"] = (1 - grouped["source_paid_share"]).clip(lower=0, upper=1)
    grouped["orders_lag_1"] = grouped.groupby("sku")["quantity"].shift(1).fillna(0)
    grouped["orders_lag_7"] = grouped.groupby("sku")["quantity"].shift(7).fillna(0)
    grouped["rolling_7_orders"] = grouped.groupby("sku")["quantity"].transform(lambda item: item.shift(1).rolling(7, min_periods=1).mean()).fillna(0)
    grouped["rolling_14_orders"] = grouped.groupby("sku")["quantity"].transform(lambda item: item.shift(1).rolling(14, min_periods=1).mean()).fillna(0)
    grouped["sku_total_orders"] = grouped.groupby("sku")["quantity"].transform("sum")
    grouped["sku_active_days"] = grouped.groupby("sku")["order_day"].transform("count")
    grouped["days_since_last_order"] = grouped.groupby("sku")["order_day"].diff().dt.days.fillna(0)
    return grouped


def _future_sku_days(daily: pd.DataFrame) -> pd.DataFrame:
    latest_day = daily["order_day"].max()
    rows = []
    for sku, group in daily.groupby("sku"):
        group = group.sort_values("order_day")
        paid_share = _safe_mean(group["source_paid_share"].tail(7), default=0.0)
        avg_price = _safe_mean(group["avg_price"].replace(0, pd.NA).dropna().tail(7), default=_safe_mean(group["avg_price"], default=0.0))
        avg_discount_pct = _safe_mean(group["avg_discount_pct"].tail(7), default=0.0)
        lag_1 = float(group["quantity"].iloc[-1])
        lag_7 = float(group["quantity"].iloc[-7]) if len(group) >= 7 else 0
        rolling_7 = float(group["quantity"].tail(7).mean())
        rolling_14 = float(group["quantity"].tail(14).mean())
        sku_total_orders = float(group["quantity"].sum())
        sku_active_days = int(len(group))
        natural_share = max(0.0, 1.0 - paid_share)
        days_since_last_order = float((latest_day - group["order_day"].iloc[-1]).days) if len(group) else 0
        for offset in range(1, FORECAST_DAYS + 1):
            day = latest_day + pd.Timedelta(days=offset)
            rows.append(
                {
                    "sku": sku,
                    "order_day": day,
                    "day_of_week": day.dayofweek,
                    "day_of_month": day.day,
                    "month": day.month,
                    "quarter": day.quarter,
                    "week_of_year": int(day.isocalendar().week),
                    "days_to_month_end": day.days_in_month - day.day,
                    "sale_context": _sale_context_for_day(day)[0],
                    "sale_intensity": _sale_context_for_day(day)[1],
                    "is_festive_season": _sale_context_for_day(day)[2],
                    "is_peak_sale_season": _sale_context_for_day(day)[3],
                    "source_paid_share": paid_share,
                    "natural_share": natural_share,
                    "avg_price": avg_price,
                    "avg_discount_pct": avg_discount_pct,
                    "days_since_last_order": days_since_last_order,
                    "orders_lag_1": lag_1,
                    "orders_lag_7": lag_7,
                    "rolling_7_orders": rolling_7,
                    "rolling_14_orders": rolling_14,
                    "sku_total_orders": sku_total_orders,
                    "sku_active_days": sku_active_days,
                }
            )
    return pd.DataFrame(rows)


def _rto_training_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = df.copy()
    rows["order_date"] = pd.to_datetime(rows["order_date"], errors="coerce")
    rows["sku"] = rows["sku"].fillna("").astype(str).str.strip()
    rows["customer_state"] = rows["customer_state"].fillna("").astype(str).str.strip()
    rows["order_source"] = rows["order_source"].fillna("").astype(str).str.strip()
    rows = rows.sort_values(["order_date", "sku", "customer_state", "order_source"], kind="mergesort", na_position="last").reset_index(drop=True)
    rows["price"] = rows["discounted_price"].fillna(0)
    rows["discount_pct"] = rows.apply(_discount_pct, axis=1)
    rows["is_rto"] = status_mask(rows, "rto").astype(int)
    rows["is_paid_source"] = rows["order_source"].astype(str).str.lower().str.contains("ad|paid|sponsored", na=False).astype(int)

    rows["sku_order_count"] = rows.groupby("sku").cumcount()
    rows["state_order_count"] = rows.groupby("customer_state").cumcount()
    rows["combo_order_count"] = rows.groupby(["sku", "customer_state"]).cumcount()
    rows["global_order_count"] = pd.Series(range(len(rows)), index=rows.index, dtype="float")

    rows["global_prior_rto_count"] = rows["is_rto"].cumsum().shift(1).fillna(0)
    rows["sku_prior_rto_count"] = rows.groupby("sku")["is_rto"].transform(lambda series: series.cumsum().shift(1).fillna(0))
    rows["state_prior_rto_count"] = rows.groupby("customer_state")["is_rto"].transform(lambda series: series.cumsum().shift(1).fillna(0))
    rows["combo_prior_rto_count"] = rows.groupby(["sku", "customer_state"])["is_rto"].transform(lambda series: series.cumsum().shift(1).fillna(0))

    prior_global_rate = rows["global_prior_rto_count"] / rows["global_order_count"].replace(0, pd.NA)
    rows["sku_historical_rto_rate"] = (rows["sku_prior_rto_count"] / rows["sku_order_count"].replace(0, pd.NA)).fillna(prior_global_rate).fillna(0.0)
    rows["state_historical_rto_rate"] = (rows["state_prior_rto_count"] / rows["state_order_count"].replace(0, pd.NA)).fillna(prior_global_rate).fillna(0.0)
    rows["sku_state_historical_rto_rate"] = (rows["combo_prior_rto_count"] / rows["combo_order_count"].replace(0, pd.NA)).fillna(prior_global_rate).fillna(0.0)
    columns = [
        "order_date",
        "sku",
        "customer_state",
        "order_source",
        "price",
        "quantity",
        "discount_pct",
        "sku_order_count",
        "state_order_count",
        "sku_historical_rto_rate",
        "state_historical_rto_rate",
        "sku_state_historical_rto_rate",
        "is_paid_source",
        "is_rto",
    ]
    return rows[columns]


def _time_train_test_split(df: pd.DataFrame, date_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    dated = df.dropna(subset=[date_col]).sort_values(date_col).copy()
    if len(dated) < 40:
        return dated, pd.DataFrame(columns=dated.columns)
    split_index = max(1, int(len(dated) * 0.75))
    return dated.iloc[:split_index].copy(), dated.iloc[split_index:].copy()


def _best_alert_threshold(y_true, probabilities) -> tuple[float, dict]:
    best = {"threshold": 0.55, "f1": -1, "precision": 0, "recall": 0, "accuracy": 0}
    for threshold in [item / 100 for item in range(35, 91, 5)]:
        prediction = (probabilities >= threshold).astype(int)
        precision = float(precision_score(y_true, prediction, zero_division=0))
        recall = float(recall_score(y_true, prediction, zero_division=0))
        f1 = float(f1_score(y_true, prediction, zero_division=0))
        accuracy = float(accuracy_score(y_true, prediction))
        if precision < 0.08 and threshold < 0.7:
            continue
        if f1 > best["f1"] or (f1 == best["f1"] and precision > best["precision"]):
            best = {"threshold": threshold, "f1": f1, "precision": precision, "recall": recall, "accuracy": accuracy}
    return best["threshold"], {
        "accuracy": round(best["accuracy"] * 100, 2),
        "precision": round(best["precision"] * 100, 2),
        "recall": round(best["recall"] * 100, 2),
        "f1": round(best["f1"] * 100, 2),
    }


def _encode_features(df: pd.DataFrame, feature_cols: list[str]):
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    encoded = encoder.fit_transform(df[feature_cols])
    return encoder, encoded


def _safe_mean(series, default: float = 0.0) -> float:
    value = series.mean() if hasattr(series, "mean") else default
    return float(default if pd.isna(value) else value)


def _discount_pct(row) -> float:
    listed = float(row.get("listed_price") or 0)
    discounted = float(row.get("discounted_price") or 0)
    if listed <= 0:
        return 0
    return max(0, min(100, ((listed - discounted) / listed) * 100))


def _fallback_demand_forecast(daily: pd.DataFrame) -> list[dict]:
    items = []
    for sku, group in daily.groupby("sku"):
        recent = float(group.sort_values("order_day").tail(7)["quantity"].mean())
        all_time = float(group["quantity"].mean())
        avg_daily = recent if not math.isnan(recent) else all_time
        items.append(
            {
                "sku": sku,
                "model": "basic_average",
                "forecast_days": FORECAST_DAYS,
                "forecast_units": round(avg_daily * FORECAST_DAYS, 1),
                "avg_daily_forecast": round(avg_daily, 2),
                "historical_avg_daily": round(all_time, 2),
                "trend": _trend_label(avg_daily, all_time),
                "confidence": _confidence_from_rows(len(group)),
                "avg_error_orders": None,
            }
        )
    return sorted(items, key=lambda item: item["forecast_units"], reverse=True)


def _fallback_rto_predictions(df: pd.DataFrame) -> list[dict]:
    items = []
    for (sku, state), group in df.groupby(["sku", "customer_state"]):
        row_count = len(group)
        probability = float(group["is_rto"].mean())
        if row_count < MIN_WATCHLIST_ORDERS and probability < 0.3:
            continue
        items.append(
            {
                "sku": sku,
                "customer_state": state,
                "model": "historical_return_rate",
                "orders": int(group["quantity"].sum()),
                "rto_probability": round(probability * 100, 1),
                "historical_rto_rate": round(probability * 100, 1),
                "risk_label": _probability_label(probability, 0.3),
                "confidence": _confidence_from_rows(row_count),
                "accuracy": None,
                "precision": None,
                "recall": None,
                "alert_cutoff": 30,
            }
        )
    return sorted(items, key=lambda item: item["rto_probability"], reverse=True)[:15]


def _trend_label(predicted_daily: float, historical_daily: float) -> str:
    if historical_daily <= 0:
        return "New Demand"
    change = (predicted_daily - historical_daily) / historical_daily
    if change >= 0.15:
        return "Growing"
    if change <= -0.15:
        return "Cooling"
    return "Stable"


def _probability_label(probability: float, high_threshold: float = 0.3) -> str:
    if probability >= high_threshold:
        return "High Risk"
    if probability >= max(0.15, high_threshold * 0.55):
        return "Medium Risk"
    return "Low Risk"


def _confidence_from_rows(rows: int) -> str:
    if rows >= 50:
        return "High"
    if rows >= 15:
        return "Medium"
    return "Low"


def _opportunity_decision(score: float, rto_probability: float) -> str:
    if rto_probability >= 30:
        return "Fix RTO Before Scaling"
    if score >= 70:
        return "Scale Ads and Stock"
    if score >= 45:
        return "Test Carefully"
    return "Keep Watching"
