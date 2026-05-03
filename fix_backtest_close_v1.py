from pathlib import Path

p = Path("backtest_sim_v1.py")
text = p.read_text()
p.with_suffix(".py.bak_close_fix_v1").write_text(text)

old = """    if df.empty:
        return []

    df = df.dropna()
    results = []
"""

new = """    if df.empty:
        return []

    # yfinance can return MultiIndex columns. Flatten safely.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    df = df.dropna()
    results = []
"""

text = text.replace(old, new)
p.write_text(text)
print("✅ Patched yfinance Close column handling")
