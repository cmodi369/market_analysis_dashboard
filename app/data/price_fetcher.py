"""Data fetching and caching for Nifty 50 market data using yfinance."""

import logging
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from app.config import NIFTY_TICKER, CACHE_DIR, CACHE_EXPIRY_HOURS

logger = logging.getLogger(__name__)

CACHE_PATH = Path(CACHE_DIR) / "nifty_market_data.parquet"
STATIC_PE_PATH = Path("data/static/historical_pe.csv")


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


def _is_cache_valid() -> bool:
    """Check if cached data exists and is fresh."""
    if not CACHE_PATH.exists():
        return False
    mod_time = datetime.fromtimestamp(CACHE_PATH.stat().st_mtime)
    return (datetime.now() - mod_time) < timedelta(hours=CACHE_EXPIRY_HOURS)


def fetch_nifty_data() -> pd.DataFrame:
    """Fetch Nifty 50 historical OHLCV data from yfinance."""
    logger.info("Fetching Nifty 50 data from yfinance...")
    ticker = yf.Ticker(NIFTY_TICKER)
    df = ticker.history(period="max")

    if df.empty:
        raise ValueError(f"No data returned from yfinance for {NIFTY_TICKER}")

    df = df.reset_index()
    # Normalize columns — yfinance may return MultiIndex or flat
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if c[1] == "" else c[0] for c in df.columns]

    keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[keep_cols].copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def fetch_real_pe_pb(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch real PE and PB ratios from niftyindices.com via web scraping.
    """
    url = "https://www.niftyindices.com/Backpage.aspx/getpepbHistoricaldataDBtoString"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://www.niftyindices.com",
        "Referer": "https://www.niftyindices.com/reports/historical-data",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Format dates as DD-Mon-YYYY
    start_str = start_date.strftime("%d-%b-%Y")
    end_str = end_date.strftime("%d-%b-%Y")

    logger.info(f"Scraping NSE PE/PB data from {start_str} to {end_str}...")

    payload = {
        "cinfo": f"{{'name':'NIFTY 50','startDate':'{start_str}','endDate':'{end_str}','indexName':'NIFTY 50'}}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result_json = response.json()
        if 'd' not in result_json:
            logger.error("NSE API response missing 'd' key")
            return pd.DataFrame()

        data_list = json.loads(result_json['d'])
        if not data_list:
            logger.warning(f"No PE/PB data found for range {start_str} to {end_str}")
            return pd.DataFrame()

        df = pd.DataFrame(data_list)
        
        # Column mapping: 'DATE' -> 'Date', 'pe' -> 'PE', 'pb' -> 'PB'
        df = df.rename(columns={"DATE": "Date", "pe": "PE", "pb": "PB"})
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.tz_localize(None)
        df["PE"] = pd.to_numeric(df["PE"], errors="coerce")
        df["PB"] = pd.to_numeric(df["PB"], errors="coerce")
        
        return df[["Date", "PE", "PB"]].dropna(subset=["Date"])
        
    except Exception as e:
        logger.error(f"Failed to fetch PE/PB data from NSE: {e}")
        raise RuntimeError(f"NSE Data Fetch Error: {e}")


def load_market_data(force_refresh: bool = False) -> pd.DataFrame:
    """
    Load Nifty 50 market data with real PE and PB columns.
    
    Tries to use cached parquet first. If refresh is needed, fetches price data
    and updates PE/PB from NSE scraping, saving to a persistent CSV.
    """
    _ensure_cache_dir()

    if not force_refresh and _is_cache_valid():
        logger.info("Loading from cache: %s", CACHE_PATH)
        return pd.read_parquet(CACHE_PATH)

    # 1. Fetch Price Data
    df = fetch_nifty_data()
    min_date = df["Date"].min()
    max_date = df["Date"].max()

    # 2. Load existing PE/PB data from static CSV
    existing_pe_df = pd.DataFrame(columns=["Date", "PE", "PB"])
    existing_pe_df["Date"] = pd.to_datetime(existing_pe_df["Date"]) # Ensure dtype
    if STATIC_PE_PATH.exists():
        try:
            existing_pe_df = pd.read_csv(STATIC_PE_PATH)
            existing_pe_df["Date"] = pd.to_datetime(existing_pe_df["Date"]).dt.tz_localize(None)
        except Exception as e:
            logger.warning(f"Could not load existing PE data: {e}")

    # 3. Determine if we need to fetch new PE/PB data
    # We fetch if missing records for recent price dates
    last_pe_date = existing_pe_df["Date"].max() if not existing_pe_df.empty else None
    
    if force_refresh or last_pe_date is None or last_pe_date < max_date:
        # Fetch in chunks to be safe, or just from last available date
        fetch_start = min_date if last_pe_date is None else last_pe_date + timedelta(days=1)
        
        # If the gap is huge (e.g., first run), fetch in yearly chunks
        fetch_end = max_date
        
        new_pe_data = []
        current_start = fetch_start
        while current_start <= fetch_end:
            current_end = min(current_start + timedelta(days=365*2), fetch_end)
            try:
                chunk_df = fetch_real_pe_pb(current_start, current_end)
                if not chunk_df.empty:
                    new_pe_data.append(chunk_df)
                current_start = current_end + timedelta(days=1)
            except Exception as e:
                logger.error(f"Error fetching chunk {current_start} to {current_end}: {e}")
                if not existing_pe_df.empty:
                    logger.warning("Using existing PE data as fallback despite missing recent dates.")
                    break
                else:
                    raise  # No data at all, re-raise error

        if new_pe_data:
            new_pe_df = pd.concat(new_pe_data).drop_duplicates(subset=["Date"])
            # Merge with existing
            updated_pe_df = pd.concat([existing_pe_df, new_pe_df]).drop_duplicates(subset=["Date"]).sort_values("Date")
            
            # Save to static CSV
            STATIC_PE_PATH.parent.mkdir(parents=True, exist_ok=True)
            updated_pe_df.to_csv(STATIC_PE_PATH, index=False)
            logger.info(f"Updated static PE/PB data at {STATIC_PE_PATH}")
            existing_pe_df = updated_pe_df

    # 4. Merge PE/PB with Price Data
    # Final safety check on dtypes before merge
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    existing_pe_df["Date"] = pd.to_datetime(existing_pe_df["Date"]).dt.tz_localize(None)
    
    df = df.merge(existing_pe_df[["Date", "PE", "PB"]], on="Date", how="left")
    
    # Check if we have massive missing data
    missing_pe_count = df["PE"].isna().sum()
    if missing_pe_count > len(df) * 0.5:
        # If we have price data back to 1990, but PE only from 2000, 
        # missing_pe_count might be high, which is expected.
        # But if recent data is missing, we should warn.
        recent_missing = df.tail(30)["PE"].isna().sum()
        if recent_missing > 5:
             logger.warning(f"Significant missing PE data in recent periods: {recent_missing}/30 days")

    # 5. Save to cache
    df.to_parquet(CACHE_PATH, index=False)
    logger.info("Cached market data to %s (%d rows)", CACHE_PATH, len(df))
    return df
