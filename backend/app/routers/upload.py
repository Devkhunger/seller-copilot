from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

import pandas as pd

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.services.csv_cleaner import clean_csv_upload

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please upload a CSV file.")

    cleaned, warnings = clean_csv_upload(await file.read())
    if cleaned.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No usable order rows found in this CSV.")

    order_dates = cleaned["order_date"].dropna()
    if not order_dates.empty:
        new_start = order_dates.min().isoformat()
        new_end = order_dates.max().isoformat()
        overlap = _find_date_overlap(current_user["email"], new_start, new_end)
        if overlap:
            overlap_start, overlap_end, existing_count = overlap
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This upload overlaps with orders already stored for this seller. "
                    f"Existing data covers {overlap_start} to {overlap_end}; {existing_count} overlapping rows were found."
                ),
            )

    seller_email = current_user["email"]
    with get_db() as conn:
        conn.execute("DELETE FROM actions WHERE seller_email = ? AND done = 0", (seller_email,))
        rows = cleaned.where(cleaned.notna(), None).copy()
        rows["order_date"] = rows["order_date"].apply(_serialize_date)
        payload = rows[
            [
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
        ].values.tolist()
        conn.executemany(
            """
            INSERT INTO order_rows (
                seller_email, order_date, sku, product_name, customer_state, status, order_source,
                listed_price, discounted_price, quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(seller_email, *row) for row in payload],
        )

    action = "Review the uploaded orders in the dashboard."
    with get_db() as conn:
        conn.execute("INSERT INTO actions (seller_email, text) VALUES (?, ?)", (seller_email, action))

    log_usage("csv_upload", f"{len(cleaned)} rows", seller_email)
    return {
        "rows_imported": len(cleaned),
        "warnings": warnings,
        "action": action,
    }


def _find_date_overlap(seller_email: str, new_start: str, new_end: str):
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT
                MIN(date(order_date)) AS min_date,
                MAX(date(order_date)) AS max_date,
                COUNT(*) AS row_count
            FROM order_rows
            WHERE seller_email = ?
              AND order_date IS NOT NULL
              AND order_date != ''
              AND date(order_date) IS NOT NULL
              AND date(order_date) BETWEEN date(?) AND date(?)
            """,
            (seller_email, new_start, new_end),
        ).fetchone()

    if not row or not row["row_count"]:
        return None
    return row["min_date"], row["max_date"], int(row["row_count"])


def _serialize_date(value):
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
