#!/usr/bin/env python3
import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.request
from typing import Dict, List, Tuple
from datetime import datetime

DEFAULT_TICKERS = {
    "NVDA": "NVIDIA Corporation",
    "GOOG": "Alphabet Inc. Class C",
    "GOOGL": "Alphabet Inc. Class A",
    "AMZN": "Amazon.com, Inc.",
    "META": "Meta Platforms, Inc.",
    "MSFT": "Microsoft Corporation",
    "AMD": "Advanced Micro Devices, Inc.",
    "AAPL": "Apple Inc.",
    "ORCL": "Oracle Corporation",
}

# Mapping from concept column name (in concept.csv) to (Ticker, Company Name)
CONCEPT_TO_TICKER = {
    "nVidia概念": ("NVDA", "NVIDIA Corporation"),
    "Google概念": ("GOOG", "Alphabet Inc. Class C"),
    "Amazon概念": ("AMZN", "Amazon.com, Inc."),
    "Meta概念": ("META", "Meta Platforms, Inc."),
    "Microsoft概念": ("MSFT", "Microsoft Corporation"),
    "AMD概念": ("AMD", "Advanced Micro Devices, Inc."),
    "Apple概念": ("AAPL", "Apple Inc."),
    "Oracle概念": ("ORCL", "Oracle Corporation"),
    "Micro概念": ("MU", "Micron Technology, Inc."),
    "SanDisk概念": ("WDC", "Western Digital Corporation"),
    # OpenAI is private
}

ENDPOINTS = {
    "daily": "TIME_SERIES_DAILY",
    "weekly": "TIME_SERIES_WEEKLY",
    "monthly": "TIME_SERIES_MONTHLY",
}

DATE_LABEL = {
    "daily": "交易日期",
    "weekly": "交易週",
    "monthly": "交易月份",
}

OUTPUT_FILES = {
    "daily": "raw_conceptstock_daily.csv",
    "weekly": "raw_conceptstock_weekly.csv",
    "monthly": "raw_conceptstock_monthly.csv",
}

FIELDNAMES = {
    "daily": [
        "stock_code",
        "company_name",
        "交易日期",
        "開盤_價格_元",
        "收盤_價格_元",
        "漲跌_價格_元",
        "漲跌_pct",
        "file_type",
        "source_file",
        "download_success",
        "download_timestamp",
        "process_timestamp",
        "stage1_process_timestamp",
    ],
    "weekly": [
        "stock_code",
        "company_name",
        "交易週",
        "開盤_價格_元",
        "收盤_價格_元",
        "漲跌_價格_元",
        "漲跌_pct",
        "file_type",
        "source_file",
        "download_success",
        "download_timestamp",
        "process_timestamp",
        "stage1_process_timestamp",
    ],
    "monthly": [
        "stock_code",
        "company_name",
        "交易月份",
        "開盤_價格_元",
        "收盤_價格_元",
        "漲跌_價格_元",
        "漲跌_pct",
        "file_type",
        "source_file",
        "download_success",
        "download_timestamp",
        "process_timestamp",
        "stage1_process_timestamp",
    ],
}


def load_env(path: str) -> Dict[str, str]:
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip()
    return env


def fetch_json(url: str) -> Dict:
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Fallback to curl for environments with SSL issues
        result = subprocess.check_output(["curl", "-sSL", url])
        return json.loads(result.decode("utf-8"))


def load_series(data: Dict) -> Dict[str, Dict[str, str]]:
    for key in data.keys():
        if "Time Series" in key:
            return data[key]
    raise RuntimeError(f"No time series in response: {data}")


def to_float(s: str):
    try:
        return float(s)
    except Exception:
        return None


def build_rows(series: Dict[str, Dict[str, str]], cadence: str) -> List[Dict[str, object]]:
    items = sorted(series.items(), key=lambda x: x[0])
    rows = []
    for date_str, v in items:
        if cadence == "monthly":
            date_key = date_str[:7]
        else:
            date_key = date_str
        rows.append(
            {
                "date_key": date_key,
                "open": to_float(v.get("1. open")),
                "close": to_float(v.get("4. close")),
            }
        )
    return rows


