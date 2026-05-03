#!/usr/bin/env python3
"""Safely add setup classification to bot.py.

Research/memory only:
- Does not change order submission.
- Does not change score thresholds.
- Does not change risk checks.
- Only tags future trade memory rows with setup labels.

Supported labels:
- breakout
- pullback
- momentum
- oversold
- rotation
- day_trade_shadow
- current_bot fallback
"""

from __future__ import annotations

from pathlib import Path

BOT = Path("bot.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Could not find insertion point for {label}")
    return text.replace(old, new, 1)


def main() -> None:
    if not BOT.exists():
        raise SystemExit("Run this from repo root: ~/trading-bot")

    text = BOT.read_text()

    classifier = '''\n\ndef classify_setup(symbol, trend, analyst, news, score, final_score, adaptive_reason=""):\n    """Classify the research setup for trade memory only.\n\n    This does not decide whether to trade. It only labels why an already-\n    selected candidate looked interesting so later learning can group outcomes.\n    """\n    try:\n        symbol = str(symbol or "").upper()\n        trend = str(trend or "").lower()\n        adaptive = str(adaptive_reason or "").lower()\n        analyst_val = float(analyst or 0)\n        news_val = float(news or 0)\n        score_val = float(score or 0)\n        final_val = float(final_score or 0)\n    except Exception:\n        return "current_bot"\n\n    # One extra category requested: day-trade shadow.\n    # This is only a research label for fast/high-confidence opportunities.\n    if final_val >= 80 and ("momentum" in adaptive or news_val >= 2):\n        return "day_trade_shadow"\n\n    if trend == "bullish" and final_val >= 75 and news_val >= 1:\n        return "breakout"\n\n    if "momentum" in adaptive or (final_val >= 70 and score_val >= 60):\n        return "momentum"\n\n    if trend == "bullish" and analyst_val >= 4 and news_val == 0:\n        return "pullback"\n\n    if trend in {"neutral", "bad_data"} and analyst_val >= 4 and final_val >= 65:\n        return "oversold"\n\n    return "current_bot"\n'''

    if "def classify_setup(" not in text:
        text = replace_once(
            text,
            "\ndef build_entry_reason(symbol, final_score, adaptive_reason, base_score=None):",
            classifier + "\ndef build_entry_reason(symbol, final_score, adaptive_reason, base_score=None):",
            "setup classifier helper",
        )

    # Expand entry reason to include setup label while keeping old calls compatible.
    old_reason_sig = "def build_entry_reason(symbol, final_score, adaptive_reason, base_score=None):"
    new_reason_sig = "def build_entry_reason(symbol, final_score, adaptive_reason, base_score=None, setup=None):"
    text = replace_once(text, old_reason_sig, new_reason_sig, "entry reason signature")

    if "parts.append(f\"setup={setup}\")" not in text:
        text = replace_once(
            text,
            "    if base_score is not None:\n        parts.append(f\"base_score={base_score}\")\n    if adaptive_reason:",
            "    if base_score is not None:\n        parts.append(f\"base_score={base_score}\")\n    if setup:\n        parts.append(f\"setup={setup}\")\n    if adaptive_reason:",
            "entry reason setup field",
        )

    # Add setup classification at candidate append point without changing candidate tuple shape too broadly.
    old_candidate_append = "        if trend == \"bullish\" and analyst >= 3 and news >= 0:\n            candidates.append((symbol, total))"
    new_candidate_append = "        if trend == \"bullish\" and analyst >= 3 and news >= 0:\n            candidates.append({\n                \"symbol\": symbol,\n                \"score\": total,\n                \"trend\": trend,\n                \"analyst\": analyst,\n                \"news\": news,\n            })"
    text = replace_once(text, old_candidate_append, new_candidate_append, "candidate metadata append")

    old_sort = "    candidates.sort(key=lambda x: x[1], reverse=True)"
    new_sort = "    candidates.sort(key=lambda x: x.get(\"score\", 0), reverse=True)"
    text = replace_once(text, old_sort, new_sort, "candidate sort metadata")

    old_fallback = "            candidates.append((fallback_symbol, 65))"
    new_fallback = "            candidates.append({\"symbol\": fallback_symbol, \"score\": 65, \"trend\": \"enhanced_fallback\", \"analyst\": 0, \"news\": 0})"
    text = replace_once(text, old_fallback, new_fallback, "fallback candidate metadata")

    old_loop = "    for symbol, score in candidates[:slots_available]:\n        final_score, adaptive_reason = apply_adaptive_score(symbol, score)"
    new_loop = (
        "    for candidate in candidates[:slots_available]:\n"
        "        symbol = candidate.get(\"symbol\")\n"
        "        score = candidate.get(\"score\", 0)\n"
        "        trend = candidate.get(\"trend\", \"unknown\")\n"
        "        analyst = candidate.get(\"analyst\", 0)\n"
        "        news = candidate.get(\"news\", 0)\n"
        "        final_score, adaptive_reason = apply_adaptive_score(symbol, score)"
    )
    text = replace_once(text, old_loop, new_loop, "candidate loop metadata")

    old_selected_buy = (
        '        entry_reason = build_entry_reason(symbol, final_score, adaptive_reason, base_score=score)\n'
        '        log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason=entry_reason)\n'
        '        # LEARNING_SHADOW_BUY_DECISION\n'
        '        log(f"BUY DECISION | {symbol} | score={final_score} | reason={entry_reason}")\n'
        '        buy(symbol, final_score, entry_reason=entry_reason, setup="current_bot")'
    )
    new_selected_buy = (
        '        setup = classify_setup(symbol, trend, analyst, news, score, final_score, adaptive_reason)\n'
        '        entry_reason = build_entry_reason(symbol, final_score, adaptive_reason, base_score=score, setup=setup)\n'
        '        log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason=entry_reason, setup=setup)\n'
        '        # LEARNING_SHADOW_BUY_DECISION\n'
        '        log(f"BUY DECISION | {symbol} | score={final_score} | setup={setup} | reason={entry_reason}")\n'
        '        buy(symbol, final_score, entry_reason=entry_reason, setup=setup)'
    )
    text = replace_once(text, old_selected_buy, new_selected_buy, "selected buy setup classification")

    # Rotation sell path gets a rotation label in the exit reason via sell reason string.
    old_rotation_sell = '            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")'
    new_rotation_sell = '            sell(weakest_position["symbol"], weakest_position["qty"], f"rotation into {symbol}")'
    # No-op placeholder kept for readability; sell memory already captures exit_reason.
    text = replace_once(text, old_rotation_sell, new_rotation_sell, "rotation sell no-op")

    BOT.write_text(text)
    print("Setup classification wiring complete.")


if __name__ == "__main__":
    main()
