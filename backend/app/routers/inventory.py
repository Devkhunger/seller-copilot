from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.schemas import InventoryUpdate
from app.services.inventory import inventory_report, upsert_inventory

router = APIRouter(prefix="/api", tags=["inventory"])


@router.get("/inventory")
def get_inventory(current_user: dict = Depends(get_current_user)):
    return {"items": inventory_report(current_user["email"])}


@router.post("/inventory")
def save_inventory(payload: InventoryUpdate, current_user: dict = Depends(get_current_user)):
    return upsert_inventory(payload.sku, payload.current_stock, current_user["email"])
