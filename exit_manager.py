def should_exit(position, get_trend):
    symbol = position.symbol
    entry = float(position.avg_entry_price)
    current = float(position.current_price)

    change = (current - entry) / entry

    # === 1. Trailing stop (real version)
    if change > 0.05:
        # if it pulled back from a strong gain
        if change < 0.03:
            return True, "trailing stop"

    # === 2. Dead trade (give it time)
    if abs(change) < 0.01:
        return False, None  # DO NOT exit yet

    # === 3. Weak trend exit
    if get_trend(symbol) == "neutral" and change < -0.02:
        return True, "weak trend"

    # === 4. Slow loser (important)
    if change < -0.03:
        return True, "slow loser"

    return False, None
