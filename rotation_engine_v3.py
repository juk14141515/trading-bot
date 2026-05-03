import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

SCANNER = OUT / "market_intelligence_latest.json"
SELL = OUT / "sell_intelligence_latest.json"
PERF = OUT / "rotation_performance_latest.json"
REGIME = OUT / "market_regime_filter_latest.json"
DEST = OUT / "rotation_engine_latest.json"
PERF_LOG = OUT / "rotation_suggestions_log.jsonl"

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def historical_adjustment(sell_symbol, buy_symbol):
    perf = load_json(PERF)
    evaluations = perf.get("evaluations", [])

    pair = [x for x in evaluations if x.get("sell_symbol") == sell_symbol and x.get("buy_symbol") == buy_symbol]
    buy = [x for x in evaluations if x.get("buy_symbol") == buy_symbol]
    sell = [x for x in evaluations if x.get("sell_symbol") == sell_symbol]

    adjustment = 0
    notes = []

    def score(rows, label, weight):
        helped = len([x for x in rows if "helped" in str(x.get("result", "")).lower()])
        hurt = len([x for x in rows if "hurt" in str(x.get("result", "")).lower()])
        total = helped + hurt
        if total < 5:
            return 0, f"{label} does not have enough history yet"
        rate = helped / total
        if rate >= 0.65:
            return weight, f"{label} has strong historical rotation results"
        if rate <= 0.45:
            return -weight, f"{label} has weak historical rotation results"
        return 0, None

    for rows, label, weight in [
        (pair, "This exact pair", 5),
        (buy, f"Buy target", 3),
        (sell, f"Sell source", 2),
    ]:
        adj, note = score(rows, label, weight)
        adjustment += adj
        if note:
            notes.append(note)

    return adjustment, notes

def score_rotation(sell_item, buy_item):
    sell_symbol = sell_item.get("symbol")
    buy_symbol = buy_item.get("symbol")

    sell_pressure = float(sell_item.get("sell_pressure", 0))
    buy_score = float(buy_item.get("final_score", 0))
    entry_score = float(buy_item.get("entry_score", 50))
    expected_edge = buy_score - sell_pressure

    if buy_score < sell_pressure:
        return None, 0, []

    base = (
        sell_pressure * 0.35 +
        buy_score * 0.35 +
        entry_score * 0.15 +
        expected_edge * 0.25
    )

    hist_adj, hist_notes = historical_adjustment(sell_symbol, buy_symbol)
    score = base + hist_adj

    return round(max(0, min(100, score)), 2), hist_adj, hist_notes

def get_regime_rules():
    regime = load_json(REGIME)
    name = regime.get("regime", "Neutral")
    score = float(regime.get("regime_score", 50) or 50)

    if name == "Risk-On" or score >= 68:
        return {
            "regime": name,
            "regime_score": score,
            "mode": "Aggressive Research",
            "rotate_threshold": 65,
            "watch_threshold": 60,
            "edge_required": 10,
            "score_adjustment": 3,
            "max_shadow_allocation": 0.35
        }

    if name == "Risk-Off" or score < 45:
        return {
            "regime": name,
            "regime_score": score,
            "mode": "Defensive Research",
            "rotate_threshold": 74,
            "watch_threshold": 68,
            "edge_required": 16,
            "score_adjustment": -6,
            "max_shadow_allocation": 0.05
        }

    return {
        "regime": name,
        "regime_score": score,
        "mode": "Selective Research",
        "rotate_threshold": 68,
        "watch_threshold": 62,
        "edge_required": 12,
        "score_adjustment": 0,
        "max_shadow_allocation": 0.15
    }

def action_label(rotation_score, sell_pressure, expected_edge, buy_score, hist_adj, regime_rules):
    rotate_threshold = regime_rules.get("rotate_threshold", 68)
    watch_threshold = regime_rules.get("watch_threshold", 62)
    edge_required = regime_rules.get("edge_required", 12)

    if hist_adj <= -8:
        return "⛔ DO NOT ROTATE"
    if rotation_score >= rotate_threshold and sell_pressure >= 55 and expected_edge >= edge_required and buy_score >= 70:
        return "🔴 ROTATE NOW"
    if rotation_score >= watch_threshold and sell_pressure >= 50 and expected_edge >= max(8, edge_required - 4):
        return "🟠 WATCH ROTATION"
    if rotation_score >= 55:
        return "🟡 LOW EDGE"
    return "⚪ IGNORE"

