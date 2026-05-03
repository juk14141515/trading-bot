import json
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd

OUT = Path("static/research")
LOG = OUT / "rotation_suggestions_log.jsonl"
OVERNIGHT = OUT / "overnight_brief_latest.json"

DEST = OUT / "rotation_performance_latest.json"
ARCHIVE = OUT / "rotation_performance_v2_history.jsonl"

HORIZONS = {
    "30m": 30,
    "60m": 60,
    "120m": 120,
}

def now_dt():
    return datetime.now()

def parse_time(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def load_logged(limit=500):
    if not LOG.exists():
        return []

    rows = []
    for line in LOG.read_text().splitlines()[-limit:]:
        try:
            r = json.loads(line)
            if r.get("sell_symbol") and r.get("buy_symbol") and r.get("timestamp"):
                rows.append(r)
        except Exception:
            pass
    return rows

def dedupe_signals(rows):
    seen = set()
    clean = []

    for r in rows:
        ts = parse_time(r.get("timestamp", ""))
        if not ts:
            continue

        bucket = ts.strftime("%Y-%m-%d %H")
        key = f"{r.get('sell_symbol')}->{r.get('buy_symbol')}::{bucket}"

        if key in seen:
            continue

        seen.add(key)
        clean.append(r)

    return clean

def get_price_change_since(symbol, signal_time, horizon_minutes):
    try:
        end_time = signal_time + timedelta(minutes=horizon_minutes)
        if now_dt() < end_time:
            return None, "not_ready"

        df = yf.download(
            symbol,
            period="5d",
            interval="5m",
            progress=False,
            auto_adjust=True
        )

        if df.empty or len(df) < 5:
            return None, "no_data"

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df.reset_index()

        time_col = None
        for c in df.columns:
            if "Datetime" in str(c) or "Date" in str(c):
                time_col = c
                break

        if time_col is None or "Close" not in df.columns:
            return None, "bad_columns"

        df[time_col] = pd.to_datetime(df[time_col]).dt.tz_localize(None)

        start_rows = df[df[time_col] >= signal_time]
        end_rows = df[df[time_col] >= end_time]

        if start_rows.empty or end_rows.empty:
            return None, "outside_data_window"

        start_price = float(start_rows.iloc[0]["Close"])
        end_price = float(end_rows.iloc[0]["Close"])

        if start_price <= 0:
            return None, "bad_start_price"

        change = round((end_price - start_price) / start_price * 100, 2)
        return change, "ok"

    except Exception as e:
        return None, f"error:{str(e)[:80]}"

def outcome_label(alpha):
    if alpha is None:
        return "pending"
    if alpha > 0.75:
        return "✅ Strong Help"
    if alpha > 0.25:
        return "✅ Helped"
    if alpha < -0.75:
        return "❌ Strong Hurt"
    if alpha < -0.25:
        return "❌ Hurt"
    return "➖ Neutral"

def regime_snapshot():
    o = load_json(OVERNIGHT)
    return {
        "market_label": o.get("market_label"),
        "risk_score": o.get("risk_score"),
        "news_impact": o.get("news_impact"),
        "top_strength": [x.get("symbol") for x in o.get("top_strength", [])[:5]],
        "top_weakness": [x.get("symbol") for x in o.get("top_weakness", [])[:5]],
        "notes": o.get("notes", [])[:3],
    }

def summarize(evaluations):
    finished = [e for e in evaluations if e.get("status") == "evaluated"]

    by_horizon = {}
    for h in HORIZONS:
        rows = [e for e in finished if e.get("horizon") == h]
        helped = len([x for x in rows if "Help" in x.get("result", "")])
        hurt = len([x for x in rows if "Hurt" in x.get("result", "")])
        neutral = len([x for x in rows if "Neutral" in x.get("result", "")])
        total = len(rows)

        by_horizon[h] = {
            "evaluated": total,
            "helped": helped,
            "hurt": hurt,
            "neutral": neutral,
            "win_rate": round(helped / total * 100, 2) if total else 0,
            "avg_alpha_pct": round(sum(x.get("rotation_alpha_pct", 0) for x in rows) / total, 2) if total else 0,
        }

    pair_stats = {}
    buy_stats = {}
    sell_stats = {}

    for e in finished:
        pair = f"{e.get('sell_symbol')}->{e.get('buy_symbol')}"
        buy = e.get("buy_symbol")
        sell = e.get("sell_symbol")

        for store, key in [(pair_stats, pair), (buy_stats, buy), (sell_stats, sell)]:
            if not key:
                continue
            store.setdefault(key, {"count": 0, "helped": 0, "hurt": 0, "neutral": 0, "alpha_sum": 0})
            store[key]["count"] += 1
            store[key]["alpha_sum"] += e.get("rotation_alpha_pct", 0)

            result = e.get("result", "")
            if "Help" in result:
                store[key]["helped"] += 1
            elif "Hurt" in result:
                store[key]["hurt"] += 1
            else:
                store[key]["neutral"] += 1

    def finalize_stats(store):
        final = []
        for key, v in store.items():
            count = v["count"]
            final.append({
                "key": key,
                "count": count,
                "helped": v["helped"],
                "hurt": v["hurt"],
                "neutral": v["neutral"],
                "win_rate": round(v["helped"] / count * 100, 2) if count else 0,
                "avg_alpha_pct": round(v["alpha_sum"] / count, 2) if count else 0,
            })
        return sorted(final, key=lambda x: (x["avg_alpha_pct"], x["win_rate"], x["count"]), reverse=True)

    primary = by_horizon.get("60m", {})
    return {
        "overall": {
            "evaluated": primary.get("evaluated", 0),
            "helped": primary.get("helped", 0),
            "hurt": primary.get("hurt", 0),
            "neutral": primary.get("neutral", 0),
            "win_rate": primary.get("win_rate", 0),
            "avg_alpha_pct": primary.get("avg_alpha_pct", 0),
            "primary_horizon": "60m",
        },
        "by_horizon": by_horizon,
        "best_pairs": finalize_stats(pair_stats)[:10],
        "best_buy_targets": finalize_stats(buy_stats)[:10],
        "weakest_sell_sources": finalize_stats(sell_stats)[:10],
    }

def main():
    now = now_dt()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    raw = load_logged()
    clean = dedupe_signals(raw)
    regime = regime_snapshot()

    evaluations = []
    pending = 0

    for r in clean:
        signal_time = parse_time(r.get("timestamp", ""))
        if not signal_time:
            continue

        sell_symbol = r.get("sell_symbol")
        buy_symbol = r.get("buy_symbol")

        for horizon, minutes in HORIZONS.items():
            sell_change, sell_status = get_price_change_since(sell_symbol, signal_time, minutes)
            buy_change, buy_status = get_price_change_since(buy_symbol, signal_time, minutes)

            if sell_change is None or buy_change is None:
                pending += 1
                evaluations.append({
                    "signal_timestamp": r.get("timestamp"),
                    "evaluated_at": now_str,
                    "horizon": horizon,
                    "sell_symbol": sell_symbol,
                    "buy_symbol": buy_symbol,
                    "status": "pending",
                    "reason": f"sell:{sell_status}, buy:{buy_status}",
                    "action": r.get("action"),
                    "rotation_score": r.get("rotation_score"),
                    "confidence": r.get("confidence"),
                    "expected_edge": r.get("expected_edge"),
                })
                continue

            alpha = round(buy_change - sell_change, 2)

            evaluations.append({
                "signal_timestamp": r.get("timestamp"),
                "evaluated_at": now_str,
                "horizon": horizon,
                "sell_symbol": sell_symbol,
                "buy_symbol": buy_symbol,
                "status": "evaluated",
                "action": r.get("action"),
                "rotation_score": r.get("rotation_score"),
                "confidence": r.get("confidence"),
                "expected_edge": r.get("expected_edge"),
                "sell_change_pct": sell_change,
                "buy_change_pct": buy_change,
                "rotation_alpha_pct": alpha,
                "result": outcome_label(alpha),
                "market_regime": regime,
            })

    summary = summarize(evaluations)

    payload = {
        "updated_at": now_str,
        "version": "v2_multi_horizon_learning",
        "status": "research_only",
        "summary": {
            **summary["overall"],
            "signals_loaded": len(raw),
            "signals_after_dedupe": len(clean),
            "pending_evaluations": pending,
        },
        "by_horizon": summary["by_horizon"],
        "best_pairs": summary["best_pairs"],
        "best_buy_targets": summary["best_buy_targets"],
        "weakest_sell_sources": summary["weakest_sell_sources"],
        "evaluations": evaluations[-150:],
        "notes": [
            "Performance Tracker v2 dedupes repeated rotation signals by pair and hour.",
            "Primary scoreboard uses 60m results.",
            "30m, 60m, and 120m horizons are tracked separately.",
            "Market regime snapshots are stored with evaluated outcomes.",
            "Research-only. Does not place trades or modify bot behavior."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))

    with ARCHIVE.open("a") as f:
        f.write(json.dumps({
            "updated_at": now_str,
            "summary": payload["summary"],
            "by_horizon": payload["by_horizon"],
            "best_pairs": payload["best_pairs"][:5],
            "best_buy_targets": payload["best_buy_targets"][:5],
            "weakest_sell_sources": payload["weakest_sell_sources"][:5],
        }) + "\n")

    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
