from fastapi import APIRouter

from app.database import log_usage
from app.schemas import ListingDoctorRequest
from app.services.listing_generator import generate_listing

router = APIRouter(prefix="/api", tags=["listing"])


@router.post("/listing-doctor")
def listing_doctor(payload: ListingDoctorRequest):
    log_usage("listing_generated", payload.product_name)
    return generate_listing(payload)