def confidence_label(rotation_score, expected_edge, hist_adj, regime_rules):
    if hist_adj <= -8:
        return "Low"

    mode = regime_rules.get("mode", "Selective Research")

    if "Aggressive" in mode:
        if rotation_score >= 68 and expected_edge >= 12 and hist_adj >= 0:
            return "High"
        if rotation_score >= 60 and expected_edge >= 8:
            return "Medium"

    if "Defensive" in mode:
        if rotation_score >= 76 and expected_edge >= 18 and hist_adj >= 3:
            return "High"
        if rotation_score >= 68 and expected_edge >= 14:
            return "Medium"
        return "Low"

    if rotation_score >= 70 and expected_edge >= 15 and hist_adj >= 0:
        return "High"
    if rotation_score >= 62 and expected_edge >= 8:
        return "Medium"
    return "Low"

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scanner = load_json(SCANNER)
    sell = load_json(SELL)
    regime_rules = get_regime_rules()

    trade_ready = scanner.get("trade_ready", [])
    sell_candidates = sell.get("sell_candidates", [])
    suggestions = []

    for s in sell_candidates:
        sell_pressure = float(s.get("sell_pressure", 0))
        if sell_pressure < 45:
            continue

        for b in trade_ready[:12]:
            sell_symbol = s.get("symbol")
            buy_symbol = b.get("symbol")

            if not sell_symbol or not buy_symbol or sell_symbol == buy_symbol:
                continue

            buy_score = float(b.get("final_score", 0))
            entry_score = float(b.get("entry_score", 50))
            expected_edge = round(buy_score - sell_pressure, 2)

            rotation_score, hist_adj, hist_notes = score_rotation(s, b)

            if rotation_score is None:
                continue

            rotation_score = round(max(0, min(100, rotation_score + regime_rules.get("score_adjustment", 0))), 2)

            action = action_label(rotation_score, sell_pressure, expected_edge, buy_score, hist_adj, regime_rules)
            confidence = confidence_label(rotation_score, expected_edge, hist_adj, regime_rules)

            suggestions.append({
                "timestamp": now,
                "sell_symbol": sell_symbol,
                "buy_symbol": buy_symbol,
                "rotation_score": rotation_score,
                "confidence": confidence,
                "historical_adjustment": hist_adj,
                "regime": regime_rules.get("regime"),
                "regime_mode": regime_rules.get("mode"),
                "regime_score": regime_rules.get("regime_score"),
                "action": action,
                "expected_edge": expected_edge,
                "sell_pressure": sell_pressure,
                "sell_verdict": s.get("verdict"),
                "buy_score": buy_score,
                "entry_score": entry_score,
                "entry_zone": b.get("entry_zone"),
                "buy_label": b.get("label"),
                "status": "research_only",
                "why": [
                    f"{sell_symbol} sell pressure is {sell_pressure}/100",
                    f"{buy_symbol} scanner score is {buy_score}",
                    f"Expected edge is {expected_edge}",
                    f"Historical adjustment is {hist_adj}",
                    f"Market regime is {regime_rules.get('regime')} ({regime_rules.get('mode')})",
                    f"{buy_symbol} entry zone: {b.get('entry_zone')}",
                ] + hist_notes,
            })

    suggestions = sorted(suggestions, key=lambda x: x["rotation_score"], reverse=True)
    top = suggestions[0] if suggestions else {}

    payload = {
        "updated_at": now,
        "version": "v3.2_regime_aware_research",
        "status": "research_only",
        "rotation_suggestions": suggestions[:25],
        "top_rotation": top,
        "regime_rules": regime_rules,
        "summary": {
            "sell_candidates_checked": len(sell_candidates),
            "trade_ready_checked": len(trade_ready),
            "rotations_found": len(suggestions),
            "rotate_now_count": len([x for x in suggestions if "ROTATE NOW" in x["action"]]),
            "watch_count": len([x for x in suggestions if "WATCH" in x["action"]]),
            "blocked_count": len([x for x in suggestions if "DO NOT ROTATE" in x["action"]]),
        },
        "notes": [
            "Rotation Engine v3.2 is research-only.",
            "Adds market regime awareness, confidence scoring, and historical performance adjustment.",
            "Does not place trades or touch the live bot.",
            "Use shadow results before any future bot integration."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))

    archive = OUT / f"rotation_engine_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive.write_text(json.dumps(payload, indent=2))

    with PERF_LOG.open("a") as f:
        for item in suggestions[:10]:
            f.write(json.dumps(item) + "\n")

    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
