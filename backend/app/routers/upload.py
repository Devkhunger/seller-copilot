from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import get_current_user
from app.database import get_db, log_usage
from app.services.csv_cleaner import clean_csv_upload
from app.services.recommender import today_actions

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    cleaned, warnings = clean_csv_upload(await file.read())
    if cleaned.empty:
        raise HTTPException(status_code=400, detail="No usable order rows found in this CSV.")

    seller_email = current_user["email"]

    with get_db() as conn:
        conn.execute("DELETE FROM actions WHERE seller_email = ? AND done = 0", (seller_email,))
        rows = cleaned.copy()
        rows.insert(0, "seller_email", seller_email)
        conn.executemany(
            """
            INSERT INTO order_rows (
                seller_email, order_date, sku, product_name, customer_state, status, order_source,
                listed_price, discounted_price, quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows.where(rows.notna(), None).values.tolist(),
        )

    with get_db() as conn:
        for action in today_actions(seller_email):
            conn.execute(
                "INSERT INTO actions (seller_email, text) VALUES (?, ?)",
                (seller_email, action),
            )

    log_usage("csv_upload", f"{file.filename}: {len(cleaned)} rows", seller_email)
    return {"rows_imported": len(cleaned), "warnings": warnings}
