"""
Ensemble Classifier Service
Combines LSTM predictor, sentiment analyzer, Shariah compliance, and technical indicators
into a weighted ensemble score that produces BUY / HOLD / AVOID verdicts.

Weights:
    - LSTM predictor:       0.30
    - Sentiment analyzer:   0.25
    - Shariah compliance:   0.25
    - Technical indicators: 0.20

Shariah hard gate: if shariah_score < 60 → verdict is AVOID immediately.
"""

import time
from typing import Optional

# ---------------------------------------------------------------------------
# In-memory cache: { symbol: (timestamp, result_dict) }
# Results cached for 4 hours per symbol
# ---------------------------------------------------------------------------
_ensemble_cache: dict = {}
_CACHE_TTL_SECONDS = 4 * 60 * 60  # 4 hours

# ---------------------------------------------------------------------------
# Ensemble weights
# ---------------------------------------------------------------------------
WEIGHT_LSTM = 0.30
WEIGHT_SENTIMENT = 0.25
WEIGHT_SHARIAH = 0.25
WEIGHT_TECHNICAL = 0.20


def _get_shariah_score(symbol: str) -> int:
    """Fetch Shariah compliance score (0-100)."""
    try:
        from backend.services.shariah import check_shariah

        result = check_shariah(symbol)
        return int(result.get("score", 50))
    except Exception as e:
        print(f"[ensemble] Shariah check failed for {symbol}: {e}")
        return 50  # Neutral fallback


def _get_lstm_score(symbol: str) -> dict:
    """Fetch LSTM prediction score and details."""
    try:
        from backend.services.lstm_predictor import predict_price

        return predict_price(symbol)
    except Exception as e:
        print(f"[ensemble] LSTM prediction failed for {symbol}: {e}")
        return {
            "score": 50,
            "predicted_price": 0.0,
            "current_price": 0.0,
            "direction": "NEUTRAL",
            "change_pct": 0.0,
            "method": "error_fallback",
        }


def _get_sentiment_score(symbol: str) -> dict:
    """Fetch sentiment analysis score and details."""
    try:
        from backend.services.sentiment import analyze_sentiment

        return analyze_sentiment(symbol)
    except Exception as e:
        print(f"[ensemble] Sentiment analysis failed for {symbol}: {e}")
        return {
            "score": 50,
            "headlines": [],
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
            "method": "error_fallback",
        }


def _get_technical_score(symbol: str) -> dict:
    """Fetch technical indicators and compute a 0-100 technical score."""
    try:
        from backend.services.stock_data import get_technical_indicators

        indicators = get_technical_indicators(symbol)

        # Compute a composite technical score from individual indicators
        score = 50.0  # Start neutral

        # RSI contribution (30-70 is healthy, oversold <30 → buy signal, overbought >70 → sell)
        rsi = indicators.get("rsi", 50)
        if rsi < 30:
            score += 15  # Oversold → potential bounce
        elif rsi < 45:
            score += 8
        elif rsi > 70:
            score -= 15  # Overbought → potential drop
        elif rsi > 55:
            score += 5  # Mild momentum

        # 52-week momentum
        momentum_52w = indicators.get("momentum_52w", 50)
        if momentum_52w > 70:
            score += 10
        elif momentum_52w > 50:
            score += 5
        elif momentum_52w < 30:
            score -= 10
        elif momentum_52w < 50:
            score -= 5

        # Volume trend (>1.2 means increasing volume → confirmation)
        volume_trend = indicators.get("volume_trend", 1.0)
        if volume_trend > 1.5:
            score += 8
        elif volume_trend > 1.2:
            score += 4
        elif volume_trend < 0.7:
            score -= 5

        # Moving average signals
        sma20 = indicators.get("sma20", 0)
        sma50 = indicators.get("sma50", 0)
        current_price = indicators.get("current_price", 0)

        if current_price and sma20 and sma50:
            # Price above both SMAs → bullish
            if current_price > sma20 > sma50:
                score += 10
            # Price below both SMAs → bearish
            elif current_price < sma20 < sma50:
                score -= 10
            # Golden cross (SMA20 > SMA50) → mildly bullish
            elif sma20 > sma50:
                score += 5
            else:
                score -= 5

        technical_score = int(max(0, min(100, score)))

        return {
            "score": technical_score,
            "indicators": indicators,
        }
    except Exception as e:
        print(f"[ensemble] Technical indicators failed for {symbol}: {e}")
        return {
            "score": 50,
            "indicators": {},
        }


