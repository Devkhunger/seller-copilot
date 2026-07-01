import re

FIELD_ALIASES = {
    "order_id": ("order_id", "sub_order_no", "amazon_order_id", "order_item_id"),
    "sku": ("sku", "seller_sku", "product_sku", "fsn"),
    "status": ("status", "order_status", "reason_for_credit_entry", "item_status"),
    "amount": ("amount", "selling_price", "supplier_listed_price", "item_total"),
    "payment_mode": ("payment_mode", "payment_type", "cod_or_prepaid"),
    "pincode": ("pincode", "customer_pincode", "ship_postal_code", "zip"),
}

def parse_currency(value) -> float:
    if value is None or value == "":
        return 0.0
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def _pick(row: dict, keys: tuple[str, ...]):
    lowered = {str(k).strip().lower().replace(" ", "_"): v for k, v in row.items()}
    for key in keys:
        if key in lowered and lowered[key] not in (None, ""):
            return lowered[key]
    return None

def normalize_order_row(row: dict) -> dict:
    raw_status = str(_pick(row, FIELD_ALIASES["status"]) or "unknown").strip().lower()
    payment = str(_pick(row, FIELD_ALIASES["payment_mode"]) or "prepaid").strip().lower()
    if "cod" in payment or "cash" in payment:
        payment = "cod"
    return {
        "order_id": str(_pick(row, FIELD_ALIASES["order_id"]) or "").strip(),
        "sku": str(_pick(row, FIELD_ALIASES["sku"]) or "").strip().upper(),
        "status": raw_status or "unknown",
        "amount": parse_currency(_pick(row, FIELD_ALIASES["amount"])),
        "payment_mode": payment,
        "pincode": str(_pick(row, FIELD_ALIASES["pincode"]) or "").strip(),
    }
