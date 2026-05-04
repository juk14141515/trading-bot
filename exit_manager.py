TRAILING_HIGH_WATER = {}


def should_exit(position, get_trend):
    symbol = position.symbol
    entry = float(position.avg_entry_price)
    current = float(position.current_price)

    change = (current - entry) / entry

    # === 1. Trailing stop
    # Track each position's best unrealized gain while the bot process is running.
    # Once a position has been up at least 5%, exit if it gives back 2% or more.
    previous_high = TRAILING_HIGH_WATER.get(symbol, change)
    high_water = max(previous_high, change)
    TRAILING_HIGH_WATER[symbol] = high_water

    if high_water >= 0.05 and change <= high_water - 0.02:
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
