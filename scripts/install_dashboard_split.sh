#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/ubuntu/trading-bot"
LIVE_APP_DIR="${APP_ROOT}/new_ponder_site"
DEV_APP_DIR="${APP_ROOT}/new_ponder_site_dev"
BACKUP_ROOT="${APP_ROOT}/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/dashboard-live-before-split-${STAMP}"
LATEST_FILE="${BACKUP_ROOT}/dashboard-live-before-split-latest.txt"
SYSTEMD_DIR="/etc/systemd/system"
LIVE_SERVICE="${SYSTEMD_DIR}/tradebot-dashboard.service"
DEV_SERVICE="${SYSTEMD_DIR}/tradebot-dashboard-dev.service"

cd "${APP_ROOT}"

echo "Creating dashboard split backup at ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}/systemd"
cp -a "${LIVE_APP_DIR}" "${BACKUP_DIR}/new_ponder_site"

if [ -f "${LIVE_SERVICE}" ]; then
  sudo cp "${LIVE_SERVICE}" "${BACKUP_DIR}/systemd/tradebot-dashboard.service"
fi

if compgen -G "${SYSTEMD_DIR}/*dashboard*.service" > /dev/null; then
  for service_file in "${SYSTEMD_DIR}"/*dashboard*.service; do
    [ -f "${service_file}" ] || continue
    sudo cp "${service_file}" "${BACKUP_DIR}/systemd/$(basename "${service_file}")"
  done
fi

printf '%s\n' "${BACKUP_DIR}" > "${LATEST_FILE}"

echo "Preparing separate DEV dashboard copy at ${DEV_APP_DIR}"
rm -rf "${DEV_APP_DIR}"
cp -a "${LIVE_APP_DIR}" "${DEV_APP_DIR}"

echo "Running syntax check before service changes"
python3 -m py_compile new_ponder_site/app.py
python3 -m py_compile new_ponder_site_dev/app.py

echo "Writing DEV dashboard service on 127.0.0.1:5050"
sudo tee "${DEV_SERVICE}" >/dev/null <<'SERVICE'
[Unit]
Description=Ponder Invest AI DEV dashboard
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/trading-bot
EnvironmentFile=-/home/ubuntu/trading-bot/.env
Environment=PONDER_DASHBOARD_ENV=dev
Environment=PONDER_DASHBOARD_HOST=127.0.0.1
Environment=PONDER_DASHBOARD_PORT=5050
ExecStart=/home/ubuntu/trading-bot/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5050 new_ponder_site_dev.app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "Writing LIVE dashboard service on 127.0.0.1:5000"
sudo tee "${LIVE_SERVICE}" >/dev/null <<'SERVICE'
[Unit]
Description=Ponder Invest AI LIVE dashboard
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/trading-bot
EnvironmentFile=-/home/ubuntu/trading-bot/.env
Environment=PONDER_DASHBOARD_ENV=live
Environment=PONDER_DASHBOARD_HOST=127.0.0.1
Environment=PONDER_DASHBOARD_PORT=5000
ExecStart=/home/ubuntu/trading-bot/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 new_ponder_site.app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "Reloading systemd and starting DEV first"
sudo systemctl daemon-reload
sudo systemctl enable tradebot-dashboard-dev.service
sudo systemctl restart tradebot-dashboard-dev.service
sudo systemctl status tradebot-dashboard-dev --no-pager
curl -I http://127.0.0.1:5050

echo "Starting LIVE dashboard"
sudo systemctl enable tradebot-dashboard.service
sudo systemctl restart tradebot-dashboard.service
sudo systemctl status tradebot-dashboard --no-pager
curl -I http://127.0.0.1:5000

echo "Cloudflare config was not touched."
echo "Rollback command: bash scripts/rollback_dashboard_split.sh"
