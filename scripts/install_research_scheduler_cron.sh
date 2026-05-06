#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ubuntu/trading-bot"
PYTHON_BIN="${APP_ROOT}/venv/bin/python3"
SCHEDULER="${APP_ROOT}/research_scheduler.py"
TMP_CRON="$(mktemp)"

if [ ! -f "${SCHEDULER}" ]; then
  echo "Missing scheduler: ${SCHEDULER}" >&2
  exit 1
fi

if [ ! -f "${PYTHON_BIN}" ]; then
  echo "Missing python binary: ${PYTHON_BIN}" >&2
  exit 1
fi

crontab -l 2>/dev/null | sed '/PONDER_RESEARCH_SCHEDULER_START/,/PONDER_RESEARCH_SCHEDULER_END/d' > "${TMP_CRON}" || true

cat >> "${TMP_CRON}" <<'EOF'
# PONDER_RESEARCH_SCHEDULER_START
# Research-only scheduler. Never places orders.

# Intraday refresh every 15 minutes during market hours (Arizona).
*/15 6-13 * * 1-5 cd /home/ubuntu/trading-bot && /home/ubuntu/trading-bot/venv/bin/python3 research_scheduler.py --mode intraday >> logs/research_scheduler_intraday.log 2>&1

# After-close evaluation + learning refresh.
35 13 * * 1-5 cd /home/ubuntu/trading-bot && /home/ubuntu/trading-bot/venv/bin/python3 research_scheduler.py --mode after-close >> logs/research_scheduler_after_close.log 2>&1

# Overnight refresh.
0 3 * * * cd /home/ubuntu/trading-bot && /home/ubuntu/trading-bot/venv/bin/python3 research_scheduler.py --mode overnight >> logs/research_scheduler_overnight.log 2>&1

# Weekly dry-run inspection report.
0 5 * * 0 cd /home/ubuntu/trading-bot && /home/ubuntu/trading-bot/venv/bin/python3 research_scheduler.py --mode inspect >> logs/research_scheduler_inspect.log 2>&1
# PONDER_RESEARCH_SCHEDULER_END
EOF

crontab "${TMP_CRON}"
rm -f "${TMP_CRON}"

mkdir -p "${APP_ROOT}/logs/research_scheduler"

printf '\nInstalled research scheduler cron entries.\n\n'
crontab -l | sed -n '/PONDER_RESEARCH_SCHEDULER_START/,/PONDER_RESEARCH_SCHEDULER_END/p'

printf '\nSafety:\n'
printf '%s\n' ' - research-only'
printf '%s\n' ' - does not import bot.py'
printf '%s\n' ' - does not place orders'
printf '%s\n' ' - only refreshes research/dashboard intelligence feeds'
