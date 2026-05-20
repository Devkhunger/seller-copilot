from fastapi import APIRouter

from app.database import get_db

router = APIRouter(prefix="/api", tags=["usage"])


@router.get("/usage")
def get_usage():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM usage_logs ORDER BY id DESC LIMIT 100").fetchall()
    return {"items": [dict(row) for row in rows]}

