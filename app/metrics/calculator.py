"""Metrics calculation for market signals analysis."""

import pandas as pd

from app.config import (
    PE_BUCKET_EDGES, PE_BUCKET_LABELS,
    PB_BUCKET_EDGES, PB_BUCKET_LABELS,
)


def get_entry_signals(
    df: pd.DataFrame,
    signal_type: str = "PE Ratio",
    pe_threshold: float = 20,
    pb_threshold: float = 3.5,
) -> pd.DataFrame:
    """
    Identify entry signal dates where valuation drops below threshold.
    Uses monthly sampling to avoid double-counting signals in the same month.
    """
    df = df.copy()

    if signal_type == "PE Ratio":
        mask = df["PE"] < pe_threshold
    elif signal_type == "PB Ratio":
        mask = df["PB"] < pb_threshold
    else:  # PE + PB
        mask = (df["PE"] < pe_threshold) & (df["PB"] < pb_threshold)

    signals = df[mask].copy()

    # Sample monthly (first occurrence per month)
    signals["YearMonth"] = signals["Date"].dt.to_period("M")
    signals = signals.groupby("YearMonth").first().reset_index(drop=True)
    return signals


def calculate_forward_returns(
    df: pd.DataFrame,
    signal_dates: pd.Series,
    holding_years: int = 3,
) -> pd.DataFrame:
    """
    Calculate forward returns (annualized CAGR) from each signal date.

    Returns DataFrame with signal date, entry/exit price, PE at entry, and CAGR.
    """
    results = []
    holding_days = holding_years * 365

    for signal_date in signal_dates:
        entry_row = df[df["Date"] == signal_date]
        if entry_row.empty:
            continue

        entry_price = entry_row["Close"].values[0]
        entry_pe = entry_row["PE"].values[0]
        entry_pb = entry_row["PB"].values[0]

        exit_date = signal_date + pd.Timedelta(days=holding_days)
        future = df[df["Date"] >= exit_date]
        if future.empty:
            continue

        exit_row = future.iloc[0]
        exit_price = exit_row["Close"]
        actual_exit_date = exit_row["Date"]

        years = (actual_exit_date - signal_date).days / 365.25
        if years <= 0 or entry_price <= 0:
            continue

        cagr = ((exit_price / entry_price) ** (1 / years) - 1) * 100

        results.append({
            "Entry Date": signal_date,
            "Exit Date": actual_exit_date,
            "Entry Price": round(entry_price, 2),
            "Exit Price": round(exit_price, 2),
            "PE at Entry": round(entry_pe, 1),
            "PB at Entry": round(entry_pb, 2),
            "CAGR (%)": round(cagr, 2),
            "Holding Years": round(years, 1),
        })

    return pd.DataFrame(results)


def compute_metrics(returns_df: pd.DataFrame) -> dict:
    """Compute summary metrics from forward returns."""
    if returns_df.empty:
        return {
            "entry_signals": 0,
            "median_return": 0.0,
            "win_rate": 0.0,
            "mean_return": 0.0,
        }

    cagr_values = returns_df["CAGR (%)"]
    return {
        "entry_signals": len(returns_df),
        "median_return": round(cagr_values.median(), 1),
        "win_rate": round((cagr_values > 0).mean() * 100, 0),
        "mean_return": round(cagr_values.mean(), 1),
    }


def get_pe_buckets(
    returns_df: pd.DataFrame,
    signal_type: str = "PE Ratio",
) -> pd.DataFrame:
    """Group returns by PE (or PB) buckets and compute median CAGR per bucket."""
    if returns_df.empty:
        return pd.DataFrame(columns=["Bucket", "Median CAGR (%)", "Count"])

    if signal_type == "PB Ratio":
        col, edges, labels = "PB at Entry", PB_BUCKET_EDGES, PB_BUCKET_LABELS
    else:
        col, edges, labels = "PE at Entry", PE_BUCKET_EDGES, PE_BUCKET_LABELS

    df = returns_df.copy()
    df["Bucket"] = pd.cut(df[col], bins=edges, labels=labels, right=False)

    bucket_stats = (
        df.groupby("Bucket", observed=False)
        .agg(**{
            "Median CAGR (%)": ("CAGR (%)", "median"),
            "Count": ("CAGR (%)", "count"),
        })
        .reset_index()
    )
    bucket_stats["Median CAGR (%)"] = bucket_stats["Median CAGR (%)"].round(1).fillna(0)
    return bucket_stats
