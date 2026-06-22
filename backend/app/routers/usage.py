from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api", tags=["usage"])


@router.get("/usage")
def get_usage(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, event_type, detail, created_at
            FROM usage_logs
            WHERE seller_email = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (current_user["email"],),
        ).fetchall()
    return {"items": [dict(row) for row in rows]}
