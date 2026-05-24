from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models.prediction import Prediction
from backend.models.shariah import ShariahCache
from backend.schemas.predictions import PredictionOut, ShariahOut
from backend.services.stock_data import get_stock_info
from backend.services.shariah import check_shariah as run_shariah_check

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

    # Fetch live info (contains AI and shariah metrics)
    info = get_stock_info(symbol_upper)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Predictions not available for symbol {symbol_upper}."
        )

    # Simple mock breakdown of ensemble components matching the metadata/roadmap
    import random
    random.seed(symbol_upper) # Deterministic scores per stock
    lstm_score = info["ai_score"] - random.randint(-5, 5)
    sentiment = info["ai_score"] + random.randint(-5, 5)
    shariah_score = info["shariah_score"]
    ensemble = info["ai_score"]
    confidence = random.randint(75, 95)

    # Save to database cache
    new_pred = Prediction(
        symbol=symbol_upper,
        verdict=info["verdict"],
        confidence=confidence,
        lstm_score=lstm_score,
        sentiment=sentiment,
        shariah_score=shariah_score,
        ensemble=ensemble
    )
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)
    return new_pred

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
