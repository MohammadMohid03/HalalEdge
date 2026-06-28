"""
News Sentiment Analyzer Service
Fetches headlines from Google News RSS, analyzes with FinBERT (HuggingFace transformers).
Falls back to keyword-based sentiment if transformers fails to load.
"""

import time
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

# ---------------------------------------------------------------------------
# In-memory cache: { symbol: (timestamp, result_dict) }
# Results cached for 1 hour per symbol
# ---------------------------------------------------------------------------
_sentiment_cache: dict = {}
_CACHE_TTL_SECONDS = 1 * 60 * 60  # 1 hour

# ---------------------------------------------------------------------------
# Lazy-loaded heavy libraries
# ---------------------------------------------------------------------------
_pipeline = None  # HuggingFace sentiment pipeline
_pipeline_load_attempted = False
_pipeline_load_failed = False

# ---------------------------------------------------------------------------
# Keyword-based fallback sentiment dictionaries
# ---------------------------------------------------------------------------
_POSITIVE_KEYWORDS = [
    "surge", "soar", "rally", "gain", "jump", "rise", "beat", "exceed",
    "upgrade", "outperform", "bullish", "record", "profit", "growth",
    "strong", "boost", "optimistic", "upbeat", "recover", "breakout",
    "buy", "high", "positive", "up", "revenue", "earnings beat",
    "innovative", "expansion", "momentum", "success", "opportunity",
]

_NEGATIVE_KEYWORDS = [
    "crash", "plunge", "drop", "fall", "decline", "loss", "miss",
    "downgrade", "underperform", "bearish", "warning", "risk",
    "weak", "cut", "pessimistic", "downturn", "sell", "low",
    "negative", "down", "layoff", "lawsuit", "investigation",
    "fraud", "bankruptcy", "recession", "inflation", "debt",
    "slump", "tumble", "concern", "fear", "uncertainty",
]


def _lazy_load_pipeline():
    """Lazy-load the HuggingFace FinBERT sentiment pipeline on first call."""
    global _pipeline, _pipeline_load_attempted, _pipeline_load_failed

    if _pipeline_load_attempted:
        return

    _pipeline_load_attempted = True
    try:
        from transformers import pipeline as hf_pipeline

        _pipeline = hf_pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            top_k=None,  # Return all labels with scores
        )
        print("[sentiment] FinBERT pipeline loaded successfully.")
    except Exception as e:
        print(f"[sentiment] Failed to load FinBERT pipeline: {e}")
        print("[sentiment] Falling back to keyword-based sentiment analysis.")
        _pipeline_load_failed = True


def _fetch_headlines(symbol: str, max_headlines: int = 15) -> List[dict]:
    """Fetch news headlines from Google News RSS for a given stock symbol."""
    import feedparser

    url = (
        f"https://news.google.com/rss/search?"
        f"q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        feed = feedparser.parse(url)
        headlines = []

        for entry in feed.entries[:max_headlines]:
            title = entry.get("title", "")
            # Google News titles often include " - Source" at the end
            source = ""
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                source = parts[1].strip() if len(parts) > 1 else ""

            published = entry.get("published", "")
            # Parse published date
            pub_dt = None
            if published:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(published)
                except Exception:
                    pub_dt = None

            headlines.append({
                "title": title,
                "source": source,
                "published": published,
                "published_dt": pub_dt,
            })

        return headlines

    except Exception as e:
        print(f"[sentiment] Failed to fetch headlines for {symbol}: {e}")
        return []


def _analyze_with_finbert(headline: str) -> dict:
    """Analyze a single headline with the FinBERT pipeline."""
    if _pipeline is None:
        raise RuntimeError("FinBERT pipeline not loaded")

    results = _pipeline(headline[:512])  # Truncate to model max length

    # results is a list of lists: [[{'label': 'positive', 'score': 0.9}, ...]]
    if results and isinstance(results[0], list):
        scores = {r["label"]: r["score"] for r in results[0]}
    elif results and isinstance(results[0], dict):
        scores = {r["label"]: r["score"] for r in results}
    else:
        return {"sentiment": "neutral", "confidence": 0.5}

    # Find dominant sentiment
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]

    return {"sentiment": best_label.lower(), "confidence": round(best_score, 4)}