def read_existing(path: str, cadence: str) -> Dict[Tuple[str, str], Dict[str, object]]:
    if not os.path.exists(path):
        return {}
    rows = {}
    date_col = DATE_LABEL[cadence]
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            stock_code = row.get("stock_code") or row.get("代號")
            if not stock_code:
                continue
            key = (stock_code, row[date_col])
            rows[key] = row
    return rows


def write_csv(path: str, cadence: str, rows: List[Dict[str, object]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES[cadence])
        w.writeheader()
        for row in rows:
            for key in (
                "file_type",
                "source_file",
                "download_success",
                "download_timestamp",
                "process_timestamp",
                "stage1_process_timestamp",
            ):
                if key not in row:
                    row[key] = None
            w.writerow(row)


def merge_and_recalc(
    existing: Dict[Tuple[str, str], Dict[str, object]],
    new_rows: List[Dict[str, object]],
    ticker: str,
    name: str,
    cadence: str,
    file_type: str,
    source_file: str,
) -> List[Dict[str, object]]:
    date_col = DATE_LABEL[cadence]
    now = datetime.now()
    download_ts = now.strftime("%Y-%m-%d %H:%M:%S")
    process_ts = now.strftime("%Y-%m-%d %H:%M:%S")
    stage1_ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    for r in new_rows:
        key = (ticker, r["date_key"])
        existing[key] = {
            date_col: r["date_key"],
            "stock_code": ticker,
            "company_name": name,
            "開盤_價格_元": r["open"],
            "收盤_價格_元": r["close"],
            "漲跌_價格_元": None,
            "漲跌_pct": None,
            "file_type": file_type,
            "source_file": source_file,
            "download_success": True,
            "download_timestamp": download_ts,
            "process_timestamp": process_ts,
            "stage1_process_timestamp": stage1_ts,
        }

    # Recalculate change fields for this ticker across all rows
    ticker_rows = [
        v for k, v in existing.items() if k[0] == ticker
    ]
    ticker_rows.sort(key=lambda x: x[date_col])

    prev_close = None
    for row in ticker_rows:
        close_p = to_float(row.get("收盤_價格_元"))
        change = None
        change_pct = None
        if prev_close is not None and close_p is not None:
            change = close_p - prev_close
            if prev_close != 0:
                change_pct = change / prev_close
        row["漲跌_價格_元"] = change
        row["漲跌_pct"] = change_pct
        prev_close = close_p

    # Return all rows sorted by ticker then date
    all_rows = list(existing.values())
    all_rows.sort(key=lambda x: (x["stock_code"], x[date_col]))
    return all_rows


def update_for_ticker(ticker: str, name: str, cadence: str, api_key: str, out_dir: str):
    function = ENDPOINTS[cadence]
    url = (
        "https://www.alphavantage.co/query?function={fn}&symbol={sym}&apikey={key}"
    ).format(fn=function, sym=ticker, key=api_key)

    data = fetch_json(url)
    if "Information" in data:
        raise RuntimeError(data["Information"])
    if "Error Message" in data:
        raise RuntimeError(data["Error Message"])

    series = load_series(data)
    new_rows = build_rows(series, cadence)

    out_path = os.path.join(out_dir, OUTPUT_FILES[cadence])
    existing = read_existing(out_path, cadence)
    merged = merge_and_recalc(existing, new_rows, ticker, name, cadence, function, url)
    write_csv(out_path, cadence, merged)


def sync_concepts(out_dir: str):
    url = "https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.CompanyInfo/refs/heads/main/raw_companyinfo.csv"
    print(f"Fetching company info from {url}...")
    
    # Use urllib to fetch the CSV
    try:
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode("utf-8-sig")
    except Exception as e:
        print(f"Error fetching CSV: {e}", file=sys.stderr)
        # Fallback to curl
        result = subprocess.check_output(["curl", "-sSL", url])
        content = result.decode("utf-8-sig")

    lines = content.splitlines()
    reader = csv.DictReader(lines)
    fieldnames = reader.fieldnames
    if not fieldnames:
        print("Empty CSV or invalid header", file=sys.stderr)
        return

    concept_cols = [c for c in fieldnames if c.endswith("概念")]
    # Standardize column names for concept.csv
    # Use 'stock_code' and 'company_name' to match the other CSVs
    output_fields = ["stock_code", "company_name"] + concept_cols
    
    out_path = os.path.join(out_dir, "concept.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        for row in reader:
            # Check if any concept column is '1'
            has_concept = any(row.get(c) == "1" for c in concept_cols)
            if has_concept:
                out_row = {
                    "stock_code": row.get("\ufeff代號") or row.get("代號"),
                    "company_name": row.get("名稱"),
                }
                for c in concept_cols:
                    out_row[c] = row.get(c)
                writer.writerow(out_row)
    print(f"Generated {out_path} with {len(concept_cols)} concept columns.")


def load_dynamic_tickers(out_dir: str) -> Dict[str, str]:
    """
    Reads concept.csv headers to find active concepts and returns corresponding tickers
    from CONCEPT_TO_TICKER mapping.
    """
    path = os.path.join(out_dir, "concept.csv")
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
    except Exception as e:
        print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
        return {}

    dynamic_tickers = {}
    for col in headers:
        if col in CONCEPT_TO_TICKER:
            ticker, name = CONCEPT_TO_TICKER[col]
            dynamic_tickers[ticker] = name
    
    return dynamic_tickers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update concept stock daily/weekly/monthly CSVs from Alpha Vantage",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ticker", help="Single ticker to update (e.g., NVDA)")
    group.add_argument("--all", action="store_true", help="Update all configured tickers")
    group.add_argument("--sync-concepts", action="store_true", help="Fetch company info and update concept.csv")
    parser.add_argument(
        "--cadence",
        choices=["daily", "weekly", "monthly", "all"],
        default="all",
        help="Which cadence to update",
    )
    parser.add_argument(
        "--out-dir",
        default=os.getcwd(),
        help="Output directory for CSVs",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.2,
        help="Seconds to sleep between API calls",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sync_concepts:
        sync_concepts(args.out_dir)
        return 0

    env = load_env(os.path.join(os.getcwd(), ".env"))
    api_key = env.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        print("Missing ALPHAVANTAGE_API_KEY. Set it in .env or env vars.", file=sys.stderr)
        return 1

    if args.ticker:
        ticker = args.ticker.upper()
        if ticker not in DEFAULT_TICKERS:
            # Check dynamic tickers too in case user asks for one specifically
            dyn = load_dynamic_tickers(args.out_dir)
            if ticker in dyn:
                 tickers = {ticker: dyn[ticker]}
            else:
                print(f"Unknown ticker {ticker}. Add it to DEFAULT_TICKERS or CONCEPT_TO_TICKER.", file=sys.stderr)
                return 1
        else:
            tickers = {ticker: DEFAULT_TICKERS[ticker]}
    else:
        tickers = DEFAULT_TICKERS.copy()
        dynamic_tickers = load_dynamic_tickers(args.out_dir)
        tickers.update(dynamic_tickers)
        print(f"Active tickers: {', '.join(sorted(tickers.keys()))}")

    cadences = ["daily", "weekly", "monthly"] if args.cadence == "all" else [args.cadence]

    for cadence in cadences:
        for i, (ticker, name) in enumerate(tickers.items()):
            if i > 0 or cadence != cadences[0]:
                time.sleep(args.sleep)
            update_for_ticker(ticker, name, cadence, api_key, args.out_dir)
            print(f"Updated {cadence} for {ticker}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
