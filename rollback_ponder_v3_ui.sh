#!/bin/bash
cd /home/ubuntu/trading-bot || exit 1
if [ -f web_dashboard.py.bak_before_ponder_v3 ]; then
  cp web_dashboard.py.bak_before_ponder_v3 web_dashboard.py
  sudo systemctl restart tradebot-dashboard.service
  echo "Rolled back Ponder UI v3 injection."
else
  echo "No rollback backup found."
fi
