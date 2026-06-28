from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.user import User
from backend.models.watchlist import Watchlist
from backend.schemas.watchlist import WatchlistCreate, WatchlistOut
from backend.schemas.stocks import StockSearchItem
from backend.services.auth import get_current_user
from backend.services.stock_data import get_stock_info

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

@router.get("/", response_model=List[StockSearchItem])
def get_watchlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    results = []
    for item in db_items:
        info = get_stock_info(item.symbol)
        results.append({
            "symbol": item.symbol,
            "name": info["name"],
            "price": info["price"],
            "change": info["change_pct"],
            "sector": info["sector"],
            "shariah_status": info["shariah_status"],
            "ai_score": info["ai_score"],
            "verdict": info["verdict"],
            "email_alerts": item.email_alerts
        })
    return results

@router.post("/", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    item_in: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    symbol_upper = item_in.symbol.upper().strip()
    
    # Check if stock exists/valid
    info = get_stock_info(symbol_upper)
    if not info:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock symbol {symbol_upper} is invalid."
         )

    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol_upper
    ).first()
    
    if existing:
        return existing

    new_item = Watchlist(
        user_id=current_user.id,
        symbol=symbol_upper
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def delete_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    symbol_upper = symbol.upper().strip()
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol_upper
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in watchlist"
        )
        
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{symbol}/toggle-alert", response_model=WatchlistOut)
def toggle_watchlist_alert(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    symbol_upper = symbol.upper().strip()
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.symbol == symbol_upper
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in watchlist"
        )
        
    item.email_alerts = not item.email_alerts
    db.commit()
    db.refresh(item)
    return item

