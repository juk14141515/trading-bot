#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ubuntu/trading-bot"
DEV_DIR="${APP_ROOT}/new_ponder_site_dev"
BACKUP_ROOT="${APP_ROOT}/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/dev-decision-interface-${STAMP}"

cd "${APP_ROOT}"

if [ ! -d "${DEV_DIR}" ]; then
  echo "DEV dashboard directory not found: ${DEV_DIR}" >&2
  exit 1
fi

echo "Backing up DEV dashboard files to ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/templates" "${BACKUP_DIR}/static/site/js"
cp "${DEV_DIR}/app.py" "${BACKUP_DIR}/app.py"
cp "${DEV_DIR}/templates/base.html" "${BACKUP_DIR}/templates/base.html"
cp "${DEV_DIR}/templates/research.html" "${BACKUP_DIR}/templates/research.html"
cp "${DEV_DIR}/templates/settings.html" "${BACKUP_DIR}/templates/settings.html"
cp "${DEV_DIR}/static/style.css" "${BACKUP_DIR}/style.css"
cp "${DEV_DIR}/static/site/js/app.js" "${BACKUP_DIR}/static/site/js/app.js"
if [ -d "${DEV_DIR}/templates/partials" ]; then
  cp -R "${DEV_DIR}/templates/partials" "${BACKUP_DIR}/templates/partials"
fi

echo "Applying Decision Interface to DEV dashboard only"
mkdir -p "${DEV_DIR}/templates/partials" "${DEV_DIR}/static/site/js"
cp "new_ponder_site/app.py" "${DEV_DIR}/app.py"
cp "new_ponder_site/templates/base.html" "${DEV_DIR}/templates/base.html"
cp "new_ponder_site/templates/research.html" "${DEV_DIR}/templates/research.html"
cp "new_ponder_site/templates/settings.html" "${DEV_DIR}/templates/settings.html"
cp -R "new_ponder_site/templates/partials/." "${DEV_DIR}/templates/partials/"
cp "new_ponder_site/static/style.css" "${DEV_DIR}/static/style.css"
cp "new_ponder_site/static/site/js/app.js" "${DEV_DIR}/static/site/js/app.js"

echo "Validating DEV dashboard syntax"
python3 -m py_compile "${DEV_DIR}/app.py"

echo "Restarting DEV dashboard only"
sudo systemctl restart tradebot-dashboard-dev.service
sleep 2
sudo systemctl status tradebot-dashboard-dev --no-pager
curl -I http://127.0.0.1:5050

echo "Applied to DEV only. LIVE dashboard, bot.py, trading logic, .env, and Cloudflare were not touched."
echo "Rollback backup: ${BACKUP_DIR}"
