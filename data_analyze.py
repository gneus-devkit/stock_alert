# ==============================================================================
# SYSTEM WORKFLOW AUTOMATION ENGINE - CENTRAL DATA ANALYZER
# AUTHOR: Gregory Haapakoski (Senior Systems Architect)
# SYSTEM: GDEV-MOBILE | Win10 Pro | i5-6300U | 8GB RAM MAX
# ENV: C:\Users\GNeUs\.dev\.venv
# ==============================================================================

"""data_analyze.py

Starting point for analyzing a JSON document containing changing stock prices.

Expected JSON shape examples handled by this module:
 - list of records: [{"symbol": "AAPL", "timestamp": 1620000000, "price": 125.0}, ...]
 - dict of time series per symbol: {"AAPL": [{"t": "2021-05-03T...", "price": 125.0}, ...], ...}

This module provides small utilities to load the data into a pandas.DataFrame,
compute returns, moving averages, volatility, and simple anomaly detection.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd


def load_json(filepath: str) -> Any:
    """Load JSON from a file and return the parsed object."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(filepath: str) -> pd.DataFrame:
    """Load a stock market CSV file into a tidy DataFrame."""
    df = pd.read_csv(filepath, parse_dates=["Timestamp"]).rename(
        columns={"Timestamp": "timestamp", "Ticker": "symbol", "Price": "price"}
    )
    return df[["timestamp", "symbol", "price"]].sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def records_to_dataframe(records: list, time_key: str = "timestamp", price_key: str = "price", symbol_key: Optional[str] = "symbol") -> pd.DataFrame:
    """Convert a list of record dicts into a tidy DataFrame.

    The returned DataFrame has a DatetimeIndex, columns: symbol, price.
    """
    if not records:
        return pd.DataFrame(columns=["symbol", "price"]).set_index(pd.DatetimeIndex([]))

    rows = []
    for r in records:
        # accept numeric epoch or ISO string
        t = r.get(time_key)
        if isinstance(t, (int, float)):
            ts = datetime.fromtimestamp(t)
        else:
            ts = pd.to_datetime(t)
        rows.append({"timestamp": ts, "symbol": r.get(symbol_key) if symbol_key else None, "price": r.get(price_key)})

    df = pd.DataFrame(rows).set_index("timestamp").sort_index()
    return df


def series_to_dataframe(series_dict: Dict[str, list], time_key: str = "t", price_key: str = "price") -> pd.DataFrame:
    """Convert a dict of symbol -> list[records] into a combined DataFrame."""
    frames = []
    for sym, recs in series_dict.items():
        tmp = records_to_dataframe(recs, time_key, price_key, symbol_key=None)
        tmp["symbol"] = sym
        frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).sort_index()


def pivot_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot DataFrame to have timestamps as index and symbols as columns with prices."""
    return df.reset_index().pivot_table(index="timestamp", columns="symbol", values="price")


def compute_returns(price_series: pd.Series) -> pd.Series:
    """Simple log returns of a price series."""
    return price_series.apply(pd.to_numeric).astype(float).pct_change().fillna(0)


def moving_average(price_series: pd.Series, window: int = 5) -> pd.Series:
    return price_series.rolling(window=window, min_periods=1).mean()


def volatility(price_series: pd.Series, window: int = 20) -> pd.Series:
    """Rolling standard deviation of returns as volatility estimate."""
    returns = compute_returns(price_series)
    return returns.rolling(window=window, min_periods=1).std()


def simple_anomaly_detector(price_series: pd.Series, window: int = 20, threshold: float = 3.0) -> pd.Series:
    """Flag points where the price change (in returns) exceeds threshold * rolling std."""
    returns = compute_returns(price_series)
    roll_std = returns.rolling(window=window, min_periods=1).std()
    flag = (returns.abs() > (threshold * roll_std)).astype(int)
    return flag


def write_csv_with_spaces(df: pd.DataFrame, output_path: str) -> None:
    """Write a CSV file with spaces after each comma for human-readable output."""
    tmp_path = Path(output_path).with_suffix(".tmp.csv")
    df.to_csv(tmp_path, index=False)
    text = tmp_path.read_text(encoding="utf-8")
    tmp_path.write_text(text.replace(",", ", "), encoding="utf-8")
    Path(output_path).write_text(text.replace(",", ", "), encoding="utf-8")
    tmp_path.unlink(missing_ok=True)


def export_analysis_csv(df: pd.DataFrame, output_path: str = "stock_analysis_output.csv") -> pd.DataFrame:
    """Write a per-symbol analysis summary to CSV for later access."""
    frames = []
    for symbol, group in df.groupby("symbol", sort=True):
        series = group.set_index("timestamp")["price"].astype(float).sort_index()
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": series.index, 
                    "symbol": symbol, 
                    "price": series.values, 
                    "returns": compute_returns(series).values, 
                    "moving_average_5": moving_average(series, window=5).values, 
                    "volatility_20": volatility(series, window=20).values, 
                    "anomaly_flag": simple_anomaly_detector(series, window=20, threshold=3.0).values,
                }
            )
        )

    if not frames:
        raise ValueError("No price data was available to export.")

    summary = pd.concat(frames, ignore_index=True)
    out_dir = Path(output_path).parent
    if out_dir != Path(""):
        out_dir.mkdir(parents=True, exist_ok=True)
    write_csv_with_spaces(summary, output_path)
    print(f"Saved analysis summary to {output_path}")
    return summary


def main():
    """Run analysis on JSON or CSV input and export persistent CSV files."""
    default_input = Path("04_logs/stock_watch/market_ticks.csv")
    input_path = sys.argv[1] if len(sys.argv) >= 2 else default_input

    if not Path(input_path).exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    if str(input_path).lower().endswith(".csv"):
        df = load_csv(input_path)
    else:
        data = load_json(input_path)
        if isinstance(data, list):
            df = records_to_dataframe(data)
        elif isinstance(data, dict):
            df = series_to_dataframe(data)
        else:
            raise SystemExit("Unsupported JSON structure")
        df = df.reset_index().rename(columns={"timestamp": "timestamp", "symbol": "symbol", "price": "price"})

    prices = pivot_prices(df.rename(columns={"timestamp": "timestamp", "symbol": "symbol", "price": "price"}))
    print(prices.tail())

    prices_output = Path("prices_output.csv")
    write_csv_with_spaces(prices, prices_output)
    print(f"Saved pivoted prices to {prices_output}")

    summary_output = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("stock_analysis_output.csv")
    export_analysis_csv(df, str(summary_output))

if __name__ == "__main__":
    main()