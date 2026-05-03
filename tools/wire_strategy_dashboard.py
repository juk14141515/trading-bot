#!/usr/bin/env python3
"""Safely wire strategy intelligence feeds into the research dashboard.

Idempotent: running this more than once should not duplicate fields/tabs.
It edits only:
- new_ponder_site/app.py
- new_ponder_site/templates/research.html
"""

from __future__ import annotations

from pathlib import Path

APP = Path("new_ponder_site/app.py")
RESEARCH = Path("new_ponder_site/templates/research.html")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Could not find insertion point for {label}")
    return text.replace(old, new, 1)


def clean_duplicate_dashboard_keys(text: str) -> str:
    duplicate = (
        '        "strategy_backtest": strategy_backtest,\n'
        '        "forward_simulations": forward_simulations,\n'
        '        "strategy_backtest": strategy_backtest,\n'
        '        "forward_simulations": forward_simulations,\n'
    )
    single = (
        '        "strategy_backtest": strategy_backtest,\n'
        '        "forward_simulations": forward_simulations,\n'
    )
    while duplicate in text:
        text = text.replace(duplicate, single)
    return text


def patch_app() -> None:
    text = APP.read_text()
    text = clean_duplicate_dashboard_keys(text)

    text = replace_once(
        text,
        '    performance = load_json("rotation_performance_latest.json")\n    bot = load_root_json("bot_status.json")',
        '    performance = load_json("rotation_performance_latest.json")\n'
        '    strategy_backtest = load_json("current_strategy_backtest_latest.json")\n'
        '    forward_simulations = load_json("forward_setup_simulations_latest.json")\n'
        '    bot = load_root_json("bot_status.json")',
        "dashboard strategy feed variables",
    )

    text = replace_once(
        text,
        '        "profit_ops": profit_ops,\n        "capital_history": load_capital_history(),',
        '        "profit_ops": profit_ops,\n'
        '        "capital_history": load_capital_history(),\n'
        '        "strategy_backtest": strategy_backtest,\n'
        '        "forward_simulations": forward_simulations,',
        "dashboard strategy data keys",
    )
    text = clean_duplicate_dashboard_keys(text)

    text = replace_once(
        text,
        '            "performance": performance,\n        }),',
        '            "performance": performance,\n'
        '            "strategy_backtest": strategy_backtest,\n'
        '            "forward_simulations": forward_simulations,\n'
        '        }),',
        "module health strategy feeds",
    )

    text = replace_once(
        text,
        '        "module_health": data.get("module_health"),\n        "roadmap": build_feature_roadmap(),',
        '        "module_health": data.get("module_health"),\n'
        '        "strategy_backtest": data.get("strategy_backtest"),\n'
        '        "forward_simulations": data.get("forward_simulations"),\n'
        '        "roadmap": build_feature_roadmap(),',
        "snapshot strategy feeds",
    )

    text = replace_once(
        text,
        '        "regime": load_json("market_regime_filter_latest.json"),\n    }',
        '        "regime": load_json("market_regime_filter_latest.json"),\n'
        '        "strategy_backtest": load_json("current_strategy_backtest_latest.json"),\n'
        '        "forward_simulations": load_json("forward_setup_simulations_latest.json"),\n'
        '    }',
        "research route strategy feeds",
    )

    APP.write_text(text)