def get_ensemble_prediction(symbol: str) -> dict:
    """Produce an ensemble prediction combining all AI/ML services.

    Returns:
        dict with keys:
            verdict (str): BUY / HOLD / AVOID
            confidence (int): 0-100 confidence level
            lstm_score (int): LSTM predictor score
            sentiment_score (int): sentiment analysis score
            shariah_score (int): Shariah compliance score
            ensemble_score (int): weighted ensemble score
            technical_indicators (dict): raw technical indicator values
    """
    symbol = symbol.upper().strip()

    # ------ Check in-memory cache ------
    if symbol in _ensemble_cache:
        cached_time, cached_result = _ensemble_cache[symbol]
        if time.time() - cached_time < _CACHE_TTL_SECONDS:
            return cached_result

    # ------ Collect all component scores ------
    lstm_result = _get_lstm_score(symbol)
    sentiment_result = _get_sentiment_score(symbol)
    shariah_score = _get_shariah_score(symbol)
    technical_result = _get_technical_score(symbol)

    lstm_score = int(lstm_result.get("score", 50))
    sentiment_score = int(sentiment_result.get("score", 50))
    technical_score = int(technical_result.get("score", 50))

    # ------ Shariah hard gate ------
    if shariah_score < 60:
        result = {
            "verdict": "AVOID",
            "confidence": max(70, 100 - shariah_score),
            "lstm_score": lstm_score,
            "sentiment_score": sentiment_score,
            "shariah_score": shariah_score,
            "ensemble_score": int(
                lstm_score * WEIGHT_LSTM
                + sentiment_score * WEIGHT_SENTIMENT
                + shariah_score * WEIGHT_SHARIAH
                + technical_score * WEIGHT_TECHNICAL
            ),
            "technical_indicators": technical_result.get("indicators", {}),
            "lstm_details": {
                "predicted_price": lstm_result.get("predicted_price", 0),
                "current_price": lstm_result.get("current_price", 0),
                "direction": lstm_result.get("direction", "NEUTRAL"),
                "change_pct": lstm_result.get("change_pct", 0),
                "method": lstm_result.get("method", "unknown"),
            },
            "sentiment_details": {
                "headlines_count": len(sentiment_result.get("headlines", [])),
                "positive_pct": sentiment_result.get("positive_pct", 0),
                "negative_pct": sentiment_result.get("negative_pct", 0),
                "neutral_pct": sentiment_result.get("neutral_pct", 0),
                "method": sentiment_result.get("method", "unknown"),
            },
        }
        _ensemble_cache[symbol] = (time.time(), result)
        return result

    # ------ Weighted ensemble score ------
    ensemble_score = (
        lstm_score * WEIGHT_LSTM
        + sentiment_score * WEIGHT_SENTIMENT
        + shariah_score * WEIGHT_SHARIAH
        + technical_score * WEIGHT_TECHNICAL
    )
    ensemble_score = int(max(0, min(100, round(ensemble_score))))

    # ------ Map to verdict ------
    if ensemble_score >= 70:
        verdict = "BUY"
    elif ensemble_score >= 45:
        verdict = "HOLD"
    else:
        verdict = "AVOID"

    # ------ Confidence calculation ------
    # Higher confidence when scores agree; lower when they diverge
    scores = [lstm_score, sentiment_score, shariah_score, technical_score]
    score_range = max(scores) - min(scores)
    # More agreement (smaller range) → higher confidence
    agreement_bonus = max(0, 30 - score_range // 2)
    base_confidence = 60
    confidence = min(99, base_confidence + agreement_bonus)

    result = {
        "verdict": verdict,
        "confidence": confidence,
        "lstm_score": lstm_score,
        "sentiment_score": sentiment_score,
        "shariah_score": shariah_score,
        "ensemble_score": ensemble_score,
        "technical_indicators": technical_result.get("indicators", {}),
        "lstm_details": {
            "predicted_price": lstm_result.get("predicted_price", 0),
            "current_price": lstm_result.get("current_price", 0),
            "direction": lstm_result.get("direction", "NEUTRAL"),
            "change_pct": lstm_result.get("change_pct", 0),
            "method": lstm_result.get("method", "unknown"),
        },
        "sentiment_details": {
            "headlines_count": len(sentiment_result.get("headlines", [])),
            "positive_pct": sentiment_result.get("positive_pct", 0),
            "negative_pct": sentiment_result.get("negative_pct", 0),
            "neutral_pct": sentiment_result.get("neutral_pct", 0),
            "method": sentiment_result.get("method", "unknown"),
        },
    }

    # ------ Cache result ------
    _ensemble_cache[symbol] = (time.time(), result)
    return result
