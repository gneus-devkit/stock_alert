import sys

import stock_scraper as ss
import data_collector as dc
import data_analyze as da


def scraper():
    ss.main()


def data_collect():
    dc.main()


def data_analysis():
    da.main()


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "collect"

    if mode not in {"scraper", "collect", "analyze"}:
        print("Usage: stock_alert.py [scraper|collect|analyze]")
        return 1
    if mode == "scraper":
        scraper()
    elif mode == "collect":
        data_collect()
    elif mode == "analyze":
        data_analysis()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())