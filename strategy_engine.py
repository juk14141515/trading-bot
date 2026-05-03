def calculate_final_score(trend_score, analyst_score, news_score, volatility_score, market_score, memory_score):
    final_score = (
        trend_score * 0.25 +
        analyst_score * 0.15 +
        news_score * 0.15 +
        volatility_score * 0.15 +
        market_score * 0.15 +
        memory_score * 0.15
    )

    return round(final_score, 2)
