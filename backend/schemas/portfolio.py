from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class HoldingBase(BaseModel):
    symbol: str
    shares: Decimal
    avg_price: Decimal

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    shares: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None

class HoldingOut(HoldingBase):
    id: UUID
    user_id: UUID
    added_at: datetime

    class Config:
        from_attributes = True

class HoldingDetailOut(BaseModel):
    id: UUID
    symbol: str
    shares: float
    avg_price: float
    current_price: float
    total_value: float
    cost_basis: float
    pl_abs: float
    pl_pct: float
    ai_score: int
    shariah_status: str
    sector: str
    company_name: str
    color: str

class PortfolioSummary(BaseModel):
    total_value: float
    total_cost: float
    total_gain_abs: float
    total_gain_pct: float
    today_gain_abs: float
    holdings_count: int
    holdings: List[HoldingDetailOut]
