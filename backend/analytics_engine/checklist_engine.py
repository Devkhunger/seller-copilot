def generate_daily_checklist(sku_metrics: list[dict]) -> list[dict]:
    actions = []
    for item in sku_metrics:
        if item.get("rto_rate", 0) >= 0.30:
            actions.append({
                "sku": item["sku"],
                "priority": "high",
                "action": f"Review COD eligibility for {item['sku']} (RTO {item['rto_rate']*100:.1f}%)",
            })
        if item.get("margin_pct", 0) < 8.0:
            actions.append({
                "sku": item["sku"],
                "priority": "medium",
                "action": f"Reprice {item['sku']} to restore net margin above 8%",
            })
    return actions
