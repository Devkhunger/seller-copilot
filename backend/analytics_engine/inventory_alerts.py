def days_of_cover(stock_on_hand: int, avg_daily_units: float) -> float:
    return round(stock_on_hand / avg_daily_units, 1)
