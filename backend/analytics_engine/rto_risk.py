def predict_rto_probability(payment_mode: str, order_value: float, pincode_rto_rate: float | None = None) -> float:
    base_rate = 0.12 if pincode_rto_rate is None else pincode_rto_rate
    score = max(0.0, min(1.0, base_rate))
    if str(payment_mode or "").lower() == "cod":
        score += 0.18
    if order_value >= 1500:
        score += 0.07
    return round(max(0.01, min(0.99, score)), 4)
