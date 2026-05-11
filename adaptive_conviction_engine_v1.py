from datetime import datetime


def conviction_level(score=0, confidence='Low', regime='neutral', capital_used_pct=0, win_rate=50):
    conviction = 0

    conviction += min(score, 100) * 0.45

    confidence_map = {
        'Low': 10,
        'Medium': 20,
        'High': 35,
        'Extreme': 50,
    }
    conviction += confidence_map.get(confidence, 0)

    regime_map = {
        'bullish': 20,
        'neutral': 0,
        'defensive': -15,
        'bearish': -30,
    }
    conviction += regime_map.get(str(regime).lower(), 0)

    if capital_used_pct < 35:
        conviction += 10

    if win_rate > 60:
        conviction += 10
    elif win_rate < 40:
        conviction -= 10

    conviction = max(0, min(100, round(conviction, 1)))

    if conviction >= 85:
        allocation = 25
        label = 'HIGH CONVICTION'
    elif conviction >= 70:
        allocation = 15
        label = 'MEDIUM CONVICTION'
    elif conviction >= 55:
        allocation = 5
        label = 'LOW CONVICTION'
    else:
        allocation = 0
        label = 'NO SHADOW MOVE'

    return {
        'generated_at': datetime.utcnow().isoformat(),
        'conviction_score': conviction,
        'conviction_label': label,
        'recommended_allocation_pct': allocation,
    }


if __name__ == '__main__':
    sample = conviction_level(
        score=82,
        confidence='Medium',
        regime='bullish',
        capital_used_pct=23,
        win_rate=58,
    )

    print(sample)
