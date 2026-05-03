import json
from datetime import datetime
from pathlib import Path
import yfinance as yf
import pandas as pd

OUT = Path("static/research")
LOG = OUT / "rotation_suggestions_log.jsonl"
DEST = OUT / "rotation_performance_latest.json"

def load_logged(limit=100):
    if not LOG.exists():
        return []
    rows = []
    for line in LOG.read_text().splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows

def get_recent_change(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="5m", progress=False, auto_adjust=True)
        if df.empty or len(df) < 4:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        close = df["Close"].astype(float)
        return round((float(close.iloc[-1]) - float(close.iloc[0])) / float(close.iloc[0]) * 100, 2)
    except Exception:
        return None

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logged = load_logged()
    evaluations = []

    for r in logged:
        sell_symbol = r.get("sell_symbol")
        buy_symbol = r.get("buy_symbol")
        if not sell_symbol or not buy_symbol:
            continue

        sell_change = get_recent_change(sell_symbol)
        buy_change = get_recent_change(buy_symbol)

        if sell_change is None or buy_change is None:
            continue

        rotation_alpha = round(buy_change - sell_change, 2)

        if rotation_alpha > 0.5:
            result = "✅ Rotation helped"
        elif rotation_alpha < -0.5:
            result = "❌ Rotation hurt"
        else:
            result = "➖ Neutral"

        evaluations.append({
            "original_timestamp": r.get("timestamp"),
            "evaluated_at": now,
            "sell_symbol": sell_symbol,
            "buy_symbol": buy_symbol,
            "action": r.get("action"),
            "rotation_score": r.get("rotation_score"),
            "sell_change_pct": sell_change,
            "buy_change_pct": buy_change,
            "rotation_alpha_pct": rotation_alpha,
            "result": result,
        })

    wins = len([x for x in evaluations if "helped" in x["result"]])
    losses = len([x for x in evaluations if "hurt" in x["result"]])
    total = len(evaluations)

    payload = {
        "updated_at": now,
        "status": "research_only",
        "evaluations": evaluations[-50:],
        "summary": {
            "evaluated": total,
            "helped": wins,
            "hurt": losses,
            "neutral": total - wins - losses,
            "win_rate": round((wins / total * 100), 2) if total else 0,
        },
        "notes": [
            "Tracks whether suggested rotations outperformed holding the sell candidate.",
            "Positive alpha means the proposed buy did better than the proposed sell.",
            "Use this before connecting rotation logic to the bot."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
