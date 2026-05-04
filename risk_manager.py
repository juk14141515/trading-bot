from trade_memory import recent_trade_count_today, symbol_traded_today

MAX_TRADES_PER_DAY = 5
MAX_POSITION_PCT = 0.12
RISK_PER_TRADE_PCT = 0.005

# Paper-learning threshold. This is intentionally looser than future live cash rules
# so the bot can collect enough paper-trade outcomes to learn from.
MIN_SCORE_TO_TRADE = 70


def can_trade(symbol, score):
    if score < MIN_SCORE_TO_TRADE:
        return False, f"score too low: {score}"

    if recent_trade_count_today() >= MAX_TRADES_PER_DAY:
        return False, "max trades per day reached"

    if symbol_traded_today(symbol):
        return False, f"{symbol} already traded today"

    return True, "approved"


def calculate_position_size(equity, price, volatility_pct):
    risk_amount = equity * RISK_PER_TRADE_PCT
    stop_distance = price * max(volatility_pct, 0.03)
    qty = int(risk_amount / stop_distance)

    max_position_value = equity * MAX_POSITION_PCT
    max_qty = int(max_position_value / price)

    return max(0, min(qty, max_qty))
