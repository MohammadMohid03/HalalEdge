import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import time
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from backend.services.shariah import check_shariah

# In-memory cache for stock information to prevent excessive yfinance API calls and speed up loads
_stock_info_cache = {}
_stock_history_cache = {}
# Caches for the dynamic screener universe (S&P 500 constituents + batch prices)
_sp500_cache = None  # (fetch_time, list[dict]) — refreshed daily
_sp500_cache_ttl = 24 * 3600
_screener_universe_cache = None  # (fetch_time, list[dict]) — refreshed every 5 min
_screener_universe_cache_ttl = 300

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

    metadata = STOCK_METADATA.get(symbol_upper, {})
    name = metadata.get("name", symbol_upper)
    sector = metadata.get("sector", "Unknown")
    color = metadata.get("color", "#0ea5e9")
    ai_score = metadata.get("ai_score", 70)
    verdict = metadata.get("verdict", "HOLD")

    # Try to load real AI score and verdict from database cache if available
    if symbol_upper not in STOCK_METADATA:
        try:
            from backend.database import SessionLocal
            from backend.models.prediction import Prediction
            db = SessionLocal()
            cached_pred = db.query(Prediction).filter(
                Prediction.symbol == symbol_upper
            ).order_by(Prediction.created_at.desc()).first()
            if cached_pred:
                ai_score = cached_pred.ensemble
                verdict = cached_pred.verdict
            db.close()
        except Exception as e:
            print(f"Error querying prediction cache for {symbol_upper}: {e}")


    # Fetch dynamic data from yfinance
    price = 100.0
    change = 0.0
    change_pct = 0.0
    market_cap = 1000000000.0
    pe_ratio = 15.0
    volume = 100000.0
    fifty_two_w_high = 120.0
    fifty_two_w_low = 80.0
    industry = metadata.get("industry", "General Services")

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
        name = info.get("longName") or info.get("shortName") or metadata.get("name", name)
    except Exception as e:
        print(f"Error fetching yfinance for {symbol_upper}: {e}")
        # Fallbacks for mock data prices
        if symbol_upper in STOCK_METADATA:
            # Simple pseudo-live price simulation if offline
            price = 150.0
            name = metadata.get("name", symbol_upper)
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
        "ai_score": ai_score,
        "verdict": verdict,
        "color": color
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
                "shariah_status": info["shariah_status"],
                "ai_score": info["ai_score"],
                "verdict": info["verdict"]
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
                    "shariah_status": info["shariah_status"],
                    "ai_score": info["ai_score"],
                    "verdict": info["verdict"]
                })
    except Exception:
        pass

    return results

# ── Dynamic screener universe (S&P 500 via Wikipedia + batch yfinance) ────────
_GICS_SECTOR_MAP = {
    "Information Technology": "Technology",
    "Health Care": "Healthcare",
    "Consumer Discretionary": "Consumer",
    "Consumer Staples": "Consumer",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Financials": "Financials",
    "Materials": "Materials",
    "Real Estate": "Real Estate",
    "Communication Services": "Communication",
    "Utilities": "Utilities",
}

# Base shariah scores per GICS sector (used for stocks without mock compliance data)
_SECTOR_BASE_SHARIAH = {
    "Information Technology": 75,
    "Health Care": 70,
    "Consumer Discretionary": 70,
    "Consumer Staples": 78,
    "Industrials": 72,
    "Energy": 68,
    "Materials": 70,
    "Communication Services": 65,
    "Utilities": 72,
    "Real Estate": 58,
    "Financials": 50,
}


def _color_from_symbol(symbol: str) -> str:
    h = hashlib.md5(symbol.encode()).hexdigest()
    return f"#{h[0:2]}{h[2:4]}{h[4:6]}"


def _get_sp500_constituents() -> List[dict]:
    """Fetch the current S&P 500 constituent list from Wikipedia (cached 24h)."""
    global _sp500_cache
    if _sp500_cache and (time.time() - _sp500_cache[0]) < _sp500_cache_ttl:
        return _sp500_cache[1]
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; HalalEdgeScreener/1.0)"}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = None
        for tbl in soup.find_all("table"):
            header_row = tbl.find("tr")
            if not header_row:
                continue
            header_texts = [c.get_text(strip=True).lower() for c in header_row.find_all(["th", "td"])]
            if "symbol" in header_texts:
                table = tbl
                break
        if not table:
            return []
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []
        headers = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]
        sym_idx = headers.index("symbol") if "symbol" in headers else 0
        name_idx = headers.index("security") if "security" in headers else sym_idx
        sector_idx = next((i for i, h in enumerate(headers) if "sector" in h), None)
        sub_idx = next((i for i, h in enumerate(headers) if "sub" in h and "industry" in h), None)

        constituents = []
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            needed = [i for i in [sym_idx, name_idx, sector_idx, sub_idx] if i is not None]
            if not needed or len(cells) <= max(needed):
                continue
            raw_sym = cells[sym_idx].get_text(strip=True).upper()
            sym = re.sub(r"[^A-Z0-9.\-]", "", raw_sym).replace(".", "-")
            if not sym:
                continue
            name = cells[name_idx].get_text(strip=True) if name_idx is not None else sym
            sector = cells[sector_idx].get_text(strip=True) if sector_idx is not None else ""
            industry = cells[sub_idx].get_text(strip=True) if sub_idx is not None else ""
            constituents.append({
                "symbol": sym,
                "name": name,
                "gics_sector": sector,
                "industry": industry,
            })
        _sp500_cache = (time.time(), constituents)
        return constituents
    except Exception as e:
        print(f"Error fetching S&P 500 constituents: {e}")
        return []


