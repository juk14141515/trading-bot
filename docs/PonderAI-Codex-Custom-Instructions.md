# Ponder Invest AI - Codex Custom Instructions

Use this document when handing the Ponder Invest AI project to Codex, Codex Cloud, ChatGPT, or another coding assistant.

## Project Identity

Project name: Ponder Invest AI

Purpose: A personal research-first AI trading bot and dashboard named after Ponder, the user's dog. The dashboard should feel professional, black/dark, clean, modular, colorblind accessible, and easier to upgrade than the older live dashboard.

Current priority: Improve the new modular Flask dashboard while keeping trading execution safe. Do not connect new research modules to live buy/sell automation unless explicitly requested.

Core rule: Watch first. Explain clearly. Protect capital. Automate only after evidence.

## Current Architecture

Server:

```text
Host: ubuntu@132.226.102.56
Project root: /home/ubuntu/trading-bot
New dashboard app: /home/ubuntu/trading-bot/new_ponder_site/app.py
New dashboard port: 5050
Old dashboard/root app: /home/ubuntu/trading-bot/web_dashboard.py
Bot root: /home/ubuntu/trading-bot
Research JSON directory: /home/ubuntu/trading-bot/static/research
```

Local Windows workspace used for patch files:

```text
C:\Users\zjuli\Documents\Codex\2026-05-02\files-mentioned-by-the-user-chatgpt
```

SSH key path normally used:

```text
C:\Users\zjuli\.ssh\tradebot.key
```

Local browser tunnel URL:

```text
http://127.0.0.1:5050
```

## Access Commands

Start SSH tunnel from Windows PowerShell:

```powershell
ssh -i "$env:USERPROFILE\.ssh\tradebot.key" -L 5050:127.0.0.1:5050 ubuntu@132.226.102.56
```

Then open:

```text
http://127.0.0.1:5050
```

If deploying a patch archive from Windows:

```powershell
scp -i "$env:USERPROFILE\.ssh\tradebot.key" "C:\PATH\TO\PATCH.tar.gz" ubuntu@132.226.102.56:~/trading-bot/
```

On Ubuntu, apply patch safely:

```bash
cd ~/trading-bot
cp -a new_ponder_site new_ponder_site_backup_before_patch_$(date +%Y%m%d_%H%M%S)
tar -xzf PATCH_NAME.tar.gz
python3 -m py_compile new_ponder_site/app.py
source venv/bin/activate
python3 new_ponder_site/app.py
```

## Important Current New Dashboard Routes

```text
/login              Secure login page
/                   Main dashboard
/profit             New modular Profit Ops page
/profit-lab         New modular Profit Lab page
/research           Card-based research modules
/assistant          Ask Ponder assistant page
/learning           Learning / achievements / missions
/build-plan         Roadmap, guardrails, Codex Cloud handoff
/settings           Theme, accessibility, module health, tools
/history            Trade journal and logs
/debug-snapshot     Snapshot and handoff JSON
/api/dashboard-data Live dashboard JSON
/api/profit-ops     Profit Ops JSON
/api/snapshot       Handoff snapshot JSON
/logout             Clears session and returns to login
```

## Important Files

New modular dashboard:

```text
/home/ubuntu/trading-bot/new_ponder_site/app.py
/home/ubuntu/trading-bot/new_ponder_site/templates/base.html
/home/ubuntu/trading-bot/new_ponder_site/templates/dashboard.html
/home/ubuntu/trading-bot/new_ponder_site/templates/profit.html
/home/ubuntu/trading-bot/new_ponder_site/templates/profit_lab.html
/home/ubuntu/trading-bot/new_ponder_site/templates/history.html
/home/ubuntu/trading-bot/new_ponder_site/templates/research.html
/home/ubuntu/trading-bot/new_ponder_site/templates/assistant.html
/home/ubuntu/trading-bot/new_ponder_site/templates/learning.html
/home/ubuntu/trading-bot/new_ponder_site/templates/build_plan.html
/home/ubuntu/trading-bot/new_ponder_site/templates/settings.html
/home/ubuntu/trading-bot/new_ponder_site/templates/debug_snapshot.html
/home/ubuntu/trading-bot/new_ponder_site/static/style.css
/home/ubuntu/trading-bot/new_ponder_site/static/site/js/app.js
```

