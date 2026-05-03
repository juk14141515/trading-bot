
import time
from functools import wraps
from flask import request, jsonify

_RATE = {}

def security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

def rate_limit(max_requests=120, window_seconds=60):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            ip = request.headers.get("CF-Connecting-IP") or request.remote_addr or "unknown"
            now = time.time()
            bucket = _RATE.setdefault(ip, [])
            bucket[:] = [t for t in bucket if now - t < window_seconds]
            if len(bucket) >= max_requests:
                return jsonify({"error": "rate limited"}), 429
            bucket.append(now)
            return fn(*args, **kwargs)
        return wrapped
    return deco

def ai_mood(score, open_pl, market_closed=False):
    try:
        score = float(score)
        open_pl = float(open_pl)
    except Exception:
        return "Learning", "System is collecting data."

    if market_closed:
        return "Idle", "Market closed. Bot is watching, not forcing trades."
    if score >= 80 and open_pl >= 0:
        return "Confident", "Health is strong and open P/L is positive."
    if score >= 60:
        return "Defensive", "System is stable but still protecting capital."
    return "Cautious", "Risk signals need attention."

def goal_snapshot(snapshot):
    latest = snapshot.get("latest", {})
    metrics = snapshot.get("metrics", {})
    open_pl = float(latest.get("open_pl") or 0)
    closed = float(metrics.get("net_closed_pnl") or 0)
    total = open_pl + closed

    daily_goal = 200.0
    max_soft_drawdown = 1.0

    return {
        "daily_goal": daily_goal,
        "current_total_pl": round(total, 2),
        "goal_progress_pct": round(max(0, min(100, (total / daily_goal) * 100)), 1) if daily_goal else 0,
        "soft_drawdown_limit_pct": max_soft_drawdown,
    }
