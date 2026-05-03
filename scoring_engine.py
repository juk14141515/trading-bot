# scoring_engine.py

def clamp_score(value):
    """
    Keep any score safely between 0 and 100.
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0

    return max(0, min(100, value))


def calculate_weighted_score(
    trend_score=0,
    analyst_score=0,
    news_score=0,
    momentum_score=0,
    volatility_score=50,
):
    """
    Multi-factor scoring engine.

    All input scores should be 0-100.
    Final score returns 0-100.
    """

    trend_score = clamp_score(trend_score)
    analyst_score = clamp_score(analyst_score)
    news_score = clamp_score(news_score)
    momentum_score = clamp_score(momentum_score)
    volatility_score = clamp_score(volatility_score)

    weights = {
        "trend": 0.35,
        "analyst": 0.20,
        "news": 0.15,
        "momentum": 0.20,
        "volatility": 0.10,
    }

    final_score = (
        trend_score * weights["trend"]
        + analyst_score * weights["analyst"]
        + news_score * weights["news"]
        + momentum_score * weights["momentum"]
        + volatility_score * weights["volatility"]
    )

    return round(final_score, 2)


def explain_score(
    symbol,
    trend_score=0,
    analyst_score=0,
    news_score=0,
    momentum_score=0,
    volatility_score=50,
):
    final_score = calculate_weighted_score(
        trend_score,
        analyst_score,
        news_score,
        momentum_score,
        volatility_score,
    )

    return {
        "symbol": symbol,
        "final_score": final_score,
        "components": {
            "trend_score": trend_score,
            "analyst_score": analyst_score,
            "news_score": news_score,
            "momentum_score": momentum_score,
            "volatility_score": volatility_score,
        },
    }