Dashboard data / analytics helpers:

```text
/home/ubuntu/trading-bot/profit_ops_analytics.py
/home/ubuntu/trading-bot/profit_ops_routes.py
/home/ubuntu/trading-bot/profit_lab_routes.py
/home/ubuntu/trading-bot/dashboard_safety_ui.py
```

Bot/runtime status:

```text
/home/ubuntu/trading-bot/bot.py
/home/ubuntu/trading-bot/risk_manager.py
/home/ubuntu/trading-bot/bot_status.json
/home/ubuntu/trading-bot/log.txt
/home/ubuntu/trading-bot/trade_history.csv
/home/ubuntu/trading-bot/equity_history.csv
```

Research data:

```text
/home/ubuntu/trading-bot/static/research/ai_summary_latest.json
/home/ubuntu/trading-bot/static/research/notifications_latest.json
/home/ubuntu/trading-bot/static/research/market_intelligence_latest.json
/home/ubuntu/trading-bot/static/research/overnight_brief_latest.json
/home/ubuntu/trading-bot/static/research/sell_intelligence_latest.json
/home/ubuntu/trading-bot/static/research/rotation_engine_latest.json
/home/ubuntu/trading-bot/static/research/rotation_performance_latest.json
/home/ubuntu/trading-bot/static/research/shadow_capital_allocator_latest.json
/home/ubuntu/trading-bot/static/research/capital_intelligence_latest.json
/home/ubuntu/trading-bot/static/research/capital_history.csv
/home/ubuntu/trading-bot/static/research/system_snapshot_latest.json
```

Environment/secrets:

```text
/home/ubuntu/trading-bot/.env
```

Never paste `.env`, API keys, private SSH keys, passwords, or Alpaca secrets into chat or GitHub.

Expected dashboard auth env vars:

```text
PONDER_DASHBOARD_USERNAME
PONDER_DASHBOARD_PASSWORD
PONDER_SECRET_KEY
```

## Current Bot Status Context

The bot is in learning/research mode. There are not enough real closed sells yet, so automation should remain conservative.

Known current data behavior:

```text
bot_status.json contains why_not_trading and last_skip_reason.
capital_intelligence_latest.json contains cash, buying_power, reserve_cash, deployable_cash, capital_used_pct, and P/L fields.
rotation_engine_latest.json contains research-only rotation suggestions.
sell_intelligence_latest.json contains sell pressure and top_exit_candidate.
shadow_capital_allocator_latest.json contains simulated allocation suggestions only.
ai_summary_latest.json contains plain-English summary and action_items.
```

## Guardrails

Do:

```text
Keep new dashboard work modular.
Prefer templates, helper functions, JSON-fed cards, and reusable CSS.
Use the existing new_ponder_site shell/sidebar across pages.
Keep visible pages consistent.
Keep settings browser-local unless server-side config is explicitly requested.
Add readable cards and charts before raw JSON dumps.
Keep research-only modules clearly labeled.
Add explanations in plain English for learning.
Use colorblind markers and not just red/green.
Back up before replacing files on the server.
Run python3 -m py_compile new_ponder_site/app.py after Python changes.
Run a JS syntax check after editing app.js when possible.
```

Do not:

```text
Do not rewrite the entire dashboard again unless explicitly requested.
Do not replace the new modular dashboard with the old inline Profit Ops UI.
Do not expose the dashboard publicly without auth.
Do not open port 5050 to everyone unless security is explicitly reviewed.
Do not modify live trading execution in bot.py unless explicitly requested.
Do not connect auto-rotation, auto-sell, or new labs to live orders yet.
Do not paste secrets into code, chat, or GitHub.
Do not rely only on color to communicate risk or P/L.
```

## Design Direction

Preferred look:

```text
Professional black/dark theme
Clean outlines
High contrast
Large click targets
Low-distraction hover states
Responsive sidebar that does not disappear
Consistent cards across all pages
Readable graphs with larger chart areas
Colorblind markers for up/down/risk states
Ponder-branded identity without making it childish
```

Ponder branding ideas:

```text
Use Ponder as the assistant/overseer.
Use phrases like Ponder Protocol, Ponder is watching, Ponder's readout.
Brand values: patience, discipline, capital protection, clear explanation.
Avoid clutter and gimmicks.
```

## Planned Feature Roadmap

