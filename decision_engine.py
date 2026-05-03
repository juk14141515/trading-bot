def decide_trade(stock, market_regime, news_impact, sell_pressure=0):
    score = float(stock.get("final_score", 0) or 0)
    entry_zone = str(stock.get("entry_zone", ""))

    if market_regime == "Risk-Off" and float(news_impact or 0) > 75:
        return {
            "action": "WAIT",
            "confidence": "Low",
            "reason": "High news risk + defensive market"
        }

    if float(sell_pressure or 0) >= 70:
        return {
            "action": "EXIT / AVOID",
            "confidence": "High",
            "reason": "Strong sell pressure detected"
        }

    if "Extended" in entry_zone:
        return {
            "action": "WAIT_PULLBACK",
            "confidence": "Medium",
            "reason": "Stock is extended, avoid chasing"
        }

    if score >= 85 and float(sell_pressure or 0) < 40:
        return {
            "action": "STRONG_BUY",
            "confidence": "High",
            "reason": "High score + low sell pressure"
        }

    if score >= 78 and "Healthy" in entry_zone:
        return {
            "action": "BUY",
            "confidence": "Medium",
            "reason": "Good score with solid entry zone"
        }

    if score >= 70:
        return {
            "action": "WATCH",
            "confidence": "Medium",
            "reason": "Decent setup, not strong enough yet"
        }

    return {
        "action": "IGNORE",
        "confidence": "Low",
        "reason": "Weak setup"
    }
