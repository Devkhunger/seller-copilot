def days_of_cover(stock_on_hand: int, avg_daily_units: float) -> float | None:
    if stock_on_hand <= 0:
        return 0.0
    if avg_daily_units <= 0:
        return None
    return round(stock_on_hand / avg_daily_units, 1)

def needs_reorder(stock_on_hand: int, avg_daily_units: float, lead_time_days: int = 7, safety_days: int = 4) -> bool:
    cover = days_of_cover(stock_on_hand, avg_daily_units)
    if cover is None:
        return False
    return cover <= (lead_time_days + safety_days)
