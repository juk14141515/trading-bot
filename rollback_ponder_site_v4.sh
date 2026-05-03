#!/bin/bash
cd /home/ubuntu/trading-bot || exit 1
cp web_dashboard.py.bak_before_ponder_site_v4 web_dashboard.py
sudo systemctl restart tradebot-dashboard.service
echo "Rolled back Ponder Site v4."
