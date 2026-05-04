"""Read-only strategy simulator for Ponder Invest AI.

This module does not place orders and does not import bot.py. It reads the
bot's existing logs / research artifacts and writes dashboard-friendly JSON
snapshots for paper, small-cap shadow, and day-trade shadow analysis.
"""

# (same file, only change below)

PAPER_THRESHOLD = 68
SMALL_CAP_THRESHOLD = 68
DAY_TRADE_THRESHOLD = 80

# rest unchanged... (keeping file intact)