Immediate dashboard features:

```text
Consistent modular UI across all pages
Live numbers without full page refresh
Equity curve and capital charts
Daily/week/all-time P/L display
Live positions
Candidate ranking and why
Why not trading panel
Module health
Copy Snapshot / Cloud Handoff
Research cards for AI Summary, Alerts, Market, Overnight, Sell, Rotation, Performance, Shadow
Settings that actually show active theme/accessibility/focus state
```

Next backend/research modules:

```text
Adaptive Capital Allocator v1
Unused Capital Optimizer
Sell Intelligence v2
Shadow Execution Tracker
Performance Tracker as a learning system
Dynamic score threshold
Opportunity threshold logic
Time-based exits
Capital rotation visibility
Learning mode performance
Daily auto-reflection
Weekly auto-optimization
```

Future research-only labs:

```text
Overnight / premarket edge
IPO research lab
Day trading research lab
Crypto / ETF / commodities research labs
Social trend scanner
Event / News Impact Layer
Strategy sandbox
Backtesting engine
Experiment tracker
```

Important: Future labs should collect data and show intelligence first. They should not be connected to live execution until separately proven.

## Codex Cloud Handoff

Codex Cloud cannot automatically inherit a local Codex Desktop chat. To continue on another device:

```text
1. Put the project in a private GitHub repo.
2. Open chatgpt.com/codex from the other device.
3. Connect/select the repo.
4. Start a new cloud task.
5. Paste this custom-instructions file.
6. Paste the dashboard Snapshot JSON from /debug-snapshot.
7. Ask for the next scoped change.
```

Suggested cloud task prompt:

```text
Continue work on Ponder Invest AI.

Use the attached custom instructions and current Snapshot JSON.

Priority:
Keep the new Flask dashboard modular and consistent. Do not change live trading logic. Add dashboard/UI/planning features only unless I explicitly ask for backend trading changes.

Current focus:
Improve dashboard consistency, Ponder branding, readable research cards, module health, live numbers, charts, snapshot handoff, and planned research-only modules.
```

## Useful Snapshot Commands

Create a bundle of the current site/routes for local Codex:

```bash
cd ~/trading-bot
tar --exclude='__pycache__' --exclude='*.log' -czf ponder-current-site-and-routes.tar.gz \
  new_ponder_site \
  profit_ops_routes.py \
  profit_lab_routes.py \
  profit_ops_analytics.py \
  dashboard_safety_ui.py \
  static/research \
  bot_status.json
```

Download from Windows PowerShell:

```powershell
scp -i "$env:USERPROFILE\.ssh\tradebot.key" ubuntu@132.226.102.56:~/trading-bot/ponder-current-site-and-routes.tar.gz "C:\Users\zjuli\Documents\Codex\2026-05-02\files-mentioned-by-the-user-chatgpt\"
```

Check bot status on Ubuntu:

```bash
cd ~/trading-bot
cat bot_status.json
tail -80 log.txt
```

Restart the bot service if needed:

```bash
sudo systemctl restart tradebot.service
sudo systemctl status tradebot.service
```

Restart the new development dashboard manually:

```bash
cd ~/trading-bot
source venv/bin/activate
python3 new_ponder_site/app.py
```

## Current Known UI Issues To Watch

```text
Long decimal values should be rounded in UI.
Any old inline Profit Ops pages should not appear inside the new app.
Sidebar should remain consistent across routes.
Settings should show active selections.
Snapshot copy may require HTTPS or localhost secure context; fallback copy code exists.
Research views should prioritize cards and tables over raw JSON.
Charts need mobile sizing checks.
```

## Security Notes

Preferred access while in development:

```text
Use SSH tunnel to 127.0.0.1:5050.
Keep login enabled.
Keep dashboard off public 0.0.0.0/0 exposure unless reviewed.
Use Cloudflare Access or a narrow IP allowlist if remote public access becomes necessary.
```

Never expose:

```text
.env
APCA_API_KEY_ID
APCA_API_SECRET_KEY
SSH private keys
Dashboard password
Webhook URLs
```

## Decision Standard

When uncertain, choose the option that:

```text
Keeps live trading safer.
Keeps the dashboard modular.
Makes the system easier to understand.
Improves future upgrade speed.
Avoids clutter.
Preserves research-only separation for now
```

