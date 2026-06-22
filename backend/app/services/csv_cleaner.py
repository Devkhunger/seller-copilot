from __future__ import annotations

import re
from io import BytesIO

import pandas as pd

CANONICAL_COLUMNS = (
    "order_date",
    "sku",
    "product_name",
    "customer_state",
    "status",
    "order_source",
    "listed_price",
    "discounted_price",
    "quantity",
)

ALIASES = {
    "order_date": ["order date", "date", "created date", "invoice date"],
    "sku": ["sku", "product sku", "item sku", "merchant sku"],
    "product_name": ["product name", "product", "item name", "title"],
    "customer_state": ["customer state", "state", "shipping state", "delivery state"],
    "status": ["status", "order status", "fulfillment status"],
    "order_source": ["order source", "source", "marketplace", "platform"],
    "listed_price": ["listed price", "mrp", "price", "original price", "selling price"],
    "discounted_price": ["discounted price", "sale price", "final price", "discount price"],
    "quantity": ["quantity", "qty", "units"],
}


def clean_csv_upload(file_bytes: bytes) -> tuple[pd.DataFrame, list[str]]:
    raw = pd.read_csv(BytesIO(file_bytes))
    raw.columns = [str(col).strip() for col in raw.columns]

    column_map = _build_column_map(raw.columns)
    warnings: list[str] = []
    cleaned = pd.DataFrame()

    for column in CANONICAL_COLUMNS:
        source_column = column_map.get(column)
        if source_column and source_column in raw.columns:
            cleaned[column] = raw[source_column]
            continue

        warnings.append(f"Missing column: {column}")
        cleaned[column] = _default_for(column)

    cleaned["order_date"] = pd.to_datetime(cleaned["order_date"], errors="coerce").dt.date
    cleaned["sku"] = cleaned["sku"].fillna("").astype(str).str.strip()
    cleaned["product_name"] = cleaned["product_name"].fillna("").astype(str).str.strip()
    cleaned["customer_state"] = cleaned["customer_state"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    cleaned["status"] = cleaned["status"].fillna("UNKNOWN").astype(str).str.strip().replace("", "UNKNOWN").str.upper()
    cleaned["order_source"] = cleaned["order_source"].fillna("natural").astype(str).str.strip().replace("", "natural")
    cleaned["listed_price"] = _safe_money(cleaned["listed_price"])
    cleaned["discounted_price"] = _safe_money(cleaned["discounted_price"])
    cleaned["quantity"] = pd.to_numeric(cleaned["quantity"], errors="coerce").fillna(1).clip(lower=1).astype(int)

    cleaned = cleaned.sort_values(by=["order_date"], kind="mergesort", na_position="last").reset_index(drop=True)
    return cleaned, warnings


def _build_column_map(columns: list[str]) -> dict[str, str]:
    normalized = {_normalize(column): column for column in columns}
    result: dict[str, str] = {}

    for canonical, aliases in ALIASES.items():
        candidates = [canonical, *aliases]
        for name in candidates:
            normalized_name = _normalize(name)
            if normalized_name in normalized:
                result[canonical] = normalized[normalized_name]
                break

    for canonical in CANONICAL_COLUMNS:
        if canonical in result:
            continue
        normalized_name = _normalize(canonical)
        if normalized_name in normalized:
            result[canonical] = normalized[normalized_name]

    return result


def _normalize(value) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _default_for(column: str):
    defaults = {
        "order_source": "natural",
        "quantity": 1,
        "listed_price": 0.0,
        "discounted_price": 0.0,
        "customer_state": "Unknown",
        "status": "UNKNOWN",
        "order_date": None,
        "sku": "",
        "product_name": "",
    }
    return defaults.get(column, "")


def _safe_money(series: pd.Series) -> pd.Series:
    values = (
        pd.to_numeric(
            series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True),
            errors="coerce",
        )
        .fillna(0.0)
    )
    return values
