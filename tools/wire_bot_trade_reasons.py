#!/usr/bin/env python3
"""Safely wire richer trade reasons into bot.py trade memory calls.

This script is intentionally conservative:
- It does not change order submission logic.
- It does not change risk checks or scoring math.
- It only enriches record_trade(...) calls and the buy(...) function signature.
- It is idempotent enough to avoid repeat patching when run more than once.
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
        raise SystemExit("Run this from the repo root: ~/trading-bot")

    text = BOT.read_text()

    # Add a tiny helper for clean, consistent entry labels.
    helper = '''\n\ndef build_entry_reason(symbol, final_score, adaptive_reason, base_score=None):\n    parts = [\n        "qualified candidate passed risk checks",\n        f"symbol={symbol}",\n        f"final_score={final_score}",\n    ]\n    if base_score is not None:\n        parts.append(f"base_score={base_score}")\n    if adaptive_reason:\n        parts.append(f"adaptive={adaptive_reason}")\n    return " | ".join(str(p) for p in parts)\n'''
    if "def build_entry_reason(" not in text:
        text = replace_once(
            text,
            "\ndef get_momentum_score(symbol):",
            helper + "\ndef get_momentum_score(symbol):",
            "entry reason helper",
        )

    # Preserve old callers by defaulting entry_reason.
    text = replace_once(
        text,
        "\ndef buy(symbol, score):",
        "\ndef buy(symbol, score, entry_reason=None, setup=\"current_bot\"):",
        "buy signature",
    )

    # Add clean defaults inside buy after price is known.
    if "entry_reason = entry_reason or f\"current_bot entry | score={score}\"" not in text:
        text = replace_once(
            text,
            "    price = float(api.get_latest_trade(symbol).price)\n\n    atr = get_atr(symbol)",
            "    price = float(api.get_latest_trade(symbol).price)\n    entry_reason = entry_reason or f\"current_bot entry | score={score}\"\n\n    atr = get_atr(symbol)",
            "buy entry reason default",
        )

    # Enrich buy memory row without changing the order call.
    old_buy_record = '        record_trade(symbol, "buy", shares, price, reason="buy order submitted", score=score)'
    new_buy_record = (
        '        record_trade(\n'
        '            symbol,\n'
        '            "buy",\n'
        '            shares,\n'
        '            price,\n'
        '            reason=entry_reason,\n'
        '            score=score,\n'
        '            entry_reason=entry_reason,\n'
        '            strategy="current_bot",\n'
        '            setup=setup,\n'
        '        )'
    )
    text = replace_once(text, old_buy_record, new_buy_record, "buy record_trade enrichment")

    # Enrich sell memory row without changing the sell order call.
    old_sell_record = '        record_trade(symbol, "sell", qty, sell_price, reason=reason, score=None, pnl=pnl, pnl_pct=pnl_pct)'
    new_sell_record = (
        '        record_trade(\n'
        '            symbol,\n'
        '            "sell",\n'
        '            qty,\n'
        '            sell_price,\n'
        '            reason=reason,\n'
        '            score=None,\n'
        '            pnl=pnl,\n'
        '            pnl_pct=pnl_pct,\n'
        '            exit_reason=reason,\n'
        '            strategy="current_bot",\n'
        '            setup="current_bot",\n'
        '        )'
    )
    text = replace_once(text, old_sell_record, new_sell_record, "sell record_trade enrichment")

    # Pass the built reason into buy at the selected-candidate point.
    old_buy_call = (
        '        log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")\n'
        '        # LEARNING_SHADOW_BUY_DECISION\n'
        '        log(f"BUY DECISION | {symbol} | score={final_score} | reason=qualified candidate passed risk checks")\n'
        '        buy(symbol, final_score)'
    )
    new_buy_call = (
        '        entry_reason = build_entry_reason(symbol, final_score, adaptive_reason, base_score=score)\n'
        '        log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason=entry_reason)\n'
        '        # LEARNING_SHADOW_BUY_DECISION\n'
        '        log(f"BUY DECISION | {symbol} | score={final_score} | reason={entry_reason}")\n'
        '        buy(symbol, final_score, entry_reason=entry_reason, setup="current_bot")'
    )
    text = replace_once(text, old_buy_call, new_buy_call, "selected candidate buy reason")

    BOT.write_text(text)
    print("Bot trade reason wiring complete.")


if __name__ == "__main__":
    main()
