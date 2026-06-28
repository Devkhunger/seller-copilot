import re

def parse_currency(value) -> float:
    if value is None or value == "":
        return 0.0
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def normalize_order_row(row: dict) -> dict:
    raw_status = str(row.get("status") or "unknown").strip().lower()
    return {
        "order_id": str(row.get("order_id") or "").strip(),
        "sku": str(row.get("sku") or "").strip().upper(),
        "status": raw_status or "unknown",
        "amount": parse_currency(row.get("amount")),
        "payment_mode": str(row.get("payment_mode") or "prepaid").strip().lower(),
        "pincode": str(row.get("pincode") or "").strip(),
    }
