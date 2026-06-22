from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import log_usage
from app.services.listing_generator import generate_listing

router = APIRouter(prefix="/api", tags=["listing"])


class ListingPayload(BaseModel):
    product_name: str
    fabric: str = ""
    color: str = ""
    size: str = ""
    design: str = ""
    platform: str = "Meesho"


@router.post("/listing-doctor")
def listing_doctor(payload: ListingPayload, current_user: dict = Depends(get_current_user)):
    log_usage("listing_doctor_used", payload.product_name, current_user["email"])
    return generate_listing(payload)
