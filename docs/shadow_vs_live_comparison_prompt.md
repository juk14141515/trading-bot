# Ponder Invest AI — Shadow vs Live Comparison Handoff Prompt

Use this prompt when continuing work in another GPT/Codex session.

---

Please inspect the current repository first before making any plan or code changes. Read the relevant files and current structure before assuming anything.

I am building an AI trading system called **Ponder Invest AI**.

## Current architecture

- Ubuntu VPS
- Python trading bot
- Alpaca paper trading
- yfinance/Finnhub data
- Flask + Gunicorn dashboard
- Separate DEV and LIVE dashboards
- Cron-based research automation

## Current state

- Live trading logic should **NOT** be changed.
- Everything new should stay **research-only / shadow-only**.
- Goal is to build a self-improving trading intelligence system before real automation.
- The system is currently in **data collection + validation phase**, not live optimization phase.

## Already built

1. Market scanner → `top_10_candidates_v2.json`
2. Shadow setup logger → logs opportunities without trading
3. Historical backfill → creates setup datasets across IPO, ETF, crypto, day trading, small-cap, large-cap pullback, gap, earnings
4. Setup outcome evaluator → labels winner/loser/flat/missed_opportunity/false_signal/early_exit/late_exit
5. Strategy researcher → finds thresholds, priority setups, deprioritized setups
6. Shadow execution engine → simulates which trades would pass strategy rules
7. Daytime shadow collector → runs during market hours and logs opportunities into `research_data/shadow_setups.csv`
8. DEV dashboard shows Shadow Execution Engine data

## Main next task

Build a **Shadow vs Live Comparison Engine**.

## Goals

- Compare actual bot trades vs shadow opportunities
- Identify missed winners
- Identify bad live trades
- Measure opportunity cost
- Detect over-filtering and under-filtering
- Compare live bot behavior against shadow strategy recommendations
- Output dashboard-ready JSON into `static/research/`

## Data sources to inspect/use

- `trade_history.csv`
- `research_data/shadow_setups.csv`
- `static/research/shadow_execution_latest.json`
- `static/research/setup_outcomes_latest.json`
- `top_10_candidates_v2.json`
- Any existing dashboard/research modules that already read JSON from `static/research/`

## Expected output file

- `static/research/shadow_live_comparison_latest.json`

## Suggested metrics

- live trades count
- shadow opportunities count
- missed winners
- missed opportunity rate
- bad live trade count
- average live return
- average shadow return
- best missed setup types
- worst live setup types
- opportunity cost estimate
- over-filtering signals
- under-filtering signals
- recommendations clearly marked research-only

## Execution constraints — very important

1. This system is already large and modular. Do **not** rewrite existing files unless absolutely necessary.
2. Prefer new files, isolated modules, and minimal integration points.
3. Avoid large refactors.
4. Do not touch `bot.py` execution behavior.
5. Do not change order placement, risk manager behavior, Alpaca trading behavior, or capital allocation behavior.
6. All outputs must be backward compatible and safe if data is missing.
7. Every module must fail gracefully and log/return errors instead of crashing cron jobs.
8. Do not assume perfect data. Handle missing fields, NaNs, partial rows, empty files, and old schemas safely.
9. Keep everything research-only: no orders, no live execution, no live trading changes.
10. Avoid adding random new modules unless they connect existing layers.

## Data reality constraints

- Shadow data is incomplete and growing over time.
- Some setups will not have full 1h/1d/3d/5d outcomes yet.
- Trade history is smaller than shadow data.
- Backfill data may not perfectly match live conditions.
- Separate historical/backfill evidence from real-time/live-shadow evidence when possible.
- Do not over-weight backfill vs real signals without labeling it clearly.

## Anti-overfitting rules

Do **not** optimize thresholds based on small sample sizes.

Suggested sample rules:

- fewer than 100 samples → informational only
- 100–300 samples → early signal
- 300+ samples → meaningful signal

Flag low sample sizes in all outputs.

## Decision output expectations

Every recommendation must answer:

- WHY this setup is good or bad
- WHAT data supports it
- SAMPLE SIZE used
- CONFIDENCE level: low / medium / high
- WHETHER it is based on live data, shadow data, historical backfill, or a mix

Do not return black-box metrics without explanations.

## System goal clarification

The goal is **not** to maximize win rate immediately.

The goal is to:

- identify repeatable edges
- understand opportunity cost
- improve decision quality over time
- reduce bad trades
- identify missed high-quality opportunities

Prefer stable, explainable signals over aggressive short-term optimization.

## Planned roadmap after Shadow vs Live Comparison

### Phase A — High-Frequency Learning Layer

- Improve day-trading research as a high-frequency learning source only
- Track 1h, 1d, 3d, 5d returns
- Measure false breakout rate
- Track fast momentum follow-through
- Keep day-trading research shadow-only
- Do not connect day-trading logic to live execution yet

### Phase B — Connect All Layers

Connect:

- daytime shadow collector
- historical backfill
- setup evaluator
- strategy researcher
- shadow execution engine
- shadow vs live comparison
- dashboard

Goal loop:

`Collect opportunities → evaluate outcomes → rank setups → simulate decisions → compare vs live → recommend improvements`

### Phase C — Dashboard UI Improvements

Update DEV dashboard to clearly show:

- Shadow Execution Engine
- Shadow vs Live Comparison
- Missed opportunities
- Best setup types
- Worst setup types
- Opportunity cost
- Why a trade was accepted/rejected
- Data freshness
- Research-only warnings

UI should be clean, card/table based, consistent with current Ponder Invest AI design, easy to understand, not cluttered, and clearly labeled:

`SHADOW ONLY / READ ONLY / NO LIVE TRADING CHANGES`

### Phase D — Promote Dashboard DEV → LIVE

Only after DEV dashboard works:

- promote dashboard changes to LIVE dashboard
- dashboard/UI only
- do not change bot trading logic
- do not change order execution
- do not change risk manager
- do not change Alpaca trading behavior

Safe rollout:

1. Verify DEV `/research`
2. Check JSON loads
3. Check service health
4. Back up live dashboard files
5. Copy dashboard-only changes
6. Restart only dashboard service
7. Confirm Cloudflare/live dashboard works

### Phase E — Later Optimization

Only after enough real shadow/live comparison data:

- adaptive thresholds
- setup weighting
- capital allocation recommendations
- missed-opportunity ranking
- regime-aware thresholds
- paper-test changes before any live automation

## Future interface requirement

Eventually add a modular interface for different website layouts/templates for different use cases. Keep JSON structures clean and reusable so multiple dashboard layouts can consume the same research outputs.

## Return requested

After inspecting the repo, return:

- current repo findings relevant to this task
- minimal modular Python implementation plan
- file names to create/update
- dashboard JSON output schema
- cron placement
- DEV dashboard UI plan
- safety checks before dashboard promotion to LIVE
- risks/unknowns found in the current repo

Do not begin risky edits until you have inspected the repo and identified the minimal safe integration path.
