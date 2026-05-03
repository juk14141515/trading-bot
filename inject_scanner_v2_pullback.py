from pathlib import Path

p = Path("market_scanner_v2.py")
text = p.read_text()

text = text.replace(
'''    vol_ratio = float(volume.iloc[-1] / avg_volume) if avg_volume else 1

    trend_score = 50''',
'''    vol_ratio = float(volume.iloc[-1] / avg_volume) if avg_volume else 1

    pullback_from_sma5_pct = float((price - sma5) / sma5 * 100) if sma5 else 0
    extension_from_sma20_pct = float((price - sma20) / sma20 * 100) if sma20 else 0

    if pullback_from_sma5_pct < -1.0 and pullback_from_sma5_pct > -4.0 and price > sma20:
        entry_zone = "✅ Pullback Entry Zone"
        entry_score = 90
    elif pullback_from_sma5_pct >= -1.0 and pullback_from_sma5_pct <= 2.5 and price > sma20:
        entry_zone = "🟢 Healthy Entry Zone"
        entry_score = 75
    elif extension_from_sma20_pct > 12 or pullback_from_sma5_pct > 5:
        entry_zone = "⚠️ Extended / Wait"
        entry_score = 35
    elif price < sma20:
        entry_zone = "❌ Below Trend"
        entry_score = 20
    else:
        entry_zone = "👀 Watch Only"
        entry_score = 50

    trend_score = 50'''
)

text = text.replace(
'''    final_score = round(
        trend_score * 0.45 +
        momentum_score * 0.40 +
        volume_score * 0.15,
        2
    )''',
'''    final_score = round(
        trend_score * 0.35 +
        momentum_score * 0.30 +
        volume_score * 0.15 +
        entry_score * 0.20,
        2
    )'''
)

text = text.replace(
'''    if final_score >= 80:
        label = "🔥 Strong Watch"
    elif final_score >= 70:
        label = "✅ Watch"
    elif final_score >= 60:
        label = "👀 Weak Watch"
    else:
        label = "Skip"''',
'''    if final_score >= 80 and entry_score >= 70:
        label = "🔥 Trade-Ready Watch"
    elif final_score >= 75:
        label = "✅ Strong Watch"
    elif final_score >= 65:
        label = "👀 Watch Only"
    else:
        label = "Skip"'''
)

text = text.replace(
'''        "volume_ratio": round(vol_ratio, 2),
        "avg_volume": int(avg_volume),
        "label": label,''',
'''        "volume_ratio": round(vol_ratio, 2),
        "pullback_from_sma5_pct": round(pullback_from_sma5_pct, 2),
        "extension_from_sma20_pct": round(extension_from_sma20_pct, 2),
        "entry_score": entry_score,
        "entry_zone": entry_zone,
        "avg_volume": int(avg_volume),
        "label": label,''',
)

text = text.replace("Ponder Market Scanner v1", "Ponder Market Scanner v2")
text = text.replace("market_scanner_results_v1.csv", "market_scanner_results_v2.csv")
text = text.replace("top_10_candidates_v1.json", "top_10_candidates_v2.json")

p.write_text(text)
print("✅ Scanner v2 pullback + entry timing installed")
