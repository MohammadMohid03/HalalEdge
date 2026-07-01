#!/usr/bin/env python3
"""
Offline ML pipeline runner for HalalEdge.

This script is meant to run on GitHub Actions (or locally). It:
  1. Loads the ensemble prediction pipeline (LSTM, sentiment, Shariah, technicals)
  2. Iterates over a list of stock symbols
  3. Generates predictions
  4. POSTs them in batches to the Render backend's /api/predictions/bulk-update endpoint

Environment variables:
  - PREDICTIONS_API_KEY: secret shared with the backend (required)
  - API_BASE: backend URL, default https://halaledge.onrender.com/api
  - MAX_SYMBOLS: limit number of symbols processed (default 200)
  - BATCH_SIZE: number of predictions per POST request (default 50)
"""

import os
import sys
import time
import argparse
import requests
from typing import List, Dict

# Add repository root so we can import backend modules
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.services.ensemble import get_ensemble_prediction

API_BASE = os.getenv("API_BASE", "https://halaledge.onrender.com/api").rstrip("/")
API_KEY = os.getenv("PREDICTIONS_API_KEY", "")
BULK_UPDATE_URL = f"{API_BASE}/predictions/bulk-update"

# Default symbol universe: the featured metadata stocks + top S&P 500 liquid names.
# The backend /stocks/screener endpoint could also be queried, but a stable list
# keeps the GitHub Actions job deterministic and fast.
DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "ADBE", "CRM", "INTC",
    "QCOM", "TXN", "ASML", "TSM", "JNJ", "UNH", "PFE", "ABT", "XOM", "CVX",
    "CAT", "BA", "COST", "WMT", "JPM", "V", "MA", "HD", "PG", "KO",
    "PEP", "MCD", "DIS", "NFLX", "AMD", "IBM", "GE", "F", "GM", "PYPL",
    "UBER", "LYFT", "ABNB", "SHOP", "SQ", "ROKU", "ZM", "DOCU", "SNOW", "CRWD",
    "PLTR", "PANW", "FTNT", "CYBR", "OKTA", "DDOG", "MDB", "NET", "FSLY", "TWLO",
    "SPGI", "BLK", "BX", "GS", "MS", "SCHW", "C", "BAC", "WFC", "USB",
    "AXP", "COF", "CME", "ICE", "MCO", "FIS", "VRSK", "INFO", "TRV", "AON",
    "MMC", "AJG", "PGR", "ALL", "HIG", "MET", "PRU", "AFL", "AIG", "BRK-B",
    "T", "VZ", "TMUS", "CMCSA", "CHTR", "DISH", "LUMN", "NWSA", "FOXA", "TRI",
    "OMC", "IPG", "WPP", "GOOG", "META", "TT", "ITW", "HON", "UPS", "FDX",
    "CSX", "UNP", "NSC", "LMT", "NOC", "RTX", "GD", "TDG", "HEI", "TXT",
    "DE", "AGCO", "CNHI", "PCAR", "OSK", "CMI", "ETN", "EMR", "ROK", "AME",
    "PH", "SWK", "SNA", "FAST", "GWW", "MSC", "DOV", "IEX", "PNR", "ITT",
    "XYL", "AQUA", "WAT", "TMO", "DHR", "ABT", "BMY", "MRK", "LLY", "VRTX",
]


def get_symbols(max_symbols: int) -> List[str]:
    """Return the symbol list, optionally capped."""
    symbols = list(dict.fromkeys(DEFAULT_SYMBOLS))  # remove duplicates, keep order
    return symbols[:max_symbols]


def predict_symbol(symbol: str) -> Dict:
    """Run the ensemble pipeline for one symbol and format the payload."""
    symbol = symbol.upper().strip()
    print(f"[predict] {symbol} ...", flush=True)
    start = time.time()

    result = get_ensemble_prediction(symbol)

    payload = {
        "symbol": symbol,
        "verdict": result.get("verdict", "HOLD"),
        "confidence": result.get("confidence", 0),
        "lstm_score": result.get("lstm_score", 0),
        "sentiment": result.get("sentiment_score", 0),
        "shariah_score": result.get("shariah_score", 0),
        "ensemble": result.get("ensemble_score", 0),
        "target_bull": result.get("lstm_details", {}).get("predicted_price", 0),
        "target_bear": result.get("lstm_details", {}).get("current_price", 0) * 0.90,
        "details": {
            "technical_indicators": result.get("technical_indicators", {}),
            "lstm_details": result.get("lstm_details", {}),
            "sentiment_details": result.get("sentiment_details", {}),
        },
    }

    print(f"[predict] {symbol} done in {time.time() - start:.1f}s -> {payload['verdict']} ({payload['ensemble']})", flush=True)
    return payload


def post_batch(batch: List[Dict], retries: int = 3) -> bool:
    """POST a batch of predictions to the backend with retries."""
    if not API_KEY:
        raise RuntimeError("PREDICTIONS_API_KEY environment variable is not set")

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                BULK_UPDATE_URL,
                json=batch,
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                timeout=120,
            )
            if resp.status_code == 200:
                print(f"[post] batch saved ({len(batch)} items): {resp.json()}", flush=True)
                return True
            print(f"[post] attempt {attempt} failed: {resp.status_code} {resp.text[:200]}", flush=True)
        except Exception as e:
            print(f"[post] attempt {attempt} error: {e}", flush=True)

        if attempt < retries:
            time.sleep(10 * attempt)

    return False


def main():
    parser = argparse.ArgumentParser(description="Run HalalEdge ML pipeline offline")
    parser.add_argument("--max-symbols", type=int, default=int(os.getenv("MAX_SYMBOLS", "200")), help="Max symbols to process")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("BATCH_SIZE", "50")), help="Bulk-update batch size")
    parser.add_argument("--offset", type=int, default=0, help="Start offset in symbol list (for parallel jobs)")
    parser.add_argument("--limit", type=int, default=0, help="Max symbols for this job (0 = use max-symbols - offset)")
    args = parser.parse_args()

    symbols = get_symbols(args.max_symbols)

    if args.offset:
        symbols = symbols[args.offset:]
    if args.limit:
        symbols = symbols[:args.limit]

    if not symbols:
        print("[main] no symbols to process", flush=True)
        return

    print(f"[main] processing {len(symbols)} symbols, batch size {args.batch_size}", flush=True)

    batch: List[Dict] = []
    failed_symbols = []

    for symbol in symbols:
        try:
            payload = predict_symbol(symbol)
            batch.append(payload)

            if len(batch) >= args.batch_size:
                if not post_batch(batch):
                    failed_symbols.extend([b["symbol"] for b in batch])
                batch = []
        except Exception as e:
            print(f"[main] failed to predict {symbol}: {e}", flush=True)
            failed_symbols.append(symbol)

    if batch:
        if not post_batch(batch):
            failed_symbols.extend([b["symbol"] for b in batch])

    print(f"[main] done. failed: {len(failed_symbols)} {failed_symbols}", flush=True)
    if failed_symbols:
        sys.exit(1)


if __name__ == "__main__":
    main()
