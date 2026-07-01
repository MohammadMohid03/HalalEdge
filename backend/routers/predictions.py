import os
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from backend.database import get_db
from backend.models.prediction import Prediction
from backend.models.shariah import ShariahCache
from backend.schemas.predictions import PredictionOut, ShariahOut, PredictionDetailOut
from backend.services.stock_data import get_stock_info
from backend.services.shariah import check_shariah as run_shariah_check
from backend.services.ensemble import get_ensemble_prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])

# ---------------------------------------------------------------------------
# Admin / GitHub Actions bulk-update endpoint
# ---------------------------------------------------------------------------

def _require_api_key(x_api_key: Optional[str] = Header(None)):
    expected = os.getenv("PREDICTIONS_API_KEY")
    if not expected or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

@router.post("/bulk-update", status_code=status.HTTP_200_OK)
def bulk_update_predictions(
    items: List[dict],
    db: Session = Depends(get_db),
    _: None = Depends(_require_api_key)
):
    """Bulk insert/update predictions from the GitHub Actions ML pipeline."""
    if not items:
        return {"saved": 0}

    saved = 0
    for item in items:
        symbol = item.get("symbol", "").upper().strip()
        if not symbol:
            continue

        pred = Prediction(
            symbol=symbol,
            verdict=item.get("verdict"),
            confidence=item.get("confidence"),
            lstm_score=item.get("lstm_score"),
            sentiment=item.get("sentiment"),
            shariah_score=item.get("shariah_score"),
            ensemble=item.get("ensemble"),
            target_bull=item.get("target_bull"),
            target_bear=item.get("target_bear"),
            details=item.get("details"),
            created_at=datetime.utcnow()
        )
        db.add(pred)
        saved += 1

    db.commit()
    return {"saved": saved}


# ---------------------------------------------------------------------------
# Public endpoints (read cached predictions only — no ML inference here)
# ---------------------------------------------------------------------------

def _latest_prediction(db: Session, symbol: str):
    return db.query(Prediction).filter(
        Prediction.symbol == symbol.upper()
    ).order_by(Prediction.created_at.desc()).first()


@router.get("/{symbol}", response_model=PredictionOut)
def get_prediction(symbol: str, db: Session = Depends(get_db)):
    symbol_upper = symbol.upper().strip()

    # Return the latest cached prediction. The ML pipeline is now run offline
    # by GitHub Actions, so we never trigger heavy model inference on Render.
    cached = _latest_prediction(db, symbol_upper)

    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prediction available for {symbol_upper} yet. Run is scheduled daily."
        )

    return cached


@router.get("/{symbol}/details", response_model=PredictionDetailOut)
def get_prediction_details(symbol: str, db: Session = Depends(get_db)):
    symbol_upper = symbol.upper().strip()

    cached = _latest_prediction(db, symbol_upper)
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prediction details available for {symbol_upper} yet."
        )

    details = cached.details or {}

    return PredictionDetailOut(
        symbol=symbol_upper,
        verdict=cached.verdict or "HOLD",
        confidence=cached.confidence or 0,
        lstm_score=cached.lstm_score or 0,
        sentiment_score=cached.sentiment or 0,
        shariah_score=cached.shariah_score or 0,
        ensemble_score=cached.ensemble or 0,
        technical_indicators=details.get("technical_indicators", {}),
        lstm_details=details.get("lstm_details", {}),
        sentiment_details=details.get("sentiment_details", {}),
    )


@router.get("/{symbol}/shariah", response_model=ShariahOut)
def get_shariah_detail(symbol: str, db: Session = Depends(get_db)):
    symbol_upper = symbol.upper().strip()

    # Check DB cache for a recent check (updated within last 24 hours)
    cache_cutoff = datetime.utcnow() - timedelta(hours=24)
    cached = db.query(ShariahCache).filter(
        ShariahCache.symbol == symbol_upper,
        ShariahCache.updated_at >= cache_cutoff
    ).first()

    if cached:
        return cached

    # Run Shariah check (this is lightweight; no heavy ML)
    try:
        result = run_shariah_check(symbol_upper)
    except Exception as e:
        print(f"[predictions] Shariah check failed for {symbol_upper}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Shariah check temporarily unavailable for {symbol_upper}."
        )

    shariah_cache = ShariahCache(
        symbol=symbol_upper,
        status=result.get("status", "Doubtful"),
        score=result.get("score", 50),
        debt_ratio=result.get("debt_ratio", 0.0),
        haram_revenue=result.get("haram_revenue", 0.0),
        business_type=result.get("business_type", "Unknown"),
    )
    db.add(shariah_cache)
    db.commit()
    db.refresh(shariah_cache)
    return shariah_cache


@router.get("/{symbol}/history")
def get_prediction_history(symbol: str, db: Session = Depends(get_db)):
    """Return the last 30 predictions for a symbol (for the stock detail page)."""
    symbol_upper = symbol.upper().strip()
    predictions = db.query(Prediction).filter(
        Prediction.symbol == symbol_upper
    ).order_by(Prediction.created_at.desc()).limit(30).all()
    return predictions
