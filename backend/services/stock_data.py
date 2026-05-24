import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
from backend.services.shariah import check_shariah

# In-memory cache for stock information to prevent excessive yfinance API calls and speed up loads
_stock_info_cache = {}
_stock_history_cache = {}

# Mock details from frontend design system
STOCK_METADATA = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "color": "#1d4ed8", "ai_score": 87, "verdict": "BUY"},
    "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "color": "#0ea5e9", "ai_score": 84, "verdict": "BUY"},
    "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "color": "#76c442", "ai_score": 91, "verdict": "BUY"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "color": "#f59e0b", "ai_score": 73, "verdict": "HOLD"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer", "color": "#f97316", "ai_score": 82, "verdict": "BUY"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer", "color": "#e11d48", "ai_score": 61, "verdict": "HOLD"},
    "META": {"name": "Meta Platforms", "sector": "Technology", "color": "#6366f1", "ai_score": 78, "verdict": "BUY"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Technology", "color": "#ec4899", "ai_score": 69, "verdict": "HOLD"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Technology", "color": "#06b6d4", "ai_score": 76, "verdict": "BUY"},
    "INTC": {"name": "Intel Corp.", "sector": "Technology", "color": "#64748b", "ai_score": 48, "verdict": "AVOID"},
    "QCOM": {"name": "Qualcomm Inc.", "sector": "Technology", "color": "#8b5cf6", "ai_score": 80, "verdict": "BUY"},
    "TXN": {"name": "Texas Instruments", "sector": "Technology", "color": "#14b8a6", "ai_score": 74, "verdict": "HOLD"},
    "ASML": {"name": "ASML Holding NV", "sector": "Technology", "color": "#f59e0b", "ai_score": 88, "verdict": "BUY"},
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Technology", "color": "#0ea5e9", "ai_score": 85, "verdict": "BUY"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "color": "#dc2626", "ai_score": 71, "verdict": "HOLD"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Healthcare", "color": "#2563eb", "ai_score": 66, "verdict": "HOLD"},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare", "color": "#7c3aed", "ai_score": 52, "verdict": "AVOID"},
    "ABT": {"name": "Abbott Laboratories", "sector": "Healthcare", "color": "#059669", "ai_score": 75, "verdict": "BUY"},
    "XOM": {"name": "ExxonMobil Corp.", "sector": "Energy", "color": "#92400e", "ai_score": 72, "verdict": "HOLD"},
    "CVX": {"name": "Chevron Corp.", "sector": "Energy", "color": "#b45309", "ai_score": 69, "verdict": "HOLD"},
    "CAT": {"name": "Caterpillar Inc.", "sector": "Industrials", "color": "#d97706", "ai_score": 81, "verdict": "BUY"},
    "BA": {"name": "Boeing Co.", "sector": "Industrials", "color": "#64748b", "ai_score": 45, "verdict": "AVOID"},
    "COST": {"name": "Costco Wholesale", "sector": "Consumer", "color": "#e11d48", "ai_score": 83, "verdict": "BUY"},
    "WMT": {"name": "Walmart Inc.", "sector": "Consumer", "color": "#1d4ed8", "ai_score": 77, "verdict": "HOLD"},
}

def get_stock_info(symbol: str) -> dict:
    symbol_upper = symbol.upper()

    # Return cached if valid and not expired (e.g. cached within last 5 minutes)
    if symbol_upper in _stock_info_cache:
        cached_time, cached_val = _stock_info_cache[symbol_upper]
        if datetime.now() - cached_time < timedelta(minutes=5):
            return cached_val

    metadata = STOCK_METADATA.get(symbol_upper, {
        "name": symbol_upper,
        "sector": "Unknown",
        "color": "#0ea5e9",
        "ai_score": 70,
        "verdict": "HOLD"
    })

    # Fetch dynamic data from yfinance
    price = 100.0
    change = 0.0
    change_pct = 0.0
    market_cap = 1000000000.0
    pe_ratio = 15.0
    volume = 100000.0
    fifty_two_w_high = 120.0
    fifty_two_w_low = 80.0
    industry = "General Services"
    sector = metadata["sector"]

    try:
        ticker = yf.Ticker(symbol_upper)
        info = ticker.info
        
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice") or price
        
        # Calculate regular market change/percent
        prev_close = info.get("regularMarketPreviousClose")
        if prev_close and price:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = info.get("regularMarketChange") or 0.0
            change_pct = info.get("regularMarketChangePercent") or 0.0

        market_cap = info.get("marketCap") or market_cap
        pe_ratio = info.get("trailingPE") or pe_ratio
        volume = info.get("regularMarketVolume") or volume
        fifty_two_w_high = info.get("fiftyTwoWeekHigh") or fifty_two_w_high
        fifty_two_w_low = info.get("fiftyTwoWeekLow") or fifty_two_w_low
        industry = info.get("industry") or industry
        sector = info.get("sector") or sector
        name = info.get("longName") or info.get("shortName") or metadata["name"]
    except Exception as e:
        print(f"Error fetching yfinance for {symbol_upper}: {e}")
        # Fallbacks for mock data prices
        if symbol_upper in STOCK_METADATA:
            # Simple pseudo-live price simulation if offline
            price = 150.0
            name = metadata["name"]
        else:
            name = symbol_upper

    shariah = check_shariah(symbol_upper)

    res = {
        "symbol": symbol_upper,
        "name": name,
        "price": round(float(price), 2),
        "change": round(float(change), 2),
        "change_pct": round(float(change_pct), 2),
        "market_cap": market_cap,
        "pe_ratio": round(float(pe_ratio), 2) if pe_ratio else None,
        "volume": volume,
        "fifty_two_week_high": round(float(fifty_two_w_high), 2),
        "fifty_two_week_low": round(float(fifty_two_w_low), 2),
        "sector": sector,
        "industry": industry,
        "shariah_status": shariah["status"],
        "shariah_score": shariah["score"],
        "ai_score": metadata["ai_score"],
        "verdict": metadata["verdict"],
        "color": metadata["color"]
    }

    _stock_info_cache[symbol_upper] = (datetime.now(), res)
    return res

