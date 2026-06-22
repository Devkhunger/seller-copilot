from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db, log_usage

router = APIRouter(prefix="/api", tags=["inventory"])


class InventoryPayload(BaseModel):
    sku: str
    current_stock: int


@router.get("/inventory")
def get_inventory(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT sku, current_stock, updated_at FROM inventory WHERE seller_email = ? ORDER BY sku ASC",
            (current_user["email"],),
        ).fetchall()
    return {"items": [dict(row) for row in rows]}


@router.post("/inventory")
def save_inventory(payload: InventoryPayload, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO inventory (seller_email, sku, current_stock)
            VALUES (?, ?, ?)
            ON CONFLICT(seller_email, sku) DO UPDATE SET current_stock = excluded.current_stock, updated_at = CURRENT_TIMESTAMP
            """,
            (current_user["email"], payload.sku, payload.current_stock),
        )
    log_usage("inventory_updated", payload.sku, current_user["email"])
    return {"ok": True}
