from .inventory_alerts import needs_reorder

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def generate_daily_checklist(sku_metrics: list[dict], high_rto_pincodes: list[str] | None = None) -> list[dict]:
    actions = []
    seen = set()
    for item in sku_metrics:
        sku = item.get("sku", "UNKNOWN")
        rto_rate = float(item.get("rto_rate", 0.0))
        margin_pct = float(item.get("margin_pct", 0.0))
        monthly_rev = float(item.get("monthly_revenue", 0.0))
        if rto_rate >= 0.30 and (sku, "rto") not in seen:
            seen.add((sku, "rto"))
            est_savings = round(monthly_rev * max(0.0, rto_rate - 0.15) * 0.25, 2)
            actions.append({
                "sku": sku,
                "category": "rto",
                "priority": "critical" if rto_rate >= 0.45 else "high",
                "estimated_impact_inr": est_savings,
                "action": f"Review COD eligibility for {sku} (RTO {rto_rate * 100:.1f}%)",
            })
        if margin_pct < 8.0 and (sku, "margin") not in seen:
            seen.add((sku, "margin"))
            est_gain = round(monthly_rev * max(0.0, (8.0 - margin_pct) / 100.0), 2)
            actions.append({
                "sku": sku,
                "category": "margin",
                "priority": "high" if margin_pct < 0 else "medium",
                "estimated_impact_inr": est_gain,
                "action": f"Reprice {sku} to restore net margin above 8%",
            })
        if "stock_on_hand" in item and "avg_daily_units" in item:
            if needs_reorder(item["stock_on_hand"], item["avg_daily_units"]) and (sku, "stock") not in seen:
                seen.add((sku, "stock"))
                actions.append({
                    "sku": sku,
                    "category": "inventory",
                    "priority": "high",
                    "estimated_impact_inr": round(monthly_rev * 0.2, 2),
                    "action": f"Reorder {sku} immediately to prevent stockout",
                })
    for pin in (high_rto_pincodes or [])[:3]:
        actions.append({
            "sku": "ALL",
            "category": "pincode",
            "priority": "medium",
            "estimated_impact_inr": 0.0,
            "action": f"Disable COD or add verification for high-RTO pincode {pin}",
        })
    actions.sort(key=lambda a: (PRIORITY_ORDER.get(a["priority"], 9), -a["estimated_impact_inr"]))
    return actions
