from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
import io
import csv

from backend.database import get_db
from backend.models.user import User
from backend.models.portfolio import Holding
from backend.schemas.portfolio import (
    HoldingCreate,
    HoldingUpdate,
    HoldingOut,
    HoldingDetailOut,
    PortfolioSummary
)
from backend.services.auth import get_current_user
from backend.services.stock_data import get_stock_info

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/", response_model=List[HoldingDetailOut])
def get_holdings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    details = []
    for h in db_holdings:
        info = get_stock_info(h.symbol)
        current_price = info["price"]
        shares_f = float(h.shares)
        avg_price_f = float(h.avg_price)
        total_val = shares_f * current_price
        cost = shares_f * avg_price_f
        pl = total_val - cost
        pl_pct = (pl / cost * 100) if cost > 0 else 0.0

        details.append({
            "id": h.id,
            "symbol": h.symbol,
            "shares": shares_f,
            "avg_price": avg_price_f,
            "current_price": current_price,
            "total_value": round(total_val, 2),
            "cost_basis": round(cost, 2),
            "pl_abs": round(pl, 2),
            "pl_pct": round(pl_pct, 2),
            "ai_score": info["ai_score"],
            "shariah_status": info["shariah_status"],
            "sector": info["sector"],
            "company_name": info["name"],
            "color": info["color"]
        })
    return details

@router.post("/", response_model=HoldingOut, status_code=status.HTTP_201_CREATED)
def add_holding(holding_in: HoldingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Standardise symbol
    symbol_upper = holding_in.symbol.upper().strip()
    
    # Verify stock exists or is valid
    info = get_stock_info(symbol_upper)
    if not info:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock symbol {symbol_upper} is invalid or could not be verified."
         )

    # Check if they already own it, if so, we can average in
    existing = db.query(Holding).filter(Holding.user_id == current_user.id, Holding.symbol == symbol_upper).first()
    if existing:
        total_shares = float(existing.shares) + float(holding_in.shares)
        total_cost = (float(existing.shares) * float(existing.avg_price)) + (float(holding_in.shares) * float(holding_in.avg_price))
        existing.avg_price = total_cost / total_shares if total_shares > 0 else 0.0
        existing.shares = total_shares
        db.commit()
        db.refresh(existing)
        return existing

    new_holding = Holding(
        user_id=current_user.id,
        symbol=symbol_upper,
        shares=holding_in.shares,
        avg_price=holding_in.avg_price
    )
    db.add(new_holding)
    db.commit()
    db.refresh(new_holding)
    return new_holding

@router.put("/{holding_id}", response_model=HoldingOut)
def update_holding(
    holding_id: str,
    holding_in: HoldingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )

    if holding_in.shares is not None:
        holding.shares = holding_in.shares
    if holding_in.avg_price is not None:
        holding.avg_price = holding_in.avg_price

    db.commit()
    db.refresh(holding)
    return holding

@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    holding_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == current_user.id).first()
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    db.delete(holding)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/summary", response_model=PortfolioSummary)
def get_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    holdings_details = get_holdings(current_user, db)
    
    total_val = sum(h["total_value"] for h in holdings_details)
    total_cost = sum(h["cost_basis"] for h in holdings_details)
    total_gain_abs = total_val - total_cost
    total_gain_pct = (total_gain_abs / total_cost * 100) if total_cost > 0 else 0.0
    
    # Calculate a random/simulated daily gain for aesthetics matching the dashboard
    import random
    random.seed(current_user.email) # Deterministic for user
    today_gain_abs = total_val * (random.uniform(-0.02, 0.035))

    return {
        "total_value": round(total_val, 2),
        "total_cost": round(total_cost, 2),
        "total_gain_abs": round(total_gain_abs, 2),
        "total_gain_pct": round(total_gain_pct, 2),
        "today_gain_abs": round(today_gain_abs, 2),
        "holdings_count": len(holdings_details),
        "holdings": holdings_details
    }

@router.get("/export")
def export_portfolio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    holdings_details = get_holdings(current_user, db)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Symbol", "Company Name", "Shares", "Avg Purchase Price ($)", 
        "Current Price ($)", "Total Value ($)", "Total Gain/Loss ($)", 
        "Gain/Loss (%)", "Shariah Status", "AI Score"
    ])
    
    for h in holdings_details:
        writer.writerow([
            h["symbol"], h["company_name"], h["shares"], h["avg_price"],
            h["current_price"], h["total_value"], h["pl_abs"],
            h["pl_pct"], h["shariah_status"], h["ai_score"]
        ])
        
    csv_content = output.getvalue()
    output.close()
    
    headers = {
        "Content-Disposition": f"attachment; filename=noorinvest_portfolio_{current_user.full_name.replace(' ', '_')}.csv"
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)