def _parse_hist_block(block) -> Optional[dict]:
    """Extract latest price/change/volume from a yfinance history DataFrame block."""
    try:
        block = block.dropna(subset=["Close"])
        if block.empty:
            return None
        closes = block["Close"].values
        vols = block["Volume"].values
        price = float(closes[-1])
        prev = float(closes[-2]) if len(closes) >= 2 else price
        change = price - prev
        change_pct = (change / prev) * 100.0 if prev else 0.0
        vol = float(vols[-1]) if len(vols) and not pd.isna(vols[-1]) else 0.0
        return {
            "price": round(price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": vol,
        }
    except Exception:
        return None


def _get_batch_prices(symbols: List[str]) -> dict:
    """Batch-fetch recent prices for many tickers via yf.download (chunked)."""
    if not symbols:
        return {}
    result = {}
    chunk_size = 100
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i + chunk_size]
        try:
            data = yf.download(chunk, period="5d", interval="1d", group_by="ticker", progress=False, threads=True)
            if data is None or getattr(data, "empty", True):
                continue
            if len(chunk) == 1:
                sym = chunk[0]
                block = data[sym] if isinstance(data.columns, pd.MultiIndex) else data
                parsed = _parse_hist_block(block)
                if parsed:
                    result[sym] = parsed
            else:
                for sym in chunk:
                    try:
                        parsed = _parse_hist_block(data[sym])
                        if parsed:
                            result[sym] = parsed
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error downloading price chunk {i}-{i + len(chunk)}: {e}")
            continue
    return result


def _fetch_single_stock_detail(symbol: str) -> dict:
    """Fetch market_cap, PE, 52w high/low, sector, industry, name from yfinance .info for one symbol."""
    try:
        info = yf.Ticker(symbol).info
        return {
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "name": info.get("longName") or info.get("shortName"),
        }
    except Exception:
        return {}


def _get_batch_stock_details(symbols: List[str]) -> dict:
    """Fetch stock details (market cap, PE, 52w range, etc.) for many tickers in parallel."""
    if not symbols:
        return {}
    result = {}
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(_fetch_single_stock_detail, sym): sym for sym in symbols}
        for future in futures:
            sym = futures[future]
            try:
                details = future.result()
                if details:
                    result[sym] = details
            except Exception:
                continue
    return result


def _shariah_heuristic(gics_sector: str, industry: str) -> dict:
    """Lightweight shariah estimate from GICS sector/sub-industry (no yfinance call)."""
    sector_lower = gics_sector.lower()
    industry_lower = industry.lower()
    if any(k in industry_lower for k in ["alcohol", "wineries", "distiller", "tobacco", "gambling", "casino", "brewing"]):
        return {"status": "Haram", "score": 30}
    if "defense" in industry_lower:
        return {"status": "Doubtful", "score": 52}
    score = _SECTOR_BASE_SHARIAH.get(gics_sector, 70)
    status = "Doubtful" if ("financial" in sector_lower or "real estate" in sector_lower) else "Halal"
    return {"status": status, "score": score}


def _ai_score_from_momentum(change_pct: float, base: int = 68) -> tuple:
    """Derive a dynamic AI score/verdict from recent price momentum."""
    score = int(max(35, min(95, base + change_pct * 3)))
    verdict = "BUY" if score >= 75 else "AVOID" if score < 50 else "HOLD"
    return score, verdict


