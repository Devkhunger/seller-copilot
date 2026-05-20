from __future__ import annotations

import re
from io import BytesIO

import pandas as pd


CANONICAL_COLUMNS = [
    "order_date",
    "sku",
    "product_name",
    "customer_state",
    "status",
    "order_source",
    "listed_price",
    "discounted_price",
    "quantity",
]

ALIASES = {
    "order_date": ["order date", "order_date", "date", "purchase date", "created at"],
    "sku": ["sku", "product sku", "supplier sku", "style id", "product id"],
    "product_name": ["product name", "product", "item name", "listing title", "title"],
    "customer_state": ["customer state", "state", "shipping state", "ship state", "destination state"],
    "status": ["status", "order status", "delivery status", "reason for credit entry"],
    "order_source": ["order source", "source", "channel", "traffic source", "ad source"],
    "listed_price": [
        "listed price",
        "supplier listed price incl gst commission",
        "supplier listed price incl gst + commission",
        "mrp",
        "price",
    ],
    "discounted_price": [
        "discounted price",
        "supplier discounted price incl gst and commision",
        "supplier discounted price incl gst and commission",
        "selling price",
        "sale price",
        "amount",
    ],
    "quantity": ["quantity", "qty", "units", "item quantity"],
}


def clean_csv_upload(file_bytes: bytes) -> tuple[pd.DataFrame, list[str]]:
    raw = pd.read_csv(BytesIO(file_bytes))
    raw.columns = [str(col).strip() for col in raw.columns]
    column_map = _build_column_map(raw.columns)
    warnings: list[str] = []

    cleaned = pd.DataFrame()
    for column in CANONICAL_COLUMNS:
        source_column = column_map.get(column)
        if source_column:
            cleaned[column] = raw[source_column]
        else:
            warnings.append(f"Missing column: {column}")
            cleaned[column] = _default_for(column)

    cleaned["order_source"] = cleaned["order_source"].fillna("natural").replace("", "natural")
    cleaned["status"] = cleaned["status"].fillna("UNKNOWN").astype(str).str.upper().str.strip()
    cleaned["sku"] = cleaned["sku"].fillna("").astype(str).str.strip()
    cleaned["product_name"] = cleaned["product_name"].fillna(cleaned["sku"]).astype(str).str.strip()
    cleaned["customer_state"] = cleaned["customer_state"].fillna("Unknown").astype(str).str.title().str.strip()
    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce").dt.date.astype("string")
    cleaned["listed_price"] = _safe_money(cleaned["listed_price"])
    cleaned["discounted_price"] = _safe_money(cleaned["discounted_price"])
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce").fillna(1).clip(lower=1).astype(int)
    cleaned = cleaned[cleaned["sku"].astype(str).str.len() > 0].copy()
    return cleaned[CANONICAL_COLUMNS], warnings


def _build_column_map(columns) -> dict[str, str]:
    normalized = {_normalize(col): col for col in columns}
    result: dict[str, str] = {}
    for canonical, names in ALIASES.items():
        for name in names:
            normalized_name = _normalize(name)
            if normalized_name in normalized:
                result[canonical] = normalized[normalized_name]
                break
        if canonical not in result:
            for norm_col, original in normalized.items():
                if any(_normalize(name) in norm_col for name in names):
                    result[canonical] = original
                    break
    return result


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _default_for(column: str):
    defaults = {
        "order_source": "natural",
        "quantity": 1,
        "listed_price": 0,
        "discounted_price": 0,
        "customer_state": "Unknown",
        "status": "UNKNOWN",
    }
    return defaults.get(column, "")


def _safe_money(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(r"[^0-9.\\-]", "", regex=True),
        errors="coerce",
    ).fillna(0.0)

