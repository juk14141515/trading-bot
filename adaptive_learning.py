
import csv
import os
from statistics import mean

TRADE_LOG_FILE = "trade_history.csv"

MIN_TRADES_TO_ADAPT = 8
MIN_SYMBOL_TRADES = 3
MAX_BOOST = 8
MAX_PENALTY = 12


def clamp(value, low=0, high=100):
    try:
        value = float(value)
    except Exception:
        value = 50
    return max(low, min(high, value))


def _read_trades():
    if not os.path.exists(TRADE_LOG_FILE):
        return []

    rows = []
    try:
        with open(TRADE_LOG_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception:
        return []

    return rows


def _closed_trades():
    rows = _read_trades()
    closed = []

    for row in rows:
        try:
            pnl = row.get("pnl")
            pnl_pct = row.get("pnl_pct")

            if pnl not in ("", None):
                row["pnl_float"] = float(pnl)
                row["pnl_pct_float"] = float(pnl_pct) if pnl_pct not in ("", None) else 0.0
                closed.append(row)
        except Exception:
            continue

    return closed


def get_performance_summary():
    trades = _closed_trades()

    if not trades:
        return {
            "trade_count": 0,
            "win_rate": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "mode": "neutral_no_data",
        }

    wins = [t["pnl_float"] for t in trades if t["pnl_float"] > 0]
    losses = [abs(t["pnl_float"]) for t in trades if t["pnl_float"] < 0]

    win_rate = len(wins) / len(trades) if trades else 0
    avg_win = mean(wins) if wins else 0
    avg_loss = mean(losses) if losses else 0

    gross_win = sum(wins)
    gross_loss = sum(losses)

    profit_factor = gross_win / gross_loss if gross_loss > 0 else gross_win if gross_win > 0 else 0

    return {
        "trade_count": len(trades),
        "win_rate": round(win_rate * 100, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "mode": "adaptive" if len(trades) >= MIN_TRADES_TO_ADAPT else "learning",
    }


def get_symbol_performance(symbol):
    trades = [t for t in _closed_trades() if t.get("symbol") == symbol]

    if len(trades) < MIN_SYMBOL_TRADES:
        return {
            "symbol": symbol,
            "trade_count": len(trades),
            "adjustment": 0,
            "reason": "not enough symbol history",
        }

    wins = [t for t in trades if t["pnl_float"] > 0]
    losses = [t for t in trades if t["pnl_float"] < 0]
    win_rate = len(wins) / len(trades)

    avg_pnl = mean([t["pnl_float"] for t in trades])

    adjustment = 0
    reasons = []

    if win_rate >= 0.6 and avg_pnl > 0:
        adjustment += MAX_BOOST
        reasons.append("symbol has strong history")
    elif win_rate <= 0.4 and avg_pnl < 0:
        adjustment -= MAX_PENALTY
        reasons.append("symbol has weak history")

    return {
        "symbol": symbol,
        "trade_count": len(trades),
        "win_rate": round(win_rate * 100, 2),
        "avg_pnl": round(avg_pnl, 2),
        "adjustment": adjustment,
        "reason": ", ".join(reasons) if reasons else "neutral symbol history",
    }


def apply_adaptive_score(symbol, base_score):
    base_score = clamp(base_score)
    summary = get_performance_summary()

    # Safe mode: do not adapt from tiny/no data
    if summary["trade_count"] < MIN_TRADES_TO_ADAPT:
        return round(base_score, 2), f"adaptive neutral | trades={summary['trade_count']}"

    adjustment = 0
    reasons = []

    # Global performance adjustment
    if summary["profit_factor"] >= 1.4 and summary["win_rate"] >= 55:
        adjustment += 4
        reasons.append("global system performing well")
    elif summary["profit_factor"] < 0.9 or summary["win_rate"] < 45:
        adjustment -= 6
        reasons.append("global system underperforming")

    # Symbol-specific adjustment
    symbol_perf = get_symbol_performance(symbol)
    adjustment += symbol_perf.get("adjustment", 0)

    if symbol_perf.get("adjustment", 0) != 0:
        reasons.append(symbol_perf.get("reason", "symbol adjustment"))

    # Confidence guardrails
    adjustment = max(-15, min(10, adjustment))

    adjusted_score = clamp(base_score + adjustment)

    reason = "; ".join(reasons) if reasons else "adaptive neutral"
    reason += f" | base={base_score} adjusted={adjusted_score} trades={summary['trade_count']}"

    return round(adjusted_score, 2), reason


def get_win_loss_summary():
    trades = _closed_trades()

    wins = [t for t in trades if t["pnl_float"] > 0]
    losses = [t for t in trades if t["pnl_float"] < 0]

    return {
        "closed_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round((len(wins) / len(trades)) * 100, 2) if trades else 0,
        "net_pnl": round(sum(t["pnl_float"] for t in trades), 2) if trades else 0,
    }
