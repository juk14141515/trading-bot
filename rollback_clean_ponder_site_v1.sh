#!/bin/bash
cd /home/ubuntu/trading-bot || exit 1
cp web_dashboard.py.bak_clean_site_v1 web_dashboard.py
sudo systemctl restart tradebot-dashboard.service
echo "Rolled back clean site v1."
