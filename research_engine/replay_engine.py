"""
Ponder Invest AI - Replay Engine v1

Purpose:
    Read-only local research tool that replays a simplified version of the live bot's
    decision flow over historical market data.

Safety:
    - No Alpaca imports
    - No order submission
    - No live bot state changes
    - Does not import bot.py
    - Writes only research outputs

Usage:
    python3 research_engine/replay_engine.py
    python3 research_engine/replay_engine.py --symbols AAPL,NVDA,MSFT --period 6mo

Outputs:
    static/research/replay_engine_latest.json
    research_data/replay_decisions.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
STATIC_RESEARCH = ROOT / "static" / "research"
RESEARCH_DATA = ROOT / "research_data"
JSON_OUTPUT = STATIC_RESEARCH / "replay_engine_latest.json"
CSV_OUTPUT = RESEARCH_DATA / "replay_decisions.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import pandas as pd
except Exception:  # pragma: no cover - handled at runtime
    pd = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover - handled at runtime
    yf = None

try:
    from scoring_engine import calculate_weighted_score
except Exception:  # safe fallback mirrors current rough weighting
    def calculate_weighted_score(
        trend_score=0,
        analyst_score=0,
        news_score=0,
        momentum_score=0,
        volatility_score=50,
    ):
        return round(
            max(0, min(100, float(trend_score))) * 0.35
            + max(0, min(100, float(analyst_score))) * 0.20
            + max(0, min(100, float(news_score))) * 0.15
            + max(0, min(100, float(momentum_score))) * 0.20
            + max(0, min(100, float(volatility_score))) * 0.10,
            2,
        )

try:
    from rotation_manager import should_rotate
except Exception:
    def should_rotate(weak_position, new_candidate_score, min_new_score=72, required_edge=18):
        if not weak_position:
            return False, "no weak position"
        if new_candidate_score < min_new_score:
            return False, f"candidate score too low: {new_candidate_score}"
        if weak_position.get("change_pct", 0) >= 0.01:
            return False, f"{weak_position.get('symbol')} is profitable"
        return new_candidate_score >= weak_position.get("score", 50) + required_edge, "fallback rotation rule"

try:
    from trade_guard_v1 import should_force_exit
except Exception:
    def should_force_exit(symbol, pnl_pct, position_score=None):
        if float(pnl_pct) <= -3.0:
            return True, f"fast_cut_loss_{float(pnl_pct):.2f}%"
        return False, "hold"


DEFAULT_WATCHLIST = [
    "AAPL", "AMZN", "NVDA", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "PLTR", "SOFI",
    "COIN", "RBLX", "U", "NFLX", "ORCL", "UBER", "SHOP", "PYPL",
    "SQ", "HOOD", "AFRM", "NET", "DDOG", "CRWD", "PANW", "ZS",
    "MDB", "APP", "UPST", "DKNG", "ROKU", "F", "GM", "T", "DIS",
]

MAX_POSITIONS = 3
STARTING_CASH = 100_000.0
MAX_TOTAL_DEPLOYED_PERCENT = 0.30
MAX_SINGLE_TRADE_PERCENT = 0.08
MIN_TRADE_DOLLARS = 500.0
MIN_SCORE_TO_TRADE = 63.0
STOP_LOSS_PERCENT = -0.06
TAKE_PROFIT_PERCENT = 0.12
TRAILING_START = 0.05
TRAILING_GIVEBACK = 0.02


@dataclass
class SimPosition:
    symbol: str
    qty: float
    entry_price: float
    entry_date: str
    entry_score: float
    high_water_pct: float = 0.0

    def market_value(self, price: float) -> float:
        return self.qty * price

    def pnl_pct(self, price: float) -> float:
        if self.entry_price <= 0:
            return 0.0
        return (price - self.entry_price) / self.entry_price

    def pnl_dollars(self, price: float) -> float:
        return (price - self.entry_price) * self.qty


@dataclass
class ReplayTrade:
    date: str
    symbol: str
    side: str
    qty: float
    price: float
    score: Optional[float]
    reason: str
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


@dataclass
class ReplayDecision:
    date: str
    event: str
    symbol: str
    score: Optional[float]
    reason: str
    cash: float
    equity: float
    positions: int


def safe_float(value, default=0.0) -> float:
    try:
        if value is None:
            return default
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        value = float(value)
        if math.isnan(value):
            return default
        return value
    except Exception:
        return default


def flatten_download(data):
    if pd is None or data is None or len(data) == 0:
        return data
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [c[0] if isinstance(c, tuple) else c for c in data.columns]
    return data.dropna(how="all")


def download_history(symbol: str, period: str, interval: str):
    if yf is None:
        raise RuntimeError("yfinance is not installed. Install it in the local research venv.")
    data = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
    data = flatten_download(data)
    if data is None or len(data) < 60:
        return None
    return data


def trend_at(data, idx: int) -> str:
    if idx < 50:
        return "insufficient"
    window = data.iloc[: idx + 1].copy()
    close = safe_float(window["Close"].iloc[-1])
    sma20 = safe_float(window["Close"].rolling(20).mean().iloc[-1])
    sma50 = safe_float(window["Close"].rolling(50).mean().iloc[-1])
    if close > sma20 > sma50:
        return "bullish"
    if close < sma20 < sma50:
        return "bearish"
    return "neutral"


def momentum_score_at(data, idx: int, lookback: int = 5) -> float:
    if idx < lookback:
        return 50.0
    current = safe_float(data["Close"].iloc[idx])
    past = safe_float(data["Close"].iloc[idx - lookback])
    if past <= 0:
        return 50.0
    pct = ((current - past) / past) * 100
    # Bot's live momentum is bounded -10 to +10, but scoring expects 0-100.
    # Convert short-term momentum into a neutral-centered 0-100 component.
    return round(max(0, min(100, 50 + pct * 5)), 2)


def volatility_score_at(data, idx: int, lookback: int = 14) -> float:
    if idx < lookback:
        return 50.0
    closes = data["Close"].iloc[idx - lookback : idx + 1].pct_change().dropna()
    vol = safe_float(closes.std(), 0.0)
    # Mild volatility is useful; extreme volatility is penalized.
    if vol <= 0:
        return 50.0
    return round(max(10, min(90, 80 - vol * 1200)), 2)


def analyst_proxy_score(symbol: str) -> float:
    """
    Historical analyst/news replay is unavailable without stored point-in-time data.
    Use neutral defaults so replay focuses on price/technical behavior.
    """
    return 50.0


def news_proxy_score(symbol: str) -> float:
    return 50.0


def score_symbol(symbol: str, data, idx: int) -> Tuple[float, Dict[str, float | str]]:
    trend = trend_at(data, idx)
    trend_score = 100 if trend == "bullish" else 0
    analyst_score = analyst_proxy_score(symbol)
    news_score = news_proxy_score(symbol)
    momentum_score = momentum_score_at(data, idx)
    volatility_score = volatility_score_at(data, idx)
    final = calculate_weighted_score(
        trend_score=trend_score,
        analyst_score=analyst_score,
        news_score=news_score,
        momentum_score=momentum_score,
        volatility_score=volatility_score,
    )
    return final, {
        "trend": trend,
        "trend_score": trend_score,
        "analyst_score": analyst_score,
        "news_score": news_score,
        "momentum_score": momentum_score,
        "volatility_score": volatility_score,
    }


def position_score(position: SimPosition, current_price: float) -> Dict[str, float | str]:
    change = position.pnl_pct(current_price)
    market_value = position.market_value(current_price)
    score = 50 + change * 120
    if change <= -0.04:
        score -= 35
    elif change <= -0.025:
        score -= 25
    elif change <= -0.01:
        score -= 12
    if change >= 0.03:
        score += 15
    elif change >= 0.015:
        score += 8
    if market_value < 500:
        score += 10
    return {
        "symbol": position.symbol,
        "score": round(score, 2),
        "change_pct": change,
        "qty": position.qty,
        "market_value": market_value,
    }


def calculate_trade_dollars(score: float, cash: float, equity: float, deployed: float) -> float:
    if score >= 75:
        dollars = cash * 0.08
    elif score >= 63:
        dollars = cash * 0.06
    else:
        dollars = cash * 0.04
    dollars = min(dollars, cash * MAX_SINGLE_TRADE_PERCENT)
    dollars = max(dollars, MIN_TRADE_DOLLARS)
    max_deployed = equity * MAX_TOTAL_DEPLOYED_PERCENT
    remaining_deployable = max(0.0, max_deployed - deployed)
    return round(min(dollars, remaining_deployable, cash), 2)


def should_exit_position(position: SimPosition, current_price: float, trend: str) -> Tuple[bool, str]:
    change = position.pnl_pct(current_price)
    position.high_water_pct = max(position.high_water_pct, change)

    guard_exit, guard_reason = should_force_exit(position.symbol, change * 100)
    if guard_exit:
        return True, guard_reason

    if change <= STOP_LOSS_PERCENT:
        return True, "stop loss"
    if change >= TAKE_PROFIT_PERCENT:
        return True, "take profit"
    if trend == "bearish":
        return True, "trend bearish"
    if position.high_water_pct >= TRAILING_START and change <= position.high_water_pct - TRAILING_GIVEBACK:
        return True, "trailing stop"
    if trend == "neutral" and change < -0.02:
        return True, "weak trend"
    if change < -0.03:
        return True, "slow loser"
    return False, "hold"


def common_replay_dates(histories: Dict[str, object]) -> List:
    dates = None
    for data in histories.values():
        idx = list(data.index)
        if dates is None:
            dates = set(idx)
        else:
            dates &= set(idx)
    if not dates:
        return []
    return sorted(dates)


def close_for_date(data, date) -> Optional[float]:
    try:
        row = data.loc[date]
        if hasattr(row, "iloc") and len(getattr(row, "shape", [])) > 1:
            row = row.iloc[0]
        price = safe_float(row["Close"])
        return price if price > 0 else None
    except Exception:
        return None


def index_for_date(data, date) -> Optional[int]:
    try:
        loc = data.index.get_loc(date)
        if isinstance(loc, slice):
            return loc.start
        if hasattr(loc, "tolist"):
            values = loc.tolist()
            if isinstance(values, list):
                return values.index(True) if True in values else int(values[0])
        return int(loc)
    except Exception:
        return None


def write_csv(decisions: List[ReplayDecision]) -> None:
    RESEARCH_DATA.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(decisions[0]).keys()) if decisions else [
            "date", "event", "symbol", "score", "reason", "cash", "equity", "positions"
        ])
        writer.writeheader()
        for decision in decisions:
            writer.writerow(asdict(decision))


def run_replay(symbols: List[str], period: str, interval: str) -> Dict:
    if pd is None:
        raise RuntimeError("pandas is required for replay_engine.py")

    histories = {}
    missing = []
    for symbol in symbols:
        try:
            data = download_history(symbol, period, interval)
            if data is None:
                missing.append(symbol)
            else:
                histories[symbol] = data
        except Exception as exc:
            missing.append(f"{symbol}: {exc}")

    if "SPY" not in histories:
        spy = download_history("SPY", period, interval)
        if spy is not None:
            histories["SPY"] = spy

    tradable_symbols = [s for s in symbols if s in histories and s != "SPY"]
    dates = common_replay_dates({s: histories[s] for s in tradable_symbols + (["SPY"] if "SPY" in histories else [])})

    cash = STARTING_CASH
    positions: Dict[str, SimPosition] = {}
    trades: List[ReplayTrade] = []
    decisions: List[ReplayDecision] = []
    equity_curve = []

    for date in dates:
        date_str = str(date.date()) if hasattr(date, "date") else str(date)
        portfolio_value = cash
        for symbol, pos in list(positions.items()):
            price = close_for_date(histories[symbol], date)
            if price:
                portfolio_value += pos.market_value(price)

        # Manage exits first, mirroring live bot cycle order.
        for symbol, pos in list(positions.items()):
            data = histories.get(symbol)
            price = close_for_date(data, date) if data is not None else None
            idx = index_for_date(data, date) if data is not None else None
            if price is None or idx is None:
                continue
            trend = trend_at(data, idx)
            exit_now, reason = should_exit_position(pos, price, trend)
            if exit_now:
                pnl = pos.pnl_dollars(price)
                pnl_pct = pos.pnl_pct(price)
                cash += pos.qty * price
                trades.append(ReplayTrade(date_str, symbol, "sell", pos.qty, round(price, 2), None, reason, round(pnl, 2), round(pnl_pct, 4)))
                decisions.append(ReplayDecision(date_str, "SELL", symbol, None, reason, round(cash, 2), round(portfolio_value, 2), len(positions) - 1))
                del positions[symbol]

        spy_trend = "bullish"
        if "SPY" in histories:
            spy_idx = index_for_date(histories["SPY"], date)
            if spy_idx is not None:
                spy_trend = trend_at(histories["SPY"], spy_idx)
        if spy_trend != "bullish":
            decisions.append(ReplayDecision(date_str, "SKIP_CYCLE", "SPY", None, f"SPY trend {spy_trend}", round(cash, 2), round(portfolio_value, 2), len(positions)))
            equity_curve.append({"date": date_str, "equity": round(portfolio_value, 2), "cash": round(cash, 2), "positions": len(positions)})
            continue

        candidates = []
        for symbol in tradable_symbols:
            if symbol in positions:
                continue
            data = histories[symbol]
            idx = index_for_date(data, date)
            price = close_for_date(data, date)
            if idx is None or price is None or idx < 50:
                continue
            score, components = score_symbol(symbol, data, idx)
            if components["trend"] == "bullish" and score >= MIN_SCORE_TO_TRADE:
                candidates.append({"symbol": symbol, "score": score, "price": price, "components": components})
            else:
                decisions.append(ReplayDecision(date_str, "SKIP_BUY", symbol, score, f"filtered trend={components['trend']} score={score}", round(cash, 2), round(portfolio_value, 2), len(positions)))

        candidates.sort(key=lambda x: x["score"], reverse=True)
        if not candidates:
            equity_curve.append({"date": date_str, "equity": round(portfolio_value, 2), "cash": round(cash, 2), "positions": len(positions)})
            continue

        slots_available = MAX_POSITIONS - len(positions)
        if slots_available <= 0:
            # Full replay mode includes rotation simulation.
            candidate = candidates[0]
            weak_positions = []
            for symbol, pos in positions.items():
                current_price = close_for_date(histories[symbol], date)
                if current_price:
                    weak_positions.append(position_score(pos, current_price))
            weak_positions.sort(key=lambda x: x["score"])
            weakest = weak_positions[0] if weak_positions else None
            rotate_ok, rotate_reason = should_rotate(weakest, candidate["score"])
            if rotate_ok and weakest:
                old_symbol = str(weakest["symbol"])
                old_pos = positions[old_symbol]
                old_price = close_for_date(histories[old_symbol], date)
                if old_price:
                    pnl = old_pos.pnl_dollars(old_price)
                    pnl_pct = old_pos.pnl_pct(old_price)
                    cash += old_pos.qty * old_price
                    trades.append(ReplayTrade(date_str, old_symbol, "sell", old_pos.qty, round(old_price, 2), None, f"rotation into {candidate['symbol']}", round(pnl, 2), round(pnl_pct, 4)))
                    decisions.append(ReplayDecision(date_str, "ROTATION_SELL", old_symbol, None, rotate_reason, round(cash, 2), round(portfolio_value, 2), len(positions) - 1))
                    del positions[old_symbol]
                    slots_available = 1
            else:
                decisions.append(ReplayDecision(date_str, "NO_ROTATION", candidate["symbol"], candidate["score"], rotate_reason, round(cash, 2), round(portfolio_value, 2), len(positions)))

        for candidate in candidates[: max(0, slots_available)]:
            if len(positions) >= MAX_POSITIONS:
                break
            symbol = candidate["symbol"]
            price = safe_float(candidate["price"])
            deployed = sum(pos.market_value(close_for_date(histories[sym], date) or pos.entry_price) for sym, pos in positions.items())
            equity = cash + deployed
            dollars = calculate_trade_dollars(candidate["score"], cash, equity, deployed)
            if dollars < MIN_TRADE_DOLLARS or price <= 0:
                decisions.append(ReplayDecision(date_str, "SKIP_BUY", symbol, candidate["score"], "insufficient deployable cash", round(cash, 2), round(equity, 2), len(positions)))
                continue
            qty = dollars / price
            cash -= dollars
            positions[symbol] = SimPosition(symbol=symbol, qty=qty, entry_price=price, entry_date=date_str, entry_score=candidate["score"])
            trades.append(ReplayTrade(date_str, symbol, "buy", round(qty, 4), round(price, 2), candidate["score"], "replay candidate selected"))
            decisions.append(ReplayDecision(date_str, "BUY", symbol, candidate["score"], "qualified replay candidate", round(cash, 2), round(equity, 2), len(positions)))

        deployed_now = sum(pos.market_value(close_for_date(histories[sym], date) or pos.entry_price) for sym, pos in positions.items())
        equity_curve.append({"date": date_str, "equity": round(cash + deployed_now, 2), "cash": round(cash, 2), "positions": len(positions)})

    # Liquidate at final available prices for final summary only.
    final_equity = cash
    open_positions = []
    if dates:
        final_date = dates[-1]
        for symbol, pos in positions.items():
            price = close_for_date(histories[symbol], final_date) or pos.entry_price
            final_equity += pos.market_value(price)
            open_positions.append({
                "symbol": symbol,
                "qty": round(pos.qty, 4),
                "entry_price": round(pos.entry_price, 2),
                "last_price": round(price, 2),
                "unrealized_pnl": round(pos.pnl_dollars(price), 2),
                "unrealized_pnl_pct": round(pos.pnl_pct(price), 4),
                "entry_score": pos.entry_score,
                "entry_date": pos.entry_date,
            })

    closed_sells = [t for t in trades if t.side == "sell"]
    wins = [t for t in closed_sells if (t.pnl or 0) > 0]
    losses = [t for t in closed_sells if (t.pnl or 0) < 0]
    gross_win = sum(t.pnl or 0 for t in wins)
    gross_loss = abs(sum(t.pnl or 0 for t in losses))
    win_rate = round((len(wins) / len(closed_sells)) * 100, 2) if closed_sells else 0
    profit_factor = round(gross_win / gross_loss, 2) if gross_loss else (round(gross_win, 2) if gross_win else 0)

    peak = None
    max_drawdown = 0.0
    for point in equity_curve:
        eq = point["equity"]
        peak = eq if peak is None else max(peak, eq)
        if peak:
            max_drawdown = min(max_drawdown, (eq - peak) / peak)

    result = {
        "status": "research_only",
        "mode": "full_bot_replay_v1",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "safety": {
            "read_only": True,
            "orders_enabled": False,
            "alpaca_imports": False,
            "bot_py_imported": False,
            "live_trading_changed": False,
        },
        "config": {
            "symbols": tradable_symbols,
            "period": period,
            "interval": interval,
            "starting_cash": STARTING_CASH,
            "max_positions": MAX_POSITIONS,
            "min_score_to_trade": MIN_SCORE_TO_TRADE,
            "notes": [
                "Historical analyst/news point-in-time data is not available, so neutral proxy values are used.",
                "Replay is for research hypotheses only, not live-trading proof.",
                "This intentionally does not import bot.py because bot.py starts the live loop on import.",
            ],
        },
        "summary": {
            "start_equity": STARTING_CASH,
            "final_equity": round(final_equity, 2),
            "net_pnl": round(final_equity - STARTING_CASH, 2),
            "net_return_pct": round((final_equity - STARTING_CASH) / STARTING_CASH * 100, 2),
            "closed_trades": len(closed_sells),
            "buys": len([t for t in trades if t.side == "buy"]),
            "sells": len(closed_sells),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "open_positions": len(open_positions),
            "decision_count": len(decisions),
            "missing_symbols": missing,
        },
        "open_positions": open_positions,
        "recent_trades": [asdict(t) for t in trades[-50:]],
        "recent_decisions": [asdict(d) for d in decisions[-100:]],
        "equity_curve": equity_curve[-250:],
        "data_quality": {
            "confidence": "low" if len(closed_sells) < 30 else "medium",
            "reason": "Replay v1 uses neutral analyst/news proxies and daily bars; validate before using for live logic.",
            "sample_sizes": {
                "symbols_loaded": len(tradable_symbols),
                "dates_replayed": len(dates),
                "closed_sells": len(closed_sells),
                "decisions": len(decisions),
            },
        },
        "recommendations": build_recommendations(len(closed_sells), win_rate, profit_factor, max_drawdown),
    }
    return result, decisions


def build_recommendations(closed: int, win_rate: float, profit_factor: float, max_drawdown: float) -> List[Dict[str, str]]:
    recs = []
    if closed < 30:
        recs.append({"type": "research_only", "message": "Keep this as hypothesis generation. Closed replay sample is still small."})
    if closed >= 10 and win_rate < 45:
        recs.append({"type": "risk", "message": "Replay win rate is weak. Review entry filters before lowering thresholds."})
    if closed >= 10 and profit_factor < 1:
        recs.append({"type": "risk", "message": "Profit factor is below 1. Focus on exits and loser control before adding more entries."})
    if max_drawdown <= -0.08:
        recs.append({"type": "drawdown", "message": "Replay drawdown exceeded 8%. Test stricter sizing or faster exits."})
    if not recs:
        recs.append({"type": "research_only", "message": "Replay completed. Compare this output against Shadow vs Live before changing live rules."})
    return recs


def save_outputs(result: Dict, decisions: List[ReplayDecision]) -> None:
    STATIC_RESEARCH.mkdir(parents=True, exist_ok=True)
    RESEARCH_DATA.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(result, indent=2))
    write_csv(decisions)


def parse_symbols(raw: str) -> List[str]:
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    return list(dict.fromkeys(symbols))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run read-only Ponder Invest AI full bot replay.")
    parser.add_argument("--symbols", default=",".join(DEFAULT_WATCHLIST[:12]), help="Comma-separated symbols to replay.")
    parser.add_argument("--period", default="6mo", help="yfinance period, e.g. 3mo, 6mo, 1y, 2y")
    parser.add_argument("--interval", default="1d", help="yfinance interval, e.g. 1d, 1h")
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    result, decisions = run_replay(symbols=symbols, period=args.period, interval=args.interval)
    save_outputs(result, decisions)

    summary = result.get("summary", {})
    print("Replay complete")
    print(f"Output: {JSON_OUTPUT}")
    print(f"Decisions: {CSV_OUTPUT}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
