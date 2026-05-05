"""Research-only setup logger for Ponder Invest AI.

This module never places orders. It records candidate setups in a durable CSV so
later evaluators can label outcomes and feed dashboard learning panels.
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent
RESEARCH_DATA_DIR = ROOT / "research_data"
SHADOW_SETUPS_FILE = RESEARCH_DATA_DIR / "shadow_setups.csv"

FIELDS = [
    "setup_id",
    "timestamp",
    "symbol",
    "setup_type",
    "score",
    "entry_price",
    "market_regime",
    "reason",
    "next_1h_return",
    "next_1d_return",
    "next_3d_return",
    "next_5d_return",
    "outcome",
    "status",
    "source",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _ensure_file(path: Path = SHADOW_SETUPS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def _read_ids(path: Path = SHADOW_SETUPS_FILE) -> set[str]:
    _ensure_file(path)
    try:
        with path.open(newline="") as f:
            return {row.get("setup_id", "") for row in csv.DictReader(f) if row.get("setup_id")}
    except Exception:
        return set()


def make_setup_id(symbol: str, setup_type: str, timestamp: str, source: str = "live_shadow") -> str:
    bucket = str(timestamp or utc_now())[:13]
    raw = f"{source}|{symbol.upper()}|{setup_type}|{bucket}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def log_shadow_setup(
    symbol: str,
    setup_type: str,
    score: float,
    entry_price: float | str = "",
    timestamp: Optional[str] = None,
    market_regime: str = "unknown",
    reason: str = "",
    next_1h_return: float | str = "",
    next_1d_return: float | str = "",
    next_3d_return: float | str = "",
    next_5d_return: float | str = "",
    outcome: str = "pending",
    status: str = "pending",
    source: str = "live_shadow",
    path: Path = SHADOW_SETUPS_FILE,
) -> bool:
    """Append one research setup if it has not already been logged."""
    try:
        timestamp = timestamp or utc_now()
        symbol = str(symbol or "").upper().strip()
        setup_type = str(setup_type or "unknown").strip()
        if not symbol or symbol == "-":
            return False

        _ensure_file(path)
        setup_id = make_setup_id(symbol, setup_type, timestamp, source)
        if setup_id in _read_ids(path):
            return False

        row = {
            "setup_id": setup_id,
            "timestamp": timestamp,
            "symbol": symbol,
            "setup_type": setup_type,
            "score": round(safe_float(score), 2),
            "entry_price": entry_price,
            "market_regime": market_regime,
            "reason": reason,
            "next_1h_return": next_1h_return,
            "next_1d_return": next_1d_return,
            "next_3d_return": next_3d_return,
            "next_5d_return": next_5d_return,
            "outcome": outcome,
            "status": status,
            "source": source,
        }
        with path.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)
        return True
    except Exception:
        return False


def classify_candidate_setup(candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create one or more shadow setup labels from an already-scored candidate."""
    symbol = str(candidate.get("symbol", "")).upper()
    score = safe_float(candidate.get("score"))
    trend = str(candidate.get("trend", "unknown")).lower()
    analyst = safe_float(candidate.get("analyst"))
    news = safe_float(candidate.get("news"))
    reason_bits = [f"trend={trend}", f"analyst={analyst}", f"news={news}", f"score={score}"]
    labels: List[Dict[str, Any]] = []

    if score >= 80:
        labels.append({"setup_type": "day_trade_momentum", "reason": "high score fast signal | " + " | ".join(reason_bits)})
    if score >= 68 and trend == "bullish":
        labels.append({"setup_type": "small_cap_breakout", "reason": "68+ bullish candidate | " + " | ".join(reason_bits)})
    if trend == "bullish" and analyst >= 4 and news <= 0:
        labels.append({"setup_type": "large_cap_pullback", "reason": "bullish trend with analyst support and quiet news | " + " | ".join(reason_bits)})
    if trend == "bullish" and news >= 1:
        labels.append({"setup_type": "earnings_or_news_reaction", "reason": "bullish candidate with catalyst/news confirmation | " + " | ".join(reason_bits)})
    if not labels and score >= 63:
        labels.append({"setup_type": "general_momentum", "reason": "watchlist candidate near trade threshold | " + " | ".join(reason_bits)})

    return labels


def log_shadow_setups_from_candidates(
    candidates: Iterable[Dict[str, Any]],
    market_regime: str = "unknown",
    price_lookup: Optional[Any] = None,
    source: str = "bot_candidate_shadow",
) -> int:
    """Log research-only setup rows for scored bot candidates.

    price_lookup may be a callable(symbol)->price. Failures are ignored.
    """
    count = 0
    for candidate in candidates or []:
        symbol = str(candidate.get("symbol", "")).upper()
        score = safe_float(candidate.get("score"))
        entry_price: Any = candidate.get("entry_price", "")
        if not entry_price and price_lookup:
            try:
                entry_price = round(safe_float(price_lookup(symbol)), 4)
            except Exception:
                entry_price = ""
        for label in classify_candidate_setup(candidate):
            if log_shadow_setup(
                symbol=symbol,
                setup_type=label["setup_type"],
                score=score,
                entry_price=entry_price,
                market_regime=market_regime,
                reason=label["reason"],
                source=source,
            ):
                count += 1
    return count


if __name__ == "__main__":
    print(f"shadow setup file: {SHADOW_SETUPS_FILE}")
