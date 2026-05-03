from pathlib import Path

file = Path("bot.py")
txt = file.read_text()

txt = txt.replace('float(latest["Close"])', 'float(latest["Close"].iloc[0])')
txt = txt.replace('float(latest["SMA20"])', 'float(latest["SMA20"].iloc[0])')
txt = txt.replace('float(latest["SMA50"])', 'float(latest["SMA50"].iloc[0])')

file.write_text(txt)

print("DONE: float warnings fixed")
