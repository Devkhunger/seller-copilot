def compute_order_profit(
    selling_price: float,
    cogs: float,
    shipping_fee: float,
    platform_fee: float,
    is_rto: bool = False,
    reverse_shipping_fee: float = 0.0,
    gst_rate: float = 0.18,
) -> dict:
    if is_rto:
        loss = -(shipping_fee + reverse_shipping_fee)
        return {"net_profit": round(loss, 2), "margin_pct": -100.0 if selling_price > 0 else 0.0}
    taxable_revenue = selling_price / (1.0 + gst_rate) if gst_rate > 0 else selling_price
    net_profit = taxable_revenue - cogs - shipping_fee - platform_fee
    margin_pct = (net_profit / selling_price * 100.0) if selling_price > 0 else 0.0
    return {"net_profit": round(net_profit, 2), "margin_pct": round(margin_pct, 2)}
