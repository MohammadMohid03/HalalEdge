from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PredictionOut(BaseModel):
    symbol: str
    verdict: str
    confidence: int
    lstm_score: int
    sentiment: int
    shariah_score: int
    ensemble: int
    created_at: datetime

    class Config:
        from_attributes = True

class ShariahOut(BaseModel):
    symbol: str
    status: str
    score: int
    debt_ratio: float
    haram_revenue: float
    business_type: str
    updated_at: datetime

    class Config:
        from_attributes = True
