"""Data fetching and caching for Nifty 50 market data using yfinance."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from app.config import NIFTY_TICKER, CACHE_DIR, CACHE_EXPIRY_HOURS, MEAN_PE, MEAN_PB

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
        raise ValueError("No data returned from yfinance for %s" % NIFTY_TICKER)

    df = df.reset_index()
    # Normalize columns — yfinance may return MultiIndex or flat
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if c[1] == "" else c[0] for c in df.columns]

    keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[keep_cols].copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def generate_synthetic_pe(price_df: pd.DataFrame) -> pd.Series:
    """
    Generate synthetic PE ratio from price history using trend analysis.

    Uses log-linear regression on price to find the fundamental growth trend,
    then PE = MEAN_PE * (price / trend). Produces realistic PE values that are
    high when prices outpace growth and low during corrections.
    """
    close = price_df["Close"].values.astype(float)
    days = np.arange(len(close))
    log_close = np.log(np.maximum(close, 1e-6))

    # Fit exponential trend (log-linear regression)
    coeffs = np.polyfit(days, log_close, 1)
    log_trend = np.polyval(coeffs, days)
    trend = np.exp(log_trend)

    # PE as deviation from trend
    pe = MEAN_PE * (close / trend)

    # Mild smoothing to reduce daily noise
    pe_series = pd.Series(pe, index=price_df.index)
    pe_smoothed = pe_series.rolling(window=21, min_periods=1, center=True).mean()
    pe_smoothed = pe_smoothed.clip(8, 40)
    return pe_smoothed


def generate_synthetic_pb(pe_series: pd.Series) -> pd.Series:
    """Generate synthetic PB ratio derived from PE with realistic scaling."""
    pb = MEAN_PB * (pe_series / MEAN_PE)
    # Slight deterministic noise so PB isn't perfectly correlated
    rng = np.random.RandomState(42)
    noise = 1.0 + 0.05 * rng.randn(len(pb))
    pb = pb * noise
    return pb.clip(1.5, 8.0)


def load_market_data(force_refresh: bool = False) -> pd.DataFrame:
    """
    Load Nifty 50 market data with PE and PB columns.

    Uses cached parquet if available and fresh, otherwise fetches from yfinance.

    Returns:
        DataFrame with columns: Date, Close, PE, PB, Open, High, Low, Volume
    """
    _ensure_cache_dir()

    if not force_refresh and _is_cache_valid():
        logger.info("Loading from cache: %s", CACHE_PATH)
        return pd.read_parquet(CACHE_PATH)

    # Fetch fresh data
    df = fetch_nifty_data()

    # Check for user-provided PE data
    if STATIC_PE_PATH.exists():
        logger.info("Loading PE data from %s", STATIC_PE_PATH)
        pe_df = pd.read_csv(STATIC_PE_PATH, parse_dates=["Date"])
        df = df.merge(pe_df[["Date", "PE", "PB"]], on="Date", how="left")
        df["PE"] = df["PE"].ffill().bfill()
        df["PB"] = df["PB"].ffill().bfill()
    else:
        logger.info("No historical PE CSV found, generating synthetic PE/PB")
        df["PE"] = generate_synthetic_pe(df)
        df["PB"] = generate_synthetic_pb(df["PE"])

    # Save to cache
    df.to_parquet(CACHE_PATH, index=False)
    logger.info("Cached market data to %s (%d rows)", CACHE_PATH, len(df))
    return df
