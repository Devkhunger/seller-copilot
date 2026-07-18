def compute_order_profit(selling_price: float, cogs: float, shipping_fee: float, platform_fee: float) -> dict:
    net_profit = selling_price - cogs - shipping_fee - platform_fee
    margin_pct = (net_profit / selling_price * 100.0) if selling_price > 0 else 0.0
    return {"net_profit": round(net_profit, 2), "margin_pct": round(margin_pct, 2)}
