"""
LSTM-style Price Predictor Service
Uses sklearn MLPRegressor as a neural network proxy (TensorFlow/Keras incompatible with Python 3.14 Windows).
Fetches 2 years of daily OHLCV data, creates 30-day sliding window sequences,
trains an MLPRegressor to predict next-day close price.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# In-memory cache: { symbol: (timestamp, result_dict) }
# Results cached for 6 hours per symbol
# ---------------------------------------------------------------------------
_prediction_cache: dict = {}
_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

# ---------------------------------------------------------------------------
# Lazy-loaded heavy libraries
# ---------------------------------------------------------------------------
_sklearn_loaded = False
_MinMaxScaler = None
_MLPRegressor = None
_np = None


def _lazy_load_sklearn():
    """Lazy-load sklearn and numpy on first call to avoid slow startup."""
    global _sklearn_loaded, _MinMaxScaler, _MLPRegressor, _np
    if _sklearn_loaded:
        return
    try:
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler
        from sklearn.neural_network import MLPRegressor

        _np = np
        _MinMaxScaler = MinMaxScaler
        _MLPRegressor = MLPRegressor
        _sklearn_loaded = True
    except ImportError as e:
        print(f"[lstm_predictor] Failed to import sklearn/numpy: {e}")
        raise


def _fetch_ohlcv(symbol: str):
    """Fetch 2 years of daily OHLCV data via yfinance."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2y", interval="1d")
    if hist is None or hist.empty:
        raise ValueError(f"No historical data returned for {symbol}")
    return hist


def _create_sequences(data, window_size: int = 30):
    """Create sliding-window sequences for supervised learning.

    Each sample X is a flattened window of `window_size` days of features
    (OHLCV = 5 features per day → 150 features per sample).
    The target y is the next-day close price.
    """
    X, y = [], []
    for i in range(len(data) - window_size):
        window = data[i : i + window_size]
        target = data[i + window_size, 3]  # Close price column (index 3)
        X.append(window.flatten())
        y.append(target)
    return _np.array(X), _np.array(y)


def _momentum_fallback(symbol: str) -> dict:
    """Fallback: simple momentum-based scoring when ML pipeline fails."""
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo", interval="1d")

        if hist is None or hist.empty:
            return _neutral_fallback(symbol)

        closes = hist["Close"].values
        current_price = float(closes[-1])

        # Simple momentum indicators
        sma_20 = float(closes[-20:].mean()) if len(closes) >= 20 else current_price
        sma_5 = float(closes[-5:].mean()) if len(closes) >= 5 else current_price

        # Price vs moving average
        momentum_score = 50.0
        if current_price > sma_20:
            momentum_score += 15
        else:
            momentum_score -= 15

        if sma_5 > sma_20:
            momentum_score += 10
        else:
            momentum_score -= 10

        # Recent trend (last 5 days)
        if len(closes) >= 5:
            recent_change = (closes[-1] - closes[-5]) / closes[-5] * 100
            momentum_score += min(max(recent_change * 2, -15), 15)

        score = int(max(0, min(100, momentum_score)))
        predicted_price = current_price * (1 + (score - 50) / 500)

        change_pct = ((predicted_price - current_price) / current_price) * 100

        if score > 70:
            direction = "BULLISH"
        elif score < 40:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        return {
            "score": score,
            "predicted_price": round(predicted_price, 2),
            "current_price": round(current_price, 2),
            "direction": direction,
            "change_pct": round(change_pct, 2),
            "method": "momentum_fallback",
        }
    except Exception as e:
        print(f"[lstm_predictor] Momentum fallback also failed for {symbol}: {e}")
        return _neutral_fallback(symbol)


def _neutral_fallback(symbol: str) -> dict:
    """Ultimate fallback: return a neutral score."""
    return {
        "score": 50,
        "predicted_price": 0.0,
        "current_price": 0.0,
        "direction": "NEUTRAL",
        "change_pct": 0.0,
        "method": "neutral_fallback",
    }


def predict_price(symbol: str) -> dict:
    """Predict next-day close price direction and magnitude.

    Returns:
        dict with keys:
            score (int 0-100): >70 bullish, 40-70 neutral, <40 bearish
            predicted_price (float): predicted next-day close
            current_price (float): latest close price
            direction (str): BULLISH / NEUTRAL / BEARISH
            change_pct (float): predicted change percentage
    """
    symbol = symbol.upper().strip()

    # ------ Check in-memory cache ------
    if symbol in _prediction_cache:
        cached_time, cached_result = _prediction_cache[symbol]
        if time.time() - cached_time < _CACHE_TTL_SECONDS:
            return cached_result

    # ------ ML pipeline ------
    try:
        _lazy_load_sklearn()

        # 1. Fetch data
        hist = _fetch_ohlcv(symbol)
        ohlcv = hist[["Open", "High", "Low", "Close", "Volume"]].values

        if len(ohlcv) < 60:
            raise ValueError(
                f"Insufficient data for {symbol}: {len(ohlcv)} rows (need >= 60)"
            )

        # 2. Normalize
        scaler = _MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(ohlcv)

        # 3. Create 30-day sliding window sequences
        window_size = 30
        X, y = _create_sequences(scaled_data, window_size)

        if len(X) < 10:
            raise ValueError(f"Too few sequences for {symbol}: {len(X)}")

        # 4. Train/test split (use last 20% for validation, train on 80%)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # 5. Train MLPRegressor
        model = _MLPRegressor(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            max_iter=200,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=10,
            learning_rate="adaptive",
            learning_rate_init=0.001,
        )
        model.fit(X_train, y_train)

        # 6. Predict next day using the last window
        last_window = scaled_data[-window_size:].flatten().reshape(1, -1)
        predicted_scaled_close = model.predict(last_window)[0]

        # 7. Inverse-transform to get actual price
        # We need to reconstruct a full feature row to inverse-transform
        dummy_row = _np.zeros((1, ohlcv.shape[1]))
        dummy_row[0, 3] = predicted_scaled_close  # Close is column index 3
        inverse_row = scaler.inverse_transform(dummy_row)
        predicted_price = float(inverse_row[0, 3])

        current_price = float(ohlcv[-1, 3])  # Last actual close

        # 8. Calculate score based on predicted direction and magnitude
        if current_price > 0:
            change_pct = ((predicted_price - current_price) / current_price) * 100
        else:
            change_pct = 0.0

        # Map change_pct to a 0-100 score
        # +5% change → score ~90, -5% → score ~10, 0% → score ~50
        raw_score = 50 + (change_pct * 8)  # 8x multiplier for sensitivity
        score = int(max(0, min(100, raw_score)))

        if score > 70:
            direction = "BULLISH"
        elif score < 40:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        result = {
            "score": score,
            "predicted_price": round(predicted_price, 2),
            "current_price": round(current_price, 2),
            "direction": direction,
            "change_pct": round(change_pct, 2),
            "method": "mlp_regressor",
        }

    except Exception as e:
        print(f"[lstm_predictor] ML prediction failed for {symbol}: {e}")
        result = _momentum_fallback(symbol)

    # ------ Cache result ------
    _prediction_cache[symbol] = (time.time(), result)
    return result
