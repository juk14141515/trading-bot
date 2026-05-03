#!/bin/bash

echo "=============================="
echo "🧠 PONDER SYSTEM HEALTH CHECK"
echo "=============================="
echo ""

echo "📡 SERVICES STATUS"
echo "------------------------------"
echo -n "Tradebot: "
systemctl is-active tradebot.service

echo -n "Dashboard: "
systemctl is-active tradebot-dashboard.service

echo ""

echo "🌐 PORT STATUS"
echo "------------------------------"
lsof -i :5000 | grep LISTEN || echo "❌ Port 5000 not active"
lsof -i :5050 | grep LISTEN || echo "⚠️ Port 5050 (new site) not active"

echo ""

echo "📊 API / SITE CHECK"
echo "------------------------------"
curl -s -o /dev/null -w "Dashboard (5000): %{http_code}\n" http://127.0.0.1:5000
curl -s -o /dev/null -w "New Site (5050): %{http_code}\n" http://127.0.0.1:5050

echo ""

echo "📁 RESEARCH DATA"
echo "------------------------------"
ls -lh static/research/*latest.json 2>/dev/null || echo "❌ No research JSON found"

echo ""

echo "📈 BOT ACTIVITY (last 5 lines)"
echo "------------------------------"
tail -n 5 log.txt 2>/dev/null || echo "⚠️ No log file"

echo ""

echo "🚨 ERROR CHECK"
echo "------------------------------"
journalctl -u tradebot.service -n 10 --no-pager | grep -i error || echo "✅ No recent bot errors"
journalctl -u tradebot-dashboard.service -n 10 --no-pager | grep -i error || echo "✅ No recent dashboard errors"

echo ""

echo "=============================="
echo "✅ HEALTH CHECK COMPLETE"
echo "=============================="