def _analyze_with_keywords(headline: str) -> dict:
    """Fallback: keyword-based sentiment analysis."""
    text = headline.lower()
    pos_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text)
    neg_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text)

    total = pos_count + neg_count
    if total == 0:
        return {"sentiment": "neutral", "confidence": 0.5}

    if pos_count > neg_count:
        confidence = min(0.5 + (pos_count - neg_count) / (total + 2) * 0.5, 0.95)
        return {"sentiment": "positive", "confidence": round(confidence, 4)}
    elif neg_count > pos_count:
        confidence = min(0.5 + (neg_count - pos_count) / (total + 2) * 0.5, 0.95)
        return {"sentiment": "negative", "confidence": round(confidence, 4)}
    else:
        return {"sentiment": "neutral", "confidence": 0.5}


def analyze_sentiment(symbol: str) -> dict:
    """Analyze news sentiment for a stock symbol.

    Returns:
        dict with keys:
            score (int 0-100): overall sentiment score
            headlines (list): individual headline sentiments
            positive_pct (float): percentage of positive headlines
            negative_pct (float): percentage of negative headlines
            neutral_pct (float): percentage of neutral headlines
    """
    symbol = symbol.upper().strip()

    # ------ Check in-memory cache ------
    if symbol in _sentiment_cache:
        cached_time, cached_result = _sentiment_cache[symbol]
        if time.time() - cached_time < _CACHE_TTL_SECONDS:
            return cached_result

    # ------ Try loading FinBERT ------
    _lazy_load_pipeline()

    # ------ Fetch headlines ------
    raw_headlines = _fetch_headlines(symbol, max_headlines=15)

    if not raw_headlines:
        result = {
            "score": 50,
            "headlines": [],
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
            "method": "no_headlines",
        }
        _sentiment_cache[symbol] = (time.time(), result)
        return result

    # ------ Analyze each headline ------
    analyzed_headlines = []
    now = datetime.now(timezone.utc)

    for h in raw_headlines:
        title = h["title"]
        if not title:
            continue

        try:
            if _pipeline is not None and not _pipeline_load_failed:
                analysis = _analyze_with_finbert(title)
            else:
                analysis = _analyze_with_keywords(title)
        except Exception as e:
            print(f"[sentiment] Analysis failed for headline: {e}")
            analysis = _analyze_with_keywords(title)

        analyzed_headlines.append({
            "title": title,
            "sentiment": analysis["sentiment"],
            "confidence": analysis["confidence"],
            "source": h["source"],
            "published": h["published"],
        })

    if not analyzed_headlines:
        result = {
            "score": 50,
            "headlines": [],
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 0.0,
            "method": "analysis_failed",
        }
        _sentiment_cache[symbol] = (time.time(), result)
        return result

    # ------ Calculate weighted sentiment score ------
    # Weight recent headlines (last 24h) 3x more than older ones
    weighted_scores = []
    total_weight = 0

    for idx, h in enumerate(analyzed_headlines):
        # Determine recency weight
        weight = 1.0
        raw_hl = raw_headlines[idx] if idx < len(raw_headlines) else None
        if raw_hl and raw_hl.get("published_dt"):
            age = now - raw_hl["published_dt"]
            if age < timedelta(hours=24):
                weight = 3.0
            elif age < timedelta(hours=48):
                weight = 2.0

        # Convert sentiment to numeric score
        sentiment = h["sentiment"]
        confidence = h["confidence"]

        if sentiment == "positive":
            numeric_score = 50 + (confidence * 50)  # 50-100
        elif sentiment == "negative":
            numeric_score = 50 - (confidence * 50)  # 0-50
        else:
            numeric_score = 50  # neutral

        weighted_scores.append(numeric_score * weight)
        total_weight += weight

    if total_weight > 0:
        final_score = sum(weighted_scores) / total_weight
    else:
        final_score = 50.0

    score = int(max(0, min(100, round(final_score))))

    # ------ Calculate sentiment distribution ------
    total = len(analyzed_headlines)
    pos_count = sum(1 for h in analyzed_headlines if h["sentiment"] == "positive")
    neg_count = sum(1 for h in analyzed_headlines if h["sentiment"] == "negative")
    neu_count = total - pos_count - neg_count

    method = "finbert" if (_pipeline is not None and not _pipeline_load_failed) else "keyword_fallback"

    result = {
        "score": score,
        "headlines": analyzed_headlines,
        "positive_pct": round(pos_count / total * 100, 1) if total > 0 else 0.0,
        "negative_pct": round(neg_count / total * 100, 1) if total > 0 else 0.0,
        "neutral_pct": round(neu_count / total * 100, 1) if total > 0 else 0.0,
        "method": method,
    }

    # ------ Cache result ------
    _sentiment_cache[symbol] = (time.time(), result)
    return result
