from fastapi import APIRouter, File, HTTPException, UploadFile

from app.database import get_db, log_usage
from app.services.csv_cleaner import clean_csv_upload
from app.services.recommender import today_actions

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    cleaned, warnings = clean_csv_upload(await file.read())
    if cleaned.empty:
        raise HTTPException(status_code=400, detail="No usable order rows found in this CSV.")

    with get_db() as conn:
        conn.execute("DELETE FROM order_rows")
        conn.execute("DELETE FROM actions WHERE done = 0")
        conn.executemany(
            """
            INSERT INTO order_rows (
                order_date, sku, product_name, customer_state, status, order_source,
                listed_price, discounted_price, quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            cleaned.where(cleaned.notna(), None).values.tolist(),
        )

    with get_db() as conn:
        for action in today_actions():
            conn.execute("INSERT INTO actions (text) VALUES (?)", (action,))

    log_usage("csv_upload", f"{file.filename}: {len(cleaned)} rows")
    return {"rows_imported": len(cleaned), "warnings": warnings}
