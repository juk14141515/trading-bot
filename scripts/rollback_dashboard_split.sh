#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ubuntu/trading-bot"
BACKUP_ROOT="${APP_ROOT}/backups"
LATEST_FILE="${BACKUP_ROOT}/dashboard-live-before-split-latest.txt"
SYSTEMD_DIR="/etc/systemd/system"
LIVE_SERVICE="${SYSTEMD_DIR}/tradebot-dashboard.service"
DEV_SERVICE_NAME="tradebot-dashboard-dev.service"

cd "${APP_ROOT}"

if [ ! -f "${LATEST_FILE}" ]; then
  echo "No dashboard split backup marker found at ${LATEST_FILE}" >&2
  exit 1
fi

BACKUP_DIR="$(cat "${LATEST_FILE}")"
if [ ! -d "${BACKUP_DIR}" ]; then
  echo "Backup directory not found: ${BACKUP_DIR}" >&2
  exit 1
fi

echo "Stopping DEV dashboard service if it exists"
if systemctl list-unit-files "${DEV_SERVICE_NAME}" --no-legend | grep -q "${DEV_SERVICE_NAME}"; then
  sudo systemctl stop "${DEV_SERVICE_NAME}" || true
fi

echo "Restoring LIVE dashboard files from ${BACKUP_DIR}"
if [ ! -d "${BACKUP_DIR}/new_ponder_site" ]; then
  echo "Backup is missing new_ponder_site files" >&2
  exit 1
fi
rm -rf "${APP_ROOT}/new_ponder_site"
cp -a "${BACKUP_DIR}/new_ponder_site" "${APP_ROOT}/new_ponder_site"

echo "Restoring tradebot-dashboard.service"
if [ -f "${BACKUP_DIR}/systemd/tradebot-dashboard.service" ]; then
  sudo cp "${BACKUP_DIR}/systemd/tradebot-dashboard.service" "${LIVE_SERVICE}"
else
  echo "Backup did not contain tradebot-dashboard.service; leaving current service file in place." >&2
fi

echo "Reloading systemd and restarting LIVE dashboard"
sudo systemctl daemon-reload
sudo systemctl restart tradebot-dashboard.service
sudo systemctl status tradebot-dashboard --no-pager
curl -I http://127.0.0.1:5000

echo "Rollback complete. bot.py, .env, trading logic, and Cloudflare config were not touched."
