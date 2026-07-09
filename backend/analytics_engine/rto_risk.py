def predict_rto_probability(payment_mode: str, order_value: float, pincode_rto_rate: float = 0.12) -> float:
    score = pincode_rto_rate
    if payment_mode == "cod":
        score += 0.18
    if order_value >= 1500:
        score += 0.07
    return round(score, 4)
