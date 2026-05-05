#!/usr/bin/env python3
"""Patch the modular dashboard to show Shadow vs Live Comparison.

This edits only dashboard source files under new_ponder_site. It does not touch
bot.py, risk_manager.py, Alpaca behavior, order placement, or live trading logic.
The companion apply script copies dashboard-only files into new_ponder_site_dev.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "new_ponder_site" / "app.py"
RESEARCH = ROOT / "new_ponder_site" / "templates" / "research.html"


def patch_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"already patched: {label}")
        return text
    if old not in text:
        raise SystemExit(f"Could not patch {label}; expected anchor not found")
    print(f"patching: {label}")
    return text.replace(old, new, 1)


def patch_app() -> None:
    text = APP.read_text()
    text = patch_once(
        text,
        '    shadow_execution = load_json("shadow_execution_latest.json")\n    data = {',
        '    shadow_execution = load_json("shadow_execution_latest.json")\n    shadow_live_comparison = load_json("shadow_live_comparison_latest.json")\n    data = {',
        "load shadow_live_comparison",
    )
    text = patch_once(
        text,
        '        "shadow_execution": shadow_execution,\n        "shadow_execution_setups": build_shadow_setup_rows(shadow_execution),',
        '        "shadow_execution": shadow_execution,\n        "shadow_live_comparison": shadow_live_comparison,\n        "shadow_execution_setups": build_shadow_setup_rows(shadow_execution),',
        "research data shadow_live_comparison",
    )
    text = patch_once(
        text,
        '@app.route("/api/shadow-execution")\ndef api_shadow_execution():\n    return safe_json_response(load_json("shadow_execution_latest.json"))\n',
        '@app.route("/api/shadow-execution")\ndef api_shadow_execution():\n    return safe_json_response(load_json("shadow_execution_latest.json"))\n\n@app.route("/api/shadow-live-comparison")\ndef api_shadow_live_comparison():\n    return safe_json_response(load_json("shadow_live_comparison_latest.json"))\n',
        "api shadow-live-comparison",
    )
    APP.write_text(text)


def patch_research() -> None:
    text = RESEARCH.read_text()
    text = patch_once(
        text,
        '{% set shadow_execution = data.get("shadow_execution", {}) %}\n{% set shadow_execution_setups = data.get("shadow_execution_setups", []) %}',
        '{% set shadow_execution = data.get("shadow_execution", {}) %}\n{% set shadow_live_comparison = data.get("shadow_live_comparison", {}) %}\n{% set shadow_execution_setups = data.get("shadow_execution_setups", []) %}',
        "template variable shadow_live_comparison",
    )
    text = patch_once(
        text,
        '<button onclick="showTab(\'strategy\')">Strategy</button>\n  <button onclick="showTab(\'future\')">Future Labs</button>',
        '<button onclick="showTab(\'strategy\')">Strategy</button>\n  <button onclick="showTab(\'shadow-live\')">Shadow vs Live</button>\n  <button onclick="showTab(\'future\')">Future Labs</button>',
        "shadow vs live tab button",
    )

    panel = r'''
<section id="tab-shadow-live" class="tab card" style="display:none">
  <h2>Shadow vs Live Comparison</h2>
  <p class="muted"><strong>SHADOW ONLY / READ ONLY / NO LIVE TRADING CHANGES.</strong> This compares actual bot trades against shadow opportunities for learning only.</p>

  {% set sl_summary = shadow_live_comparison.get("summary", {}) %}
  {% set sl_quality = shadow_live_comparison.get("data_quality", {}) %}
  {% set sl_filter = shadow_live_comparison.get("filter_diagnostics", {}) %}

  {% if shadow_live_comparison %}
    <div class="grid">
      <div class="card mini"><h3>Live Trades</h3><div class="big">{{ sl_summary.get("live_trades_count", 0) }}</div></div>
      <div class="card mini"><h3>Shadow Opportunities</h3><div class="big">{{ sl_summary.get("shadow_opportunities_count", 0) }}</div></div>
      <div class="card mini"><h3>Missed Winners</h3><div class="big warnText">{{ sl_summary.get("missed_winners_count", 0) }}</div></div>
      <div class="card mini"><h3>Bad Live Trades</h3><div class="big riskText">{{ sl_summary.get("bad_live_trade_count", 0) }}</div></div>
      <div class="card mini"><h3>Opportunity Cost</h3><div class="big">{{ sl_summary.get("opportunity_cost_estimate_pct", "not ready") }}</div></div>
      <div class="card mini"><h3>Confidence</h3><div class="big small-big">{{ sl_summary.get("confidence", sl_quality.get("confidence", "low")) }}</div></div>
    </div>

    <div class="research-statusbar">
      <div><span class="status-dot warn"></span><strong>Research only - do not optimize live trading from this alone.</strong></div>
      <span>{{ sl_summary.get("sample_label", sl_quality.get("sample_label", "informational_only")) }}</span>
      <span>Updated: {{ shadow_live_comparison.get("updated_at", shadow_live_comparison.get("generated_at", "unknown")) }}</span>
    </div>

    <h3>Diagnostics</h3>
    <div class="grid">
      <div class="card mini"><h3>Over-filtering?</h3><div class="big small-big">{{ sl_filter.get("possible_over_filtering", false) }}</div></div>
      <div class="card mini"><h3>Under-filtering?</h3><div class="big small-big">{{ sl_filter.get("possible_under_filtering", false) }}</div></div>
    </div>
    <ul>
      {% for note in sl_filter.get("notes", []) %}<li>{{ note }}</li>{% else %}<li>No diagnostics yet.</li>{% endfor %}
    </ul>

    <h3>Research-Only Recommendations</h3>
    <table>
      <thead><tr><th>Message</th><th>Why</th><th>Sample Size</th><th>Confidence</th><th>Basis</th></tr></thead>
      <tbody>
      {% for rec in shadow_live_comparison.get("recommendations", []) %}
        <tr>
          <td><strong>{{ rec.get("message") }}</strong></td>
          <td>{{ rec.get("why") }}</td>
          <td>{{ rec.get("sample_size") }}</td>
          <td>{{ rec.get("confidence") }}</td>
          <td>{{ rec.get("basis") }}</td>
        </tr>
      {% else %}<tr><td colspan="5">No recommendations yet.</td></tr>{% endfor %}
      </tbody>
    </table>

    <h3>Missed Winners</h3>
    <table>
      <thead><tr><th>Symbol</th><th>Setup</th><th>Score</th><th>Return %</th><th>Outcome</th><th>Source</th><th>Reason</th></tr></thead>
      <tbody>
      {% for row in shadow_live_comparison.get("missed_winners", [])[:15] %}
        <tr>
          <td><strong>{{ row.get("symbol") }}</strong></td>
          <td>{{ row.get("setup_type") }}</td>
          <td>{{ row.get("score") }}</td>
          <td>{{ row.get("return_pct") }}</td>
          <td>{{ row.get("outcome") }}</td>
          <td>{{ row.get("source") or row.get("source_file") }}</td>
          <td>{{ row.get("reason") }}</td>
        </tr>
      {% else %}<tr><td colspan="7">No missed winners identified yet.</td></tr>{% endfor %}
      </tbody>
    </table>

    <h3>Bad Live Trades</h3>
    <table>
      <thead><tr><th>Symbol</th><th>Setup</th><th>Return %</th><th>Outcome</th><th>Timestamp</th></tr></thead>
      <tbody>
      {% for row in shadow_live_comparison.get("bad_live_trades", [])[:15] %}
        <tr>
          <td><strong>{{ row.get("symbol") }}</strong></td>
          <td>{{ row.get("setup_type") }}</td>
          <td>{{ row.get("return_pct") }}</td>
          <td>{{ row.get("outcome") }}</td>
          <td>{{ row.get("timestamp") }}</td>
        </tr>
      {% else %}<tr><td colspan="5">No bad live trades identified yet.</td></tr>{% endfor %}
      </tbody>
    </table>

    <h3>Best Missed Setup Types</h3>
    <table>
      <thead><tr><th>Setup</th><th>Samples</th><th>Winner Count</th><th>Win Rate</th><th>Avg Return %</th><th>Confidence</th><th>Basis</th></tr></thead>
      <tbody>
      {% for row in shadow_live_comparison.get("best_missed_setup_types", [])[:10] %}
        <tr>
          <td><strong>{{ row.get("setup_type") }}</strong></td>
          <td>{{ row.get("sample_size") }}</td>
          <td>{{ row.get("winner_count") }}</td>
          <td>{{ row.get("win_rate") }}</td>
          <td>{{ row.get("avg_return_pct") }}</td>
          <td>{{ row.get("confidence") }}</td>
          <td>{{ row.get("basis") }}</td>
        </tr>
      {% else %}<tr><td colspan="7">No missed setup ranking yet.</td></tr>{% endfor %}
      </tbody>
    </table>

    <details><summary>Raw Shadow vs Live JSON</summary><pre>{{ shadow_live_comparison | tojson(indent=2) }}</pre></details>
  {% else %}
    <div class="empty-state">Shadow vs Live comparison data is not available yet. Expected static/research/shadow_live_comparison_latest.json.</div>
  {% endif %}
</section>
'''
    text = patch_once(
        text,
        '\n<section id="tab-future" class="tab card" style="display:none">',
        '\n' + panel + '\n<section id="tab-future" class="tab card" style="display:none">',
        "shadow vs live panel",
    )
    RESEARCH.write_text(text)


def main() -> None:
    patch_app()
    patch_research()
    print("Shadow vs Live dashboard patch applied to new_ponder_site source only.")


if __name__ == "__main__":
    main()
