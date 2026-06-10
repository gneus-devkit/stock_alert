import sys
import threading
import time

import stock_scraper as ss
import data_collector as dc
import data_analyze as da
import compare_data as cd


def scraper():
    ss.main()


def data_collect():
    dc.main()


def data_analysis():
    da.main()


def run_live_alerts():
    """Start the collector in the background and run the live 5% alert monitor."""
    collector_thread = threading.Thread(target=dc.main, daemon=True)
    collector_thread.start()
    time.sleep(2)
    print("[+] Live prices are being collected in the background.")
    print("[+] Starting 5% price change alert monitor...")
    cd.monitor("04_logs/stock_watch/market_ticks.csv", threshold=0.05, lookback_minutes=30, interval_sec=20)


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "collect"

    if mode not in {"scraper", "collect", "analyze", "alert", "all"}:
        print("Usage: stock_alert.py [scraper|collect|analyze|alert|all]")
        return 1

    if mode == "scraper":
        scraper()
    elif mode == "collect":
        data_collect()
    elif mode == "analyze":
        data_analysis()
    elif mode == "alert":
        run_live_alerts()
    elif mode == "all":
        da.main()
        run_live_alerts()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())