def get_history(symbol: str, period: str = "1y") -> List[dict]:
    symbol_upper = symbol.upper()
    cache_key = f"{symbol_upper}_{period}"

    if cache_key in _stock_history_cache:
        cached_time, cached_val = _stock_history_cache[cache_key]
        if datetime.now() - cached_time < timedelta(hours=1):
            return cached_val

    # Translate frontend periods to yfinance periods
    yf_period = "1y"
    if period == "1D":
        yf_period = "1d"
    elif period == "1W":
        yf_period = "5d"
    elif period == "1M":
        yf_period = "1mo"
    elif period == "3M":
        yf_period = "3mo"
    elif period == "1Y":
        yf_period = "1y"

    history_items = []
    try:
        ticker = yf.Ticker(symbol_upper)
        # Fetch appropriate interval based on period
        interval = "1m" if period == "1D" else "15m" if period == "1W" else "1d"
        hist = ticker.history(period=yf_period, interval=interval)

        if not hist.empty:
            for idx, row in hist.iterrows():
                # Formats index (Datetime) as string
                date_str = idx.strftime("%Y-%m-%d %H:%M:%S") if isinstance(idx, pd.Timestamp) else str(idx)
                history_items.append({
                    "date": date_str,
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"])
                })
    except Exception as e:
        print(f"Error fetching history for {symbol_upper}: {e}")
        # Build synthetic history
        base_price = 100.0
        if symbol_upper in STOCK_METADATA:
            # Estimate a base price
            base_price = 150.0
        
        pts = 48 if period == "1D" else 7 if period == "1W" else 30 if period == "1M" else 90 if period == "3M" else 250
        now = datetime.now()
        for i in range(pts):
            d = now - timedelta(days=(pts-i))
            history_items.append({
                "date": d.strftime("%Y-%m-%d"),
                "open": base_price,
                "high": base_price + 2.0,
                "low": base_price - 2.0,
                "close": base_price + 0.5,
                "volume": 500000
            })

    _stock_history_cache[cache_key] = (datetime.now(), history_items)
    return history_items

def search_stocks(query: str) -> List[dict]:
    query_lower = query.lower().strip()
    results = []
    
    # Check mock database first
    for sym, meta in STOCK_METADATA.items():
        if query_lower in sym.lower() or query_lower in meta["name"].lower():
            info = get_stock_info(sym)
            results.append({
                "symbol": sym,
                "name": meta["name"],
                "price": info["price"],
                "change": info["change_pct"],
                "sector": meta["sector"],
                "shariah_status": info["shariah_status"]
            })
            
    if len(results) >= 5:
        return results[:10]

    # If few results, look up via yfinance search API (ticker autocomplete)
    try:
        tickers = yf.Search(query).tickers
        for tick in tickers[:5]:
            sym = tick.get("symbol")
            if sym and sym not in STOCK_METADATA:
                info = get_stock_info(sym)
                results.append({
                    "symbol": sym,
                    "name": tick.get("name", sym),
                    "price": info["price"],
                    "change": info["change_pct"],
                    "sector": info["sector"],
                    "shariah_status": info["shariah_status"]
                })
    except Exception:
        pass

    return results

def get_screener_stocks(filters: dict) -> List[dict]:
    # Screener works primarily on our 24 mock stocks, plus dynamic query capabilities
    all_screened = []
    for sym in STOCK_METADATA.keys():
        all_screened.append(get_stock_info(sym))

    # Apply filters
    filtered = []
    for s in all_screened:
        # Shariah filter
        shariah_f = filters.get("shariah", "all")
        if shariah_f != "all" and s["shariah_status"].lower() != shariah_f.lower():
            continue
            
        # Sector filter
        sector_f = filters.get("sector", "all")
        if sector_f != "all" and s["sector"].lower() != sector_f.lower():
            continue

        # AI Rating filter
        rating_f = filters.get("rating", "all")
        if rating_f == "buy" and s["verdict"] != "BUY":
            continue
        elif rating_f == "hold" and s["verdict"] != "HOLD":
            continue
        elif rating_f == "avoid" and s["verdict"] != "AVOID":
            continue

        # Search Query filter
        q = filters.get("q", "")
        if q and (q.lower() not in s["symbol"].lower() and q.lower() not in s["name"].lower()):
            continue

        filtered.append(s)

    return filtered

def get_top_picks() -> List[dict]:
    # Top Picks defined as Halal stocks with highest AI scores
    all_stocks = [get_stock_info(sym) for sym in STOCK_METADATA.keys()]
    halal_stocks = [s for s in all_stocks if s["shariah_status"] == "Halal"]
    halal_stocks.sort(key=lambda x: x["ai_score"], reverse=True)
    return halal_stocks[:6]
