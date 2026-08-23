def predict_rto_probability(
    payment_mode: str,
    order_value: float,
    pincode_rto_rate: float | None = None,
    prior_buyer_rtos: int = 0,
    pincode: str | None = None,
    pincode_profiles: dict[str, dict] | None = None,
) -> float:
    if pincode_rto_rate is None and pincode and pincode_profiles:
        profile = pincode_profiles.get(str(pincode).strip())
        if profile is not None:
            pincode_rto_rate = profile.get("rto_rate")
    base_rate = 0.12 if pincode_rto_rate is None else pincode_rto_rate
    score = max(0.0, min(1.0, base_rate))
    is_cod = str(payment_mode or "").lower() == "cod"
    if is_cod:
        score += 0.18
    if is_cod and order_value >= 1500:
        score += 0.09
    elif order_value >= 2500:
        score += 0.04
    if prior_buyer_rtos > 0:
        score += min(0.30, prior_buyer_rtos * 0.12)
    return round(max(0.01, min(0.99, score)), 4)

def risk_band(probability: float) -> str:
    if probability >= 0.45:
        return "high"
    if probability >= 0.25:
        return "medium"
    return "low"
