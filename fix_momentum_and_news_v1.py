from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "bot.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"bot.py.bak_fix_momentum_news_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

# 1) Add safe momentum function if missing
if "def get_momentum_score(" not in txt:
    marker = "def buy(symbol, score):"
    func = r'''
def get_momentum_score(symbol):
    """
    Safe momentum score fallback.
    Returns bounded -10 to +10 score.
    Never breaks bot if data fails.
    """
    try:
        import yfinance as yf
        data = yf.download(symbol, period="5d", interval="5m", progress=False)

        if data is None or len(data) < 10:
            return 0

        close = data["Close"].dropna()
        if len(close) < 10:
            return 0

        first = float(close.iloc[0])
        last = float(close.iloc[-1])

        if first <= 0:
            return 0

        pct_change = ((last - first) / first) * 100
        score = max(-10, min(10, pct_change * 2))
        return round(score, 2)

    except Exception as e:
        try:
            log(f"ERROR | momentum {symbol} | {e}")
        except Exception:
            pass
        return 0


'''
    if marker in txt:
        txt = txt.replace(marker, func + marker, 1)
        print("DONE: added get_momentum_score")
    else:
        txt += "\n" + func
        print("DONE: added get_momentum_score at end")
else:
    print("SKIP: get_momentum_score already exists")

# 2) Add helper for Alpaca/Finnhub/yfinance tuple/dict/object news formats
if "def safe_headline_text(" not in txt:
    marker = "def get_momentum_score("
    helper = r'''
def safe_headline_text(item):
    """
    Handles news items that may be objects, dicts, tuples, or strings.
    Prevents: tuple object has no attribute headline.
    """
    try:
        if item is None:
            return ""
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return str(item.get("headline") or item.get("title") or item.get("summary") or "")
        if isinstance(item, (tuple, list)):
            return " ".join(str(x) for x in item if x is not None)
        return str(
            getattr(item, "headline", None)
            or getattr(item, "title", None)
            or getattr(item, "summary", None)
            or item
        )
    except Exception:
        return ""


'''
    if marker in txt:
        txt = txt.replace(marker, helper + marker, 1)
    else:
        txt += "\n" + helper
    print("DONE: added safe_headline_text")
else:
    print("SKIP: safe_headline_text already exists")

# 3) Patch direct .headline access patterns
replacements = {
    "headline = news.headline": "headline = safe_headline_text(news)",
    "headline = item.headline": "headline = safe_headline_text(item)",
    "headline = article.headline": "headline = safe_headline_text(article)",
    "headline = n.headline": "headline = safe_headline_text(n)",
    "headline = h.headline": "headline = safe_headline_text(h)",
    "headline = a.headline": "headline = safe_headline_text(a)",
}

patched = 0
for old, new in replacements.items():
    if old in txt:
        txt = txt.replace(old, new)
        patched += 1

# 4) Patch common inline `.headline.lower()` usage
txt = txt.replace(".headline.lower()", "_headline_safe_lower_PLACEHOLDER")

# Restore placeholder carefully by converting object access lines if any remain
if "_headline_safe_lower_PLACEHOLDER" in txt:
    txt = txt.replace("_headline_safe_lower_PLACEHOLDER", ".headline.lower()")
    print("NOTE: inline .headline.lower() may still exist. Check grep below.")

FILE.write_text(txt)

print(f"DONE: patched headline assignments: {patched}")
print("NEXT:")
print("python3 -m py_compile bot.py")
print("grep -n \"headline\" bot.py | head -40")
print("sudo systemctl restart tradebot")
