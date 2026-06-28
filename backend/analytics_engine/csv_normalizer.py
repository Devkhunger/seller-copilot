def normalize_order_row(row: dict) -> dict:
    return {
        "order_id": str(row.get("order_id", "")).strip(),
        "sku": str(row.get("sku", "")).strip().upper(),
        "status": str(row.get("status", "unknown")).strip().lower(),
        "amount": float(row.get("amount", 0) or 0),
        "payment_mode": str(row.get("payment_mode", "prepaid")).strip().lower(),
    }
