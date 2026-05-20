from pydantic import BaseModel, Field


class ListingDoctorRequest(BaseModel):
    product_name: str
    fabric: str = ""
    color: str = ""
    size: str = ""
    design: str = ""
    platform: str = Field(default="Meesho")


class InventoryUpdate(BaseModel):
    sku: str
    current_stock: int = Field(ge=0)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class ProfitSettingsUpdate(BaseModel):
    product_cost_percent: float | None = Field(default=None, ge=0)
    marketplace_fee_percent: float | None = Field(default=None, ge=0)
    forward_shipping_per_order: float | None = Field(default=None, ge=0)
    return_shipping_per_order: float | None = Field(default=None, ge=0)
    ad_cost_percent: float | None = Field(default=None, ge=0)