def patch_research_template() -> None:
    text = RESEARCH.read_text()

    text = replace_once(
        text,
        '{% set shadow = data.get("shadow", {}) %}',
        '{% set shadow = data.get("shadow", {}) %}\n'
        '{% set strategy_backtest = data.get("strategy_backtest", {}) %}\n'
        '{% set forward_simulations = data.get("forward_simulations", {}) %}',
        "strategy template variables",
    )

    text = replace_once(
        text,
        '  <button onclick="showTab(\'shadow\')">Shadow</button>\n  <button onclick="showTab(\'future\')">Future Labs</button>',
        '  <button onclick="showTab(\'shadow\')">Shadow</button>\n'
        '  <button onclick="showTab(\'strategy\')">Strategy</button>\n'
        '  <button onclick="showTab(\'future\')">Future Labs</button>',
        "strategy tab button",
    )

    if 'id="tab-strategy"' not in text:
        strategy_section = r'''
<section id="tab-strategy" class="tab card" style="display:none">
  <h2>Strategy Intelligence</h2>
  <p class="muted">Research-only strategy learning. Metrics stay marked as insufficient data until real outcomes exist.</p>

  {% set backtest_summary = strategy_backtest.get("summary", {}) %}
  {% set forward_summary = forward_simulations.get("summary", {}) %}

  <div class="grid">
    <div class="card mini">
      <h3>Backtest Status</h3>
      <div class="big small-big">{{ strategy_backtest.get("status", "missing") }}</div>
      <p>{{ backtest_summary.get("message", "Uses closed trade memory when available.") }}</p>
    </div>
    <div class="card mini">
      <h3>Closed Samples</h3>
      <div class="big">{{ backtest_summary.get("sample_size", 0) }}</div>
      <p>Real closed trades with PnL.</p>
    </div>
    <div class="card mini">
      <h3>Current Bot Win Rate</h3>
      <div class="big">
        {% if backtest_summary.get("win_rate") is not none %}
          {{ backtest_summary.get("win_rate") }}%
        {% else %}
          No evaluated trades yet
        {% endif %}
      </div>
      <p>Never inferred from fake data.</p>
    </div>
    <div class="card mini">
      <h3>Forward Status</h3>
      <div class="big small-big">{{ forward_simulations.get("status", "missing") }}</div>
      <p>{{ forward_summary.get("message", "Waiting for evaluated forward outcomes.") }}</p>
    </div>
  </div>

  <h3>Setup Comparison</h3>
  <table>
    <thead><tr><th>Setup</th><th>Status</th><th>Samples</th><th>Win Rate</th><th>Avg Return</th><th>Outcome</th></tr></thead>
    <tbody>
      {% for setup in strategy_backtest.get("setups", []) %}
        <tr>
          <td><strong>{{ setup.get("setup", "unknown") }}</strong></td>
          <td>{{ setup.get("status", "insufficient_data") }}</td>
          <td>{{ setup.get("sample_size", 0) }}</td>
          <td>{% if setup.get("win_rate") is not none %}{{ setup.get("win_rate") }}%{% else %}No evaluated trades yet{% endif %}</td>
          <td>{% if setup.get("avg_return_pct") is not none %}{{ setup.get("avg_return_pct") }}%{% else %}No evaluated trades yet{% endif %}</td>
          <td>{{ setup.get("outcome", "insufficient data") }}</td>
        </tr>
      {% else %}
        <tr><td colspan="6">No setup data yet.</td></tr>
      {% endfor %}
    </tbody>
  </table>

  <h3>Forward Simulation Summary</h3>
  <div class="grid">
    <div class="card mini"><h3>Evaluated</h3><div class="big">{{ forward_summary.get("evaluated", 0) }}</div></div>
    <div class="card mini"><h3>Pending</h3><div class="big">{{ forward_summary.get("pending", 0) }}</div></div>
    <div class="card mini"><h3>Scanner Candidates</h3><div class="big">{{ forward_summary.get("scanner_candidates_available", 0) }}</div></div>
  </div>

  <details><summary>Raw Strategy Backtest</summary><pre>{{ strategy_backtest | tojson(indent=2) }}</pre></details>
  <details><summary>Raw Forward Simulations</summary><pre>{{ forward_simulations | tojson(indent=2) }}</pre></details>
</section>

'''
        text = text.replace(
            '<section id="tab-future" class="tab card" style="display:none">',
            strategy_section + '<section id="tab-future" class="tab card" style="display:none">',
            1,
        )

    RESEARCH.write_text(text)


def main() -> None:
    if not APP.exists() or not RESEARCH.exists():
        raise SystemExit("Run this from the repo root: ~/trading-bot")
    patch_app()
    patch_research_template()
    print("Strategy dashboard wiring complete.")


if __name__ == "__main__":
    main()
