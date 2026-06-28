from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List


from backend.database import get_db
from backend.models.prediction import Prediction
from backend.models.shariah import ShariahCache
from backend.schemas.predictions import PredictionOut, ShariahOut, PredictionDetailOut
from backend.services.stock_data import get_stock_info
from backend.services.shariah import check_shariah as run_shariah_check
from backend.services.ensemble import get_ensemble_prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/{symbol}", response_model=PredictionOut)
def get_prediction(symbol: str, db: Session = Depends(get_db)):
    symbol_upper = symbol.upper().strip()
    
    # Check DB cache for a recent prediction (created within last 24 hours)
    cache_cutoff = datetime.utcnow() - timedelta(hours=24)
    cached = db.query(Prediction).filter(
        Prediction.symbol == symbol_upper,
        Prediction.created_at >= cache_cutoff
    ).order_by(Prediction.created_at.desc()).first()

    if cached:
        return cached

    # Run the real ensemble prediction pipeline
    try:
        ensemble_result = get_ensemble_prediction(symbol_upper)
    except Exception as e:
        print(f"[predictions] Ensemble prediction failed for {symbol_upper}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI prediction service temporarily unavailable for {symbol_upper}."
        )

    # Save to database cache
    # Fetch previous prediction first to check if verdict changed
    prev_pred = db.query(Prediction).filter(Prediction.symbol == symbol_upper).order_by(Prediction.created_at.desc()).first()

    new_pred = Prediction(
        symbol=symbol_upper,
        verdict=ensemble_result["verdict"],
        confidence=ensemble_result["confidence"],
        lstm_score=ensemble_result["lstm_score"],
        sentiment=ensemble_result["sentiment_score"],
        shariah_score=ensemble_result["shariah_score"],
        ensemble=ensemble_result["ensemble_score"]
    )
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    # Check if verdict changed and send alerts
    if prev_pred and prev_pred.verdict != new_pred.verdict:
        from backend.models.watchlist import Watchlist
        from backend.models.user import User
        from backend.services.auth import send_simulated_email

        subscribers = db.query(User).join(Watchlist, Watchlist.user_id == User.id).filter(
            Watchlist.symbol == symbol_upper,
            Watchlist.email_alerts == True
        ).all()

        for sub in subscribers:
            alert_body = f"""Assalamu Alaikum {sub.full_name},

This is an automated alert from HalalEdge. 

The AI Verdict for your watchlisted stock {symbol_upper} has changed:

Previous Verdict: {prev_pred.verdict}
New AI Verdict: {new_pred.verdict} (Ensemble Score: {new_pred.ensemble}%, Confidence: {new_pred.confidence}%)

You can view the detailed breakdown including LSTM price target and FinBERT news sentiment at:
http://localhost:5500/stock.html?sym={symbol_upper}

Regards,
The HalalEdge AI Engine
"""
            send_simulated_email(
                sub.email,
                f"HalalEdge Alert: {symbol_upper} Verdict Changed to {new_pred.verdict}",
                alert_body
            )

    return new_pred


@router.get("/{symbol}/details", response_model=PredictionDetailOut)
def get_prediction_details(symbol: str):
    """Return full breakdown of the ensemble prediction with all component details."""
    symbol_upper = symbol.upper().strip()

    try:
        ensemble_result = get_ensemble_prediction(symbol_upper)
    except Exception as e:
        print(f"[predictions] Detail prediction failed for {symbol_upper}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI prediction service temporarily unavailable for {symbol_upper}."
        )

    return PredictionDetailOut(
        symbol=symbol_upper,
        verdict=ensemble_result["verdict"],
        confidence=ensemble_result["confidence"],
        lstm_score=ensemble_result["lstm_score"],
        sentiment_score=ensemble_result["sentiment_score"],
        shariah_score=ensemble_result["shariah_score"],
        ensemble_score=ensemble_result["ensemble_score"],
        technical_indicators=ensemble_result.get("technical_indicators", {}),
        lstm_details=ensemble_result.get("lstm_details", {}),
        sentiment_details=ensemble_result.get("sentiment_details", {}),
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

    # Run check
    shariah_res = run_shariah_check(symbol_upper)

    # Save or update cache in DB
    cached_db = db.query(ShariahCache).filter(ShariahCache.symbol == symbol_upper).first()
    if cached_db:
        cached_db.status = shariah_res["status"]
        cached_db.score = shariah_res["score"]
        cached_db.debt_ratio = shariah_res["debt_ratio"]
        cached_db.haram_revenue = shariah_res["haram_revenue"]
        cached_db.business_type = shariah_res["business_type"]
        cached_db.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cached_db)
        return cached_db
    else:
        new_cache = ShariahCache(
            symbol=symbol_upper,
            status=shariah_res["status"],
            score=shariah_res["score"],
            debt_ratio=shariah_res["debt_ratio"],
            haram_revenue=shariah_res["haram_revenue"],
            business_type=shariah_res["business_type"]
        )
        db.add(new_cache)
        db.commit()
        db.refresh(new_cache)
        return new_cache

@router.get("/{symbol}/history", response_model=List[PredictionOut])
def get_prediction_history(symbol: str, db: Session = Depends(get_db)):
    """Return historical cached predictions for a given stock symbol to track accuracy."""
    symbol_upper = symbol.upper().strip()
    history = db.query(Prediction).filter(
        Prediction.symbol == symbol_upper
    ).order_by(Prediction.created_at.desc()).limit(10).all()
    return history

