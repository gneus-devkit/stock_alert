import csv
import time
from datetime import datetime, timedelta
from pathlib import Path


def open_csv(file: str) -> tuple[list[list[str]], list[list[str]], list[list[str]], list[list[str]], list[list[str]]]:
    """Read the collector or analysis CSV and return five separate symbol-specific lists."""
    amd_rows = []
    tsla_rows = []
    nvda_rows = []
    meta_rows = []
    mu_rows = []
    path = Path(file)
    if not path.exists():
        path = Path(__file__).with_name(file)

    with path.open("r", encoding="utf-8", newline="") as datafile:
        reader = csv.reader(datafile)
        for raw in reader:
            cells = [value.strip() for value in raw]
            if not cells or not cells[0]:
                continue
            if cells[0].lower() in {"timestamp", "time", "timestamp, ticker, price"}:
                continue

            symbol = cells[1] if len(cells) > 1 else ""
            if symbol in {"AMD", "TSLA", "NVDA", "META", "MU"}:
                if symbol == "AMD":
                    amd_rows.append(cells)
                elif symbol == "TSLA":
                    tsla_rows.append(cells)
                elif symbol == "NVDA":
                    nvda_rows.append(cells)
                elif symbol == "META":
                    meta_rows.append(cells)
                elif symbol == "MU":
                    mu_rows.append(cells)

    return amd_rows, tsla_rows, nvda_rows, meta_rows, mu_rows


def show_lists() -> None:
    """Print each symbol list with its embedded rows."""
    amd_rows, tsla_rows, nvda_rows, meta_rows, mu_rows = open_csv("stock_analysis_output.csv")
    print("AMD list:", amd_rows)
    print("TSLA list:", tsla_rows)
    print("NVDA list:", nvda_rows)
    print("META list:", meta_rows)
    print("MU list:", mu_rows)


def detect_alerts(rows: list[list[str]], symbol: str, threshold: float = 0.05, lookback_minutes: int = 30) -> list[str]:
    """Detect 5%+ moves versus the previous tick and the value from 30 minutes earlier for one symbol."""
    alerts = []
    for idx, row in enumerate(rows):
        if len(row) < 3:
            continue
        try:
            current_time = datetime.strptime(row[0].strip(), "%Y-%m-%d %H:%M:%S")
            current_price = float(row[2])
        except (TypeError, ValueError):
            continue

        reference_time = current_time - timedelta(minutes=lookback_minutes)
        reference_index = None
        for j in range(idx - 1, -1, -1):
            try:
                candidate_time = datetime.strptime(rows[j][0].strip(), "%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                continue
            if candidate_time <= reference_time:
                reference_index = j
                break

        if reference_index is None:
            continue

        try:
            previous_price = float(rows[reference_index][2])
        except (TypeError, ValueError):
            continue

        if idx >= 1:
            prev_tick_price = float(rows[idx - 1][2]) if len(rows[idx - 1]) > 2 else 0.0
            tick_pct = (current_price - prev_tick_price) / prev_tick_price if prev_tick_price else 0.0
            if abs(tick_pct) >= threshold:
                tick_direction = "up" if tick_pct > 0 else "down"
                alerts.append(
                    f"ALERT {symbol}: {tick_direction} {tick_pct * 100:.2f}% vs immediate prior point "
                    f"({current_time.strftime('%Y-%m-%d %H:%M:%S')} | {prev_tick_price:.2f} -> {current_price:.2f})"
                )

        if reference_index is not None and reference_index != idx:
            try:
                prior_30_price = float(rows[reference_index][2])
            except (TypeError, ValueError):
                prior_30_price = 0.0
            pct_change = (current_price - prior_30_price) / prior_30_price if prior_30_price else 0.0
            if abs(pct_change) >= threshold:
                direction = "up" if pct_change > 0 else "down"
                alerts.append(
                    f"ALERT {symbol}: {direction} {pct_change * 100:.2f}% vs 30-minute prior "
                    f"({current_time.strftime('%Y-%m-%d %H:%M:%S')} | {prior_30_price:.2f} -> {current_price:.2f})"
                )
    return alerts


def compare(file: str = "04_logs/stock_watch/market_ticks.csv", threshold: float = 0.05, lookback_minutes: int = 30) -> list[str]:
    """Run a one-shot comparison for the current CSV and return any 5% alert messages."""
    alerts = []
    symbol_lists = open_csv(file)
    symbols = ("AMD", "TSLA", "NVDA", "META", "MU")
    for symbol, rows in zip(symbols, symbol_lists):
        alerts.extend(detect_alerts(rows, symbol, threshold, lookback_minutes))
    for message in alerts:
        print(message)
    return alerts


def monitor(file: str = "04_logs/stock_watch/market_ticks.csv", threshold: float = 0.05, lookback_minutes: int = 30, interval_sec: int = 20) -> None:
    """Continuously watch the live collector CSV and emit 5% / 30-minute alerts."""
    seen = set()
    print(f"[+] Monitoring {file} for 5% moves over {lookback_minutes} minutes. Press Ctrl+C to stop.")
    try:
        while True:
            symbol_lists = open_csv(file)
            symbols = ("AMD", "TSLA", "NVDA", "META", "MU")
            for symbol, rows in zip(symbols, symbol_lists):
                for alert in detect_alerts(rows, symbol, threshold, lookback_minutes):
                    marker = (symbol, alert)
                    if marker not in seen:
                        seen.add(marker)
                        print(alert)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n[+] Alert monitor stopped.")


if __name__ == "__main__":
    monitor()