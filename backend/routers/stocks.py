from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional
from backend.schemas.stocks import StockSearchItem, StockDetailOut, StockHistoryOut
from backend.services.stock_data import (
    get_stock_info,
    get_history,
    search_stocks,
    get_screener_stocks,
    get_top_picks
)

router = APIRouter(prefix="/stocks", tags=["stocks"])

@router.get("/search", response_model=List[StockSearchItem])
def search(q: str = Query(..., min_length=1)):
    return search_stocks(q)

@router.get("/screener", response_model=List[StockDetailOut])
def screener(
    sector: str = "all",
    shariah: str = "all",
    rating: str = "all",
    q: str = ""
):
    filters = {
        "sector": sector,
        "shariah": shariah,
        "rating": rating,
        "q": q
    }
    return get_screener_stocks(filters)

@router.get("/top-picks", response_model=List[StockDetailOut])
def top_picks():
    return get_top_picks()

@router.get("/{symbol}", response_model=StockDetailOut)
def stock_detail(symbol: str):
    info = get_stock_info(symbol)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol} not found"
        )
    return info

@router.get("/{symbol}/history", response_model=StockHistoryOut)
def stock_history(symbol: str, period: str = "1y"):
    history_items = get_history(symbol, period)
    return {
        "symbol": symbol.upper(),
        "history": history_items
    }
