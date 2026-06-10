# ==============================================================================
# GNeUs SYSTEM WORKFLOW AUTOMATION ENGINE - COMPOSABLE TICKER INTERFACE
# AUTHOR: Gregory (Senior Systems Architect)
# SYSTEM: GNEUS-BLK-OS | Win11 Ent | i5-1035G1 | 12GB RAM MAX
# ENV: D:\Documents\GNeUs_DEV\.venv
# ==============================================================================
import os
import sys
import time
import gc
import requests

# ==============================================================================
# USER CONFIGURATION BLOCK - CHANGE THE VALUE INSIDE THE QUOTES BELOW
# ==============================================================================
TARGET_STOCK_TICKER = "AMD"  # <--- Change this to any valid symbol (e.g., "NVDA", "AMD", "META")
POLLING_INTERVAL_SEC = 20     # <--- Execution delay between real-time data lookups
# ==============================================================================

# Pre-flight environment containment check
VENV_PATH = r"D:\Documents\GNeUs_DEV\.venv"
if not os.path.exists(VENV_PATH):
    print(f"[-] CRITICAL FAILURE: Managed Virtual Environment Missing at {VENV_PATH}")
    sys.exit(1)


class Stock_Tracker:
    """
    Production-grade financial ingestion layer designed to cleanly integrate
    into larger multi-threaded DevOps architectures.
    """
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self.ticker}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.params = {
            "region": "US",
            "lang": "en-US",
            "includePrePost": "false",
            "interval": "2m",
            "useYfid": "true",
            "range": "1d"
        }

    def get_current_value(self) -> float:
        """
        Queries the financial data endpoint and returns the raw market price.
        Returns -1.0 if an error occurs.
        """
        try:
            response = requests.get(self.url, headers=self.headers, params=self.params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                meta = data["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                return float(price) if price else -1.0
            elif response.status_code == 429:
                print("[-] HTTP 429: Rate limited by endpoint provider.")
                return -1.0
            else:
                return -1.0
        except Exception as e:
            print(f"[-] Data Ingestion Exception: {str(e)}")
            return -1.0


def main():
    """
    Standalone runner execution loop. Executes when run directly from a text editor.
    """
    # Use the clean variable defined in the configuration block at the top
    tracker = Stock_Tracker(ticker=TARGET_STOCK_TICKER)
    
    print(f"[+] GNeUs Core Tracker Initiated for Target: {TARGET_STOCK_TICKER}")
    print(f"[+] Polling state active at {POLLING_INTERVAL_SEC} second intervals...")
    
    try:
        while True:
            price = tracker.get_current_value()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            if price != -1.0:
                print(f"[{timestamp}] {TARGET_STOCK_TICKER}: ${price:.2f}")
            else:
                print(f"[{timestamp}] Failed to retrieve fresh tick data.")
                
            time.sleep(POLLING_INTERVAL_SEC)
            gc.collect()  # Flush heap references to protect local 12GB RAM pool
            
    except KeyboardInterrupt:
        print("\n[+] Extraction loop terminated cleanly.")

if __name__ == "__main__":
    main()
# stock_alert
