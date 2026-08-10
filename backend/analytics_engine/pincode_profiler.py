from collections import defaultdict

def profile_pincodes(orders: list[dict], min_orders: int = 5) -> dict[str, dict]:
    stats = defaultdict(lambda: {"total": 0, "rto": 0})
    for o in orders:
        pin = str(o.get("pincode") or "").strip()
        if not pin:
            continue
        stats[pin]["total"] += 1
        if str(o.get("status", "")).lower() in ("rto", "returned_to_origin"):
            stats[pin]["rto"] += 1
    return {
        pin: {**s, "rto_rate": round(s["rto"] / s["total"], 4)}
        for pin, s in stats.items()
        if s["total"] >= min_orders
    }

def flagged_cod_pincodes(orders: list[dict], min_orders: int = 5, threshold: float = 0.35) -> list[str]:
    profiles = profile_pincodes(orders, min_orders=min_orders)
    return sorted(pin for pin, info in profiles.items() if info["rto_rate"] >= threshold)
