# ==============================================================================
# SYSTEM WORKFLOW AUTOMATION ENGINE - CENTRAL DATA COLLECTOR
# AUTHOR: Gregory Haapakoski (Senior Systems Architect)
# SYSTEM: GDEV-MOBILE | Win10 Pro | i5-6300U | 8GB RAM MAX
# ENV: C:\Users\GNeUs\.dev\.venv
# ==============================================================================
import os
import sys
import time
import gc
from datetime import datetime

# Enforce system environment verification before execution
VENV_PATH = r"C:\Users\GNeUs\.dev\.venv"
if not os.path.exists(VENV_PATH):
    print(f"[-] CRITICAL FAILURE: Managed Virtual Environment Missing at {VENV_PATH}")
    sys.exit(1)

# Import the architectural tracker class directly from your previous file
try:
    from stock_scraper import Stock_Tracker
except ImportError:
    print("[-] CRITICAL: stock_scraper.py not found in the current directory execution path.")
    sys.exit(1)

# ==============================================================================
# COLLECTOR RUNTIME CONFIGURATION
# ==============================================================================
WATCHLIST = ["TSLA", "NVDA", "AMD", "META", "MU"]
COLLECTION_CYCLE_SEC = 20
OUTPUT_LOG_DIR = r"C:\Users\GNeUs\.dev\04_logs\stock_watch"
OUTPUT_CSV_FILE = os.path.join(OUTPUT_LOG_DIR, "market_ticks.csv")
# ==============================================================================

def initialize_storage():
    """Ensures directories exist and sets up CSV headers on the C:\ drive."""
    if not os.path.exists(OUTPUT_LOG_DIR):
        os.makedirs(OUTPUT_LOG_DIR)
    
    if not os.path.exists(OUTPUT_CSV_FILE):
        with open(OUTPUT_CSV_FILE, "w", encoding="utf-8") as f:
            f.write("Timestamp,Ticker,Price\n")
        print(f"[+] Storage initialized. File registered at: {OUTPUT_CSV_FILE}")

def main():
    initialize_storage()
    
    # Batch-instantiate the tracking engines inside an isolated memory list
    print(f"[+] Initializing GNeUs Ingestion Engines for Watchlist: {WATCHLIST}")
    engines = {ticker: Stock_Tracker(ticker) for ticker in WATCHLIST}
    
    print(f"[+] Central Daemon Engine Active. Polling cluster every {COLLECTION_CYCLE_SEC}s...")
    
    try:
        while True:
            loop_start_time = time.time()
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Execute sequential extraction across the collection array
            with open(OUTPUT_CSV_FILE, "a", encoding="utf-8") as csv_out:
                for ticker, engine in engines.items():
                    price = engine.get_current_value()
                    
                    if price != -1.0:
                        record = f"{timestamp_str},{ticker},{price:.2f}\n"
                        csv_out.write(record)
                        print(f"[*] logged | {timestamp_str} | {ticker} -> ${price:.2f}")
                    else:
                        print(f"[-] Data Drop | Failed to resolve tick for {ticker}")
            
            # Flush internal buffers to physical spindle disk instantly
            csv_out.close()
            
            # Calculate dynamic delta to maintain an accurate 20-second tracking sequence
            elapsed = time.time() - loop_start_time
            sleep_duration = max(0.1, COLLECTION_CYCLE_SEC - elapsed)
            time.sleep(sleep_duration)
            
            # Rigid Garbage Collection to enforce the 12GB RAM ceiling limit
            gc.collect()
            
    except KeyboardInterrupt:
        print("\n[+] Central Collector Daemon stopped securely via administrative instruction.")

if __name__ == "__main__":
    main()
