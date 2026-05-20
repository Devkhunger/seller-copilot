from dataclasses import dataclass


@dataclass
class OrderRow:
    order_date: str | None
    sku: str
    product_name: str
    customer_state: str
    status: str
    order_source: str
    listed_price: float
    discounted_price: float
    quantity: int

