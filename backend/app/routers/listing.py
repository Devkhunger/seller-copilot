from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database import log_usage
from app.schemas import ListingDoctorRequest
from app.services.listing_generator import generate_listing

router = APIRouter(prefix="/api", tags=["listing"])


@router.post("/listing-doctor")
def listing_doctor(payload: ListingDoctorRequest, current_user: dict = Depends(get_current_user)):
    seller_email = current_user["email"]
    log_usage("listing_generated", payload.product_name, seller_email)
    return generate_listing(payload)