def _get_extended_screener_stocks() -> List[dict]:
    """Build screener data for S&P 500 stocks beyond STOCK_METADATA (dynamic, cached 5 min)."""
    global _screener_universe_cache
    if _screener_universe_cache and (time.time() - _screener_universe_cache[0]) < _screener_universe_cache_ttl:
        return _screener_universe_cache[1]

    constituents = _get_sp500_constituents()
    extended = [c for c in constituents if c["symbol"] not in STOCK_METADATA]
    if not extended:
        return []

    symbols = [c["symbol"] for c in extended]
    batch_prices = _get_batch_prices(symbols)
    batch_details = _get_batch_stock_details(symbols)

    results = []
    for c in extended:
        sym = c["symbol"]
        px = batch_prices.get(sym)
        if not px:
            continue
        det = batch_details.get(sym, {})
        mapped_sector = _GICS_SECTOR_MAP.get(c["gics_sector"], c["gics_sector"] or "Unknown")
        sector = det.get("sector") or mapped_sector
        sh = _shariah_heuristic(c["gics_sector"], c["industry"])
        ai_score, verdict = _ai_score_from_momentum(px["change_pct"])
        market_cap = det.get("market_cap")
        fifty_two_w_high = det.get("fifty_two_week_high")
        fifty_two_w_low = det.get("fifty_two_week_low")
        pe_ratio = det.get("pe_ratio")
        results.append({
            "symbol": sym,
            "name": det.get("name") or c["name"],
            "price": px["price"],
            "change": px["change"],
            "change_pct": px["change_pct"],
            "market_cap": market_cap if market_cap else None,
            "pe_ratio": round(float(pe_ratio), 2) if pe_ratio else None,
            "volume": px["volume"],
            "fifty_two_week_high": round(float(fifty_two_w_high), 2) if fifty_two_w_high else None,
            "fifty_two_week_low": round(float(fifty_two_w_low), 2) if fifty_two_w_low else None,
            "sector": sector,
            "industry": det.get("industry") or c["industry"] or sector,
            "shariah_status": sh["status"],
            "shariah_score": sh["score"],
            "ai_score": ai_score,
            "verdict": verdict,
            "color": _color_from_symbol(sym),
        })

    _screener_universe_cache = (time.time(), results)
    return results


def get_screener_stocks(filters: dict) -> List[dict]:
    # Featured stocks from STOCK_METADATA (rich data, fetched in parallel, cached per-stock)
    with ThreadPoolExecutor(max_workers=8) as ex:
        all_screened = list(ex.map(get_stock_info, list(STOCK_METADATA.keys())))
    # Extended universe: S&P 500 constituents fetched dynamically via yfinance
    all_screened.extend(_get_extended_screener_stocks())

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


def get_technical_indicators(symbol: str) -> dict:
    """Calculate technical indicators for a given stock symbol.

    Returns:
        dict with keys:
            rsi (float): 14-day Relative Strength Index (0-100)
            momentum_52w (float): 52-week price momentum as percentage (0-100)
            volume_trend (float): 5-day avg volume / 20-day avg volume ratio
            beta (float): stock beta from yfinance info
            sma20 (float): 20-day Simple Moving Average
            sma50 (float): 50-day Simple Moving Average
            current_price (float): latest close price
            pe_ratio (float): trailing P/E ratio
    """
    symbol_upper = symbol.upper().strip()

    # Default values
    indicators = {
        "rsi": 50.0,
        "momentum_52w": 50.0,
        "volume_trend": 1.0,
        "beta": 1.0,
        "sma20": 0.0,
        "sma50": 0.0,
        "current_price": 0.0,
        "pe_ratio": 0.0,
    }

    try:
        ticker = yf.Ticker(symbol_upper)

        # Fetch 1 year of daily data for calculations
        hist = ticker.history(period="1y", interval="1d")

        if hist is None or hist.empty or len(hist) < 20:
            return indicators

        closes = hist["Close"].values
        volumes = hist["Volume"].values
        current_price = float(closes[-1])
        indicators["current_price"] = round(current_price, 2)

        # --- RSI (14-day) ---
        if len(closes) >= 15:
            deltas = pd.Series(closes).diff()
            gains = deltas.where(deltas > 0, 0.0)
            losses = (-deltas).where(deltas < 0, 0.0)
            avg_gain = gains.rolling(window=14, min_periods=14).mean().iloc[-1]
            avg_loss = losses.rolling(window=14, min_periods=14).mean().iloc[-1]
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100.0  # No losses → fully overbought
            indicators["rsi"] = round(float(rsi), 2)

        # --- 52-week momentum ---
        high_52w = float(closes.max())
        low_52w = float(closes.min())
        if high_52w != low_52w:
            momentum = (current_price - low_52w) / (high_52w - low_52w) * 100
        else:
            momentum = 50.0
        indicators["momentum_52w"] = round(momentum, 2)

        # --- Volume trend (5-day avg / 20-day avg) ---
        if len(volumes) >= 20:
            avg_vol_5 = float(volumes[-5:].mean())
            avg_vol_20 = float(volumes[-20:].mean())
            if avg_vol_20 > 0:
                indicators["volume_trend"] = round(avg_vol_5 / avg_vol_20, 2)

        # --- SMA20 and SMA50 ---
        if len(closes) >= 20:
            indicators["sma20"] = round(float(closes[-20:].mean()), 2)
        if len(closes) >= 50:
            indicators["sma50"] = round(float(closes[-50:].mean()), 2)

        # --- Beta and PE ratio from yfinance info ---
        try:
            info = ticker.info
            indicators["beta"] = round(float(info.get("beta", 1.0) or 1.0), 2)
            indicators["pe_ratio"] = round(float(info.get("trailingPE", 0.0) or 0.0), 2)
        except Exception:
            pass  # Keep defaults

    except Exception as e:
        print(f"Error calculating technical indicators for {symbol_upper}: {e}")

    return indicators
