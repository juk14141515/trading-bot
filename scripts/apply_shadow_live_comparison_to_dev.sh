#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ubuntu/trading-bot"
DEV_DIR="${APP_ROOT}/new_ponder_site_dev"
BACKUP_ROOT="${APP_ROOT}/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/dev-shadow-live-${STAMP}"

cd "${APP_ROOT}"

if [ ! -d "${DEV_DIR}" ]; then
  echo "DEV dashboard directory not found: ${DEV_DIR}" >&2
  exit 1
fi

echo "Backing up DEV dashboard files to ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/templates"
cp "${DEV_DIR}/app.py" "${BACKUP_DIR}/app.py"
cp "${DEV_DIR}/templates/research.html" "${BACKUP_DIR}/templates/research.html"
cp "${DEV_DIR}/static/style.css" "${BACKUP_DIR}/style.css" || true

echo "Patching source dashboard (new_ponder_site)"
python3 scripts/patch_shadow_live_dashboard.py

echo "Applying patched dashboard to DEV only"
cp "new_ponder_site/app.py" "${DEV_DIR}/app.py"
cp "new_ponder_site/templates/research.html" "${DEV_DIR}/templates/research.html"
cp "new_ponder_site/static/style.css" "${DEV_DIR}/static/style.css" || true

echo "Validating DEV dashboard syntax"
python3 -m py_compile "${DEV_DIR}/app.py"

echo "Restarting DEV dashboard only"
sudo systemctl restart tradebot-dashboard-dev.service
sleep 2
sudo systemctl status tradebot-dashboard-dev --no-pager || true
curl -I http://127.0.0.1:5050 || true

echo "Applied to DEV only. LIVE dashboard, bot.py, trading logic, .env, and Cloudflare were not touched."
