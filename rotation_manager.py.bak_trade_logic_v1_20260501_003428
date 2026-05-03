def get_position_score(position):
    """
    Lower score = weaker position.
    Higher score = stronger hold.
    """
    try:
        symbol = position.symbol
        entry = float(position.avg_entry_price)
        current = float(position.current_price)
        market_value = abs(float(position.market_value))
        unrealized_plpc = float(position.unrealized_plpc)

        score = 50

        # P/L impact
        score += unrealized_plpc * 120

        # Penalize losers faster
        if unrealized_plpc <= -0.04:
            score -= 35
        elif unrealized_plpc <= -0.025:
            score -= 25
        elif unrealized_plpc <= -0.01:
            score -= 12

        # Reward winners
        if unrealized_plpc >= 0.03:
            score += 15
        elif unrealized_plpc >= 0.015:
            score += 8

        # Avoid rotating tiny/noisy positions too aggressively
        if market_value < 500:
            score += 10

        return {
            "symbol": symbol,
            "score": round(score, 2),
            "change_pct": unrealized_plpc,
            "qty": abs(float(position.qty)),
            "market_value": market_value,
        }

    except Exception:
        return {
            "symbol": getattr(position, "symbol", "UNKNOWN"),
            "score": 999,
            "change_pct": 0,
            "qty": 0,
            "market_value": 0,
        }


def find_weakest_position(positions):
    if not positions:
        return None

    ranked = [get_position_score(p) for p in positions]
    ranked.sort(key=lambda x: x["score"])
    return ranked[0]


def should_rotate(weak_position, new_candidate_score, min_new_score=72, required_edge=18):
    """
    Rotate only when the new trade is clearly stronger than the weakest current position.
    """
    if not weak_position:
        return False, "no weak position"

    weak_symbol = weak_position["symbol"]
    weak_score = weak_position["score"]
    weak_change = weak_position["change_pct"]

    if new_candidate_score < min_new_score:
        return False, f"candidate score too low: {new_candidate_score}"

    # Do not rotate out of healthy positions
    if weak_change >= 0.01:
        return False, f"{weak_symbol} is profitable"

    # Allow faster replacement for meaningful losers
    if weak_change <= -0.035:
        required_edge = 8
    elif weak_change <= -0.02:
        required_edge = 12

    if new_candidate_score < weak_score + required_edge:
        return False, f"candidate edge too small vs {weak_symbol}"

    return True, f"rotate out of {weak_symbol}"
