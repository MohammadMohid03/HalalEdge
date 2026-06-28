from pydantic import BaseModel
from typing import List, Optional

class StockSearchItem(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    sector: str
    shariah_status: str
    ai_score: int
    verdict: str
    email_alerts: Optional[bool] = False



class StockDetailOut(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    sector: str
    industry: str
    shariah_status: str
    shariah_score: int
    ai_score: int
    verdict: str
    color: Optional[str] = None

class StockHistoryItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockHistoryOut(BaseModel):
    symbol: str
    history: List[StockHistoryItem]


class StockDetailBatchItem(BaseModel):
    symbol: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    ai_score: Optional[int] = None
    verdict: Optional[str] = None
