from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")

# 1) Create research decision generator
(ROOT / "decision_research_v1.py").write_text(r'''import json
from datetime import datetime
from pathlib import Path

from decision_engine import decide_trade

OUT = Path("static/research")
MARKET = OUT / "market_intelligence_latest.json"
REGIME = OUT / "market_regime_filter_latest.json"
SELL = OUT / "sell_intelligence_latest.json"
DEST = OUT / "decision_engine_latest.json"

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def sell_pressure_map(sell_data):
    out = {}
    for item in sell_data.get("sell_candidates", []):
        sym = item.get("symbol")
        if sym:
            out[sym] = item.get("sell_pressure", 0)
    return out

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    market = load_json(MARKET)
    regime_data = load_json(REGIME)
    sell_data = load_json(SELL)

    regime = regime_data.get("regime", "Unknown")
    news_impact = market.get("overnight_brief", {}).get("news_impact", 0)

    pressures = sell_pressure_map(sell_data)

    candidates = market.get("trade_ready", []) or market.get("scanner_top", [])
    decisions = []

    for stock in candidates[:20]:
        symbol = stock.get("symbol", "UNKNOWN")
        result = decide_trade(
            stock,
            regime,
            news_impact,
            sell_pressure=pressures.get(symbol, 0)
        )

        decisions.append({
            "symbol": symbol,
            "score": stock.get("final_score"),
            "entry_zone": stock.get("entry_zone"),
            "sell_pressure": pressures.get(symbol, 0),
            "action": result.get("action"),
            "confidence": result.get("confidence"),
            "reason": result.get("reason"),
            "status": "research_only"
        })

    summary = {
        "buy_count": len([x for x in decisions if x["action"] in ["BUY", "STRONG_BUY"]]),
        "watch_count": len([x for x in decisions if x["action"] in ["WATCH", "WAIT", "WAIT_PULLBACK"]]),
        "ignore_count": len([x for x in decisions if x["action"] == "IGNORE"]),
        "exit_avoid_count": len([x for x in decisions if x["action"] == "EXIT / AVOID"]),
    }

    payload = {
        "updated_at": now,
        "version": "decision_research_v1",
        "status": "research_only",
        "regime": regime,
        "news_impact": news_impact,
        "summary": summary,
        "decisions": decisions,
        "notes": [
            "Research-only decision layer.",
            "Does not place trades.",
            "Does not change bot behavior.",
            "Used for UI guidance and learning."
        ]
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload["summary"], indent=2))

if __name__ == "__main__":
    main()
''')

# 2) Patch research pipeline to run it after market intelligence exists
pipe = ROOT / "research_pipeline_v1.py"
text = pipe.read_text()

if 'run(["python3", "decision_research_v1.py"])' not in text:
    text = text.replace(
        'latest.write_text(json.dumps(payload, indent=2))',
        'latest.write_text(json.dumps(payload, indent=2))'
    )

    text = text.replace(
        'print("Saved:", latest, flush=True)',
        'print("Saved:", latest, flush=True)\n\n    run(["python3", "decision_research_v1.py"])'
    )

pipe.write_text(text)

print("✅ Installed Decision Research v1")
print("Created: decision_research_v1.py")
print("Patched: research_pipeline_v1.py")
print("Output: static/research/decision_engine_latest.json")
