from fastapi import APIRouter

from app.database import log_usage
from app.schemas import InventoryUpdate
from app.services.inventory import inventory_report, upsert_inventory

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/inventory")
def get_inventory():
    return {"items": inventory_report()}


@router.post("/inventory")
def post_inventory(payload: InventoryUpdate):
    result = upsert_inventory(payload.sku, payload.current_stock)
    log_usage("inventory_updated", f"{payload.sku}: {payload.current_stock}")
    return result

