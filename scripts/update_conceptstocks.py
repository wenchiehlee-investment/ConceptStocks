#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta


def mask_api_key(url: str) -> str:
    """Mask API key in URL for safe storage in CSV files."""
    return re.sub(r'apikey=[^&]+', 'apikey=***MASKED***', url, flags=re.IGNORECASE)

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
    "Google概念": ("GOOGL", "Alphabet Inc."),
    "Amazon概念": ("AMZN", "Amazon.com, Inc."),
    "Meta概念": ("META", "Meta Platforms, Inc."),
    "Microsoft概念": ("MSFT", "Microsoft Corporation"),
    "AMD概念": ("AMD", "Advanced Micro Devices, Inc."),
    "Apple概念": ("AAPL", "Apple Inc."),
    "Oracle概念": ("ORCL", "Oracle Corporation"),
    "Micro概念": ("MU", "Micron Technology, Inc."),
    "SanDisk概念": ("WDC", "Western Digital Corporation"),
    "Qualcomm概念": ("QCOM", "Qualcomm Inc."),
    "Lenovo概念": ("LNVGY", "Lenovo Group ADR"),
    "TSMC概念": ("TSM", "Taiwan Semiconductor Manufacturing Company Limited"),
    "台積電概念": ("TSM", "Taiwan Semiconductor Manufacturing Company Limited"),
    # OpenAI is private
}

# Normalize non-US/local listings into US tickers for provider consistency.
TICKER_QUERY_OVERRIDES = {
    "0992.HK": ("LNVGY", "Lenovo Group ADR"),
    "2330.TW": ("TSM", "Taiwan Semiconductor Manufacturing Company Limited"),
}


ENDPOINTS = {
    "daily": "TIME_SERIES_DAILY",
    "weekly": "TIME_SERIES_WEEKLY",
    "monthly": "TIME_SERIES_MONTHLY",
}

YAHOO_INTERVALS = {
    "daily": "1d",
    "weekly": "1wk",
    "monthly": "1mo",
}

YAHOO_FILE_TYPES = {
    "daily": "YAHOO_FINANCE_DAILY",
    "weekly": "YAHOO_FINANCE_WEEKLY",
    "monthly": "YAHOO_FINANCE_MONTHLY",
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


def parse_optional_date(value: str, flag_name: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid {flag_name} '{value}'. Use YYYY-MM-DD or YYYY/MM/DD.")


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


def trim_existing_range(
    existing: Dict[Tuple[str, str], Dict[str, object]],
    ticker: str,
    cadence: str,
    start_date: date = None,
    end_date: date = None,
) -> None:
    if cadence != "daily":
        return
    # Only trim when an explicit bounded range is requested.
    # Incremental updates typically pass only --start-date and should retain history.
    if start_date is None or end_date is None:
        return

    date_col = DATE_LABEL[cadence]
    keys_to_delete = []
    for key, row in existing.items():
        if key[0] != ticker:
            continue
        row_date = datetime.strptime(row[date_col], "%Y-%m-%d").date()
        if start_date and row_date < start_date:
            keys_to_delete.append(key)
            continue
        if end_date and row_date > end_date:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del existing[key]


def filter_rows_by_date(
    rows: List[Dict[str, object]],
    cadence: str,
    start_date: date = None,
    end_date: date = None,
) -> List[Dict[str, object]]:
    if cadence != "daily":
        return rows
    if start_date is None and end_date is None:
        return rows

    filtered = []
    for row in rows:
        row_date = datetime.strptime(row["date_key"], "%Y-%m-%d").date()
        if start_date and row_date < start_date:
            continue
        if end_date and row_date > end_date:
            continue
        filtered.append(row)
    return filtered


def is_full_outputsize_premium_error(message: str) -> bool:
    text = (message or "").lower()
    return (
        "outputsize=full" in text
        and "premium feature" in text
        and "time_series_daily" in text
    )


def fetch_rows_from_alphavantage(
    ticker: str,
    cadence: str,
    api_key: str,
    daily_outputsize: str = "compact",
) -> Tuple[List[Dict[str, object]], str, str]:
    if not api_key:
        raise RuntimeError("Missing ALPHAVANTAGE_API_KEY for Alpha Vantage provider.")

    function = ENDPOINTS[cadence]
    base_url = "https://www.alphavantage.co/query?function={fn}&symbol={sym}&apikey={key}".format(
        fn=function, sym=ticker, key=api_key
    )
    request_outputsize = daily_outputsize
    url = base_url
    if cadence == "daily":
        url = f"{base_url}&outputsize={request_outputsize}"

    data = fetch_json(url)
    if "Information" in data:
        info_msg = data["Information"]
        if cadence == "daily" and request_outputsize == "full" and is_full_outputsize_premium_error(info_msg):
            request_outputsize = "compact"
            url = f"{base_url}&outputsize={request_outputsize}"
            print(f"{ticker}: outputsize=full is premium; falling back to outputsize=compact.")
            data = fetch_json(url)
        else:
            raise RuntimeError(info_msg)
        if "Information" in data:
            raise RuntimeError(data["Information"])
    if "Error Message" in data:
        raise RuntimeError(data["Error Message"])

    series = load_series(data)
    new_rows = build_rows(series, cadence)
    masked_url = mask_api_key(url)
    return new_rows, function, masked_url


def fetch_rows_from_yahoo(
    ticker: str,
    cadence: str,
    start_date: date = None,
    end_date: date = None,
) -> Tuple[List[Dict[str, object]], str, str]:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'yfinance'. Install it with: pip install yfinance"
        ) from exc

    interval = YAHOO_INTERVALS[cadence]
    history_kwargs = {
        "interval": interval,
        "auto_adjust": False,
        "actions": False,
    }
    if start_date or end_date:
        if start_date:
            history_kwargs["start"] = start_date.isoformat()
        if end_date:
            history_kwargs["end"] = (end_date + timedelta(days=1)).isoformat()
    else:
        history_kwargs["period"] = "max"

    history = yf.Ticker(ticker).history(**history_kwargs)
    if history is None or history.empty:
        raise RuntimeError(f"No Yahoo Finance data returned for {ticker} ({cadence}).")

    rows = []
    for idx, row in history.iterrows():
        date_str = idx.strftime("%Y-%m-%d")
        date_key = date_str[:7] if cadence == "monthly" else date_str
        rows.append(
            {
                "date_key": date_key,
                "open": to_float(row.get("Open")),
                "close": to_float(row.get("Close")),
            }
        )

    rows.sort(key=lambda x: x["date_key"])
    source_bits = [f"interval={interval}"]
    if start_date:
        source_bits.append(f"start={start_date.isoformat()}")
    if end_date:
        source_bits.append(f"end={end_date.isoformat()}")
    source_file = f"yfinance:{ticker}?" + "&".join(source_bits)
    return rows, YAHOO_FILE_TYPES[cadence], source_file


def verify_yahoo_vs_alphavantage(
    ticker: str,
    cadence: str,
    yahoo_rows: List[Dict[str, object]],
    api_key: str,
    close_tolerance: float,
) -> Optional[Dict[str, object]]:
    if cadence != "daily":
        return None
    try:
        av_rows, _, _ = fetch_rows_from_alphavantage(
            ticker=ticker,
            cadence=cadence,
            api_key=api_key,
            daily_outputsize="compact",
        )
    except RuntimeError as exc:
        reason = str(exc)
        print(f"{ticker}: Yahoo/Alpha verification skipped ({reason}).")
        return {
            "ticker": ticker,
            "overlap_days": 0,
            "avg_abs_diff": None,
            "max_abs_diff": None,
            "mismatches": 0,
            "tolerance": close_tolerance,
            "status": "skipped_alpha_unavailable",
            "mismatch_dates_preview": reason[:200],
        }
    av_map = {row["date_key"]: to_float(row.get("close")) for row in av_rows}
    yahoo_map = {row["date_key"]: to_float(row.get("close")) for row in yahoo_rows}

    overlap = sorted(set(av_map.keys()) & set(yahoo_map.keys()))
    if not overlap:
        print(f"{ticker}: Yahoo/Alpha verification skipped (no overlapping dates).")
        return {
            "ticker": ticker,
            "overlap_days": 0,
            "avg_abs_diff": None,
            "max_abs_diff": None,
            "mismatches": 0,
            "tolerance": close_tolerance,
            "status": "skipped_no_overlap",
        }

    diffs = []
    mismatches = 0
    mismatch_dates = []
    for date_key in overlap:
        av_close = av_map.get(date_key)
        yahoo_close = yahoo_map.get(date_key)
        if av_close is None or yahoo_close is None:
            continue
        diff = abs(yahoo_close - av_close)
        diffs.append(diff)
        if diff > close_tolerance:
            mismatches += 1
            mismatch_dates.append(date_key)

    if not diffs:
        print(f"{ticker}: Yahoo/Alpha verification skipped (no comparable close values).")
        return {
            "ticker": ticker,
            "overlap_days": len(overlap),
            "avg_abs_diff": None,
            "max_abs_diff": None,
            "mismatches": 0,
            "tolerance": close_tolerance,
            "status": "skipped_no_comparable_values",
        }

    avg_abs_diff = sum(diffs) / len(diffs)
    max_abs_diff = max(diffs)
    status = "pass" if mismatches == 0 else "mismatch"
    print(
        f"{ticker}: Yahoo vs Alpha close overlap={len(diffs)} days, "
        f"avg_abs_diff={avg_abs_diff:.6f}, max_abs_diff={max_abs_diff:.6f}, "
        f"mismatches(>{close_tolerance})={mismatches}"
    )
    return {
        "ticker": ticker,
        "overlap_days": len(diffs),
        "avg_abs_diff": avg_abs_diff,
        "max_abs_diff": max_abs_diff,
        "mismatches": mismatches,
        "tolerance": close_tolerance,
        "status": status,
        "mismatch_dates_preview": ";".join(mismatch_dates[:10]),
    }


def write_verification_report(path: str, rows: List[Dict[str, object]]) -> None:
    fieldnames = [
        "ticker",
        "status",
        "overlap_days",
        "avg_abs_diff",
        "max_abs_diff",
        "mismatches",
        "tolerance",
        "mismatch_dates_preview",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fieldnames})


def update_for_ticker(
    ticker: str,
    name: str,
    cadence: str,
    api_key: str,
    out_dir: str,
    provider: str = "alphavantage",
    daily_outputsize: str = "compact",
    start_date: date = None,
    end_date: date = None,
    verify_against_alphavantage: bool = False,
    verify_close_tolerance: float = 0.05,
) -> Optional[Dict[str, object]]:
    verification_summary = None
    if provider == "alphavantage":
        new_rows, file_type, source_file = fetch_rows_from_alphavantage(
            ticker=ticker,
            cadence=cadence,
            api_key=api_key,
            daily_outputsize=daily_outputsize,
        )
    elif provider == "yahoo":
        new_rows, file_type, source_file = fetch_rows_from_yahoo(
            ticker=ticker,
            cadence=cadence,
            start_date=start_date,
            end_date=end_date,
        )
        if verify_against_alphavantage:
            if not api_key:
                print(f"{ticker}: skipped verification (missing ALPHAVANTAGE_API_KEY).")
            else:
                verification_summary = verify_yahoo_vs_alphavantage(
                    ticker=ticker,
                    cadence=cadence,
                    yahoo_rows=new_rows,
                    api_key=api_key,
                    close_tolerance=verify_close_tolerance,
                )
    else:
        raise RuntimeError(f"Unsupported provider: {provider}")

    new_rows = filter_rows_by_date(new_rows, cadence, start_date, end_date)

    out_path = os.path.join(out_dir, OUTPUT_FILES[cadence])
    existing = read_existing(out_path, cadence)
    trim_existing_range(existing, ticker, cadence, start_date, end_date)
    merged = merge_and_recalc(existing, new_rows, ticker, name, cadence, file_type, source_file)
    write_csv(out_path, cadence, merged)
    return verification_summary


def load_concept_metadata(out_dir: str) -> Dict[str, Tuple[str, str, str, str, str, str, str]]:
    """Load concept metadata from raw_conceptstock_company_metadata.csv."""
    metadata_path = os.path.join(out_dir, "raw_conceptstock_company_metadata.csv")
    metadata = {}

    if not os.path.exists(metadata_path):
        return metadata

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                concept = row.get("概念欄位", "")
                if concept:
                    metadata[concept] = (
                        row.get("Ticker", "-"),
                        row.get("公司名稱", "-"),
                        row.get("CIK", "-"),
                        row.get("最新財報", "-"),
                        row.get("即將發布", "-"),
                        row.get("發布時間", "-"),
                        row.get("產品區段", "-"),
                    )
    except Exception as e:
        print(f"  Warning: Could not read {metadata_path}: {e}")

    return metadata


def update_readme_concepts(out_dir: str, concept_cols: List[str]):
    """Update README.md with the dynamic concept list from concept.csv."""
    readme_path = os.path.join(out_dir, "README.md")

    if not os.path.exists(readme_path):
        print(f"  README.md not found at {readme_path}, skipping update")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load metadata from raw_conceptstock_company_metadata.csv
    metadata = load_concept_metadata(out_dir)

    # Generate current timestamp
    now = datetime.now()
    update_time_str = now.strftime("%Y-%m-%d %H:%M:%S CST")
    update_time_line = f"Update time: {update_time_str}"

    # Build the new concept table
    table_lines = [
        "| 概念欄位 | 公司名稱 | Ticker | CIK | 最新財報 | 即將發布 | 發布時間 | 產品區段 |",
        "|----------|----------|--------|-----|----------|----------|----------|----------|",
    ]

    for col in concept_cols:
        if col in metadata:
            ticker, name, cik, latest_report, upcoming, release_date, segments = metadata[col]
            table_lines.append(f"| {col} | {name} | {ticker} | {cik} | {latest_report} | {upcoming} | {release_date} | {segments} |")
        else:
            # Unknown concept - add with placeholders
            table_lines.append(f"| {col} | - | - | - | - | - | - | - |")

    table_lines.append("")
    table_lines.append(f"> 概念欄位來源：`concept.csv` 中以「概念」結尾的欄位（共 {len(concept_cols)} 個）")
    table_lines.append(f"> 概念 metadata：`raw_conceptstock_company_metadata.csv`")

    new_table = "\n".join(table_lines)

    # Find and replace the concept table section
    # Pattern: from "### Concept columns" to "### 財年制度說明" (preserve fiscal year explanation)
    pattern = r"(### Concept columns \(end with 「概念」\)\n\n).*?((?=\n### 財年制度說明|\nAdditional column:|\n## ))"
    replacement = r"\1" + update_time_line + "\n" + new_table + "\n\n"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  Updated README.md with {len(concept_cols)} concept columns")
    else:
        print(f"  README.md concept table unchanged")


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

    # Update README.md with the concept list
    update_readme_concepts(out_dir, concept_cols)


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

    metadata = load_concept_metadata(out_dir)
    dynamic_tickers = {}
    for col in headers:
        if not col.endswith("概念"):
            continue

        ticker = ""
        name = ""
        if col in CONCEPT_TO_TICKER:
            ticker, name = CONCEPT_TO_TICKER[col]
        elif col in metadata:
            # metadata tuple format:
            # (ticker, name, cik, latest_report, upcoming, release_date, segments)
            meta_ticker, meta_name, _, _, _, _, _ = metadata[col]
            ticker = (meta_ticker or "").strip()
            name = (meta_name or "").strip()
        else:
            continue

        if not ticker or ticker == "-":
            continue

        if ticker in TICKER_QUERY_OVERRIDES:
            ticker, override_name = TICKER_QUERY_OVERRIDES[ticker]
            if not name or name == "-":
                name = override_name

        if not name or name == "-":
            name = ticker

        dynamic_tickers[ticker] = name
    
    return dynamic_tickers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update concept stock daily/weekly/monthly CSVs from Alpha Vantage or Yahoo Finance",
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
    parser.add_argument(
        "--provider",
        choices=["alphavantage", "yahoo"],
        default="alphavantage",
        help="Data provider for price series.",
    )
    parser.add_argument(
        "--daily-outputsize",
        choices=["compact", "full"],
        default="compact",
        help="Alpha Vantage daily output size (only used with --provider alphavantage).",
    )
    parser.add_argument(
        "--start-date",
        help="Filter daily data from this date (YYYY-MM-DD or YYYY/MM/DD). For Yahoo, this is also used in the API request.",
    )
    parser.add_argument(
        "--end-date",
        help="Filter daily data to this date (YYYY-MM-DD or YYYY/MM/DD). For Yahoo, this is also used in the API request.",
    )
    parser.add_argument(
        "--verify-against-alphavantage",
        action="store_true",
        help="When --provider yahoo and --cadence daily, compare overlapping close prices vs Alpha Vantage compact data.",
    )
    parser.add_argument(
        "--verify-close-tolerance",
        type=float,
        default=0.05,
        help="Absolute close-price tolerance used by --verify-against-alphavantage (default: 0.05).",
    )
    parser.add_argument(
        "--verify-strict",
        action="store_true",
        help="With --verify-against-alphavantage, exit non-zero if any ticker has mismatches above tolerance.",
    )
    parser.add_argument(
        "--verify-report",
        default="",
        help="Optional CSV path for Yahoo-vs-Alpha verification summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sync_concepts:
        sync_concepts(args.out_dir)
        return 0

    env = load_env(os.path.join(os.getcwd(), ".env"))
    api_key = env.get("ALPHAVANTAGE_API_KEY") or os.environ.get("ALPHAVANTAGE_API_KEY")
    needs_alpha_key = args.provider == "alphavantage" or args.verify_against_alphavantage
    if needs_alpha_key and not api_key:
        print(
            "Missing ALPHAVANTAGE_API_KEY. Set it in .env or env vars.",
            file=sys.stderr,
        )
        return 1
    if args.verify_close_tolerance < 0:
        print("--verify-close-tolerance must be >= 0.", file=sys.stderr)
        return 1
    if args.verify_strict and not args.verify_against_alphavantage:
        print("--verify-strict requires --verify-against-alphavantage.", file=sys.stderr)
        return 1
    if args.provider != "yahoo" and args.verify_against_alphavantage:
        print("--verify-against-alphavantage is only applied when --provider yahoo.")
    if args.verify_report and not args.verify_against_alphavantage:
        print("--verify-report requires --verify-against-alphavantage.", file=sys.stderr)
        return 1
    if args.provider == "yahoo":
        try:
            import yfinance  # noqa: F401
        except ImportError:
            print(
                "Missing dependency 'yfinance'. Install it with: pip install yfinance",
                file=sys.stderr,
            )
            return 1

    start_date = None
    end_date = None
    try:
        if args.start_date:
            start_date = parse_optional_date(args.start_date, "--start-date")
        if args.end_date:
            end_date = parse_optional_date(args.end_date, "--end-date")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if start_date and end_date and start_date > end_date:
        print("--start-date cannot be later than --end-date.", file=sys.stderr)
        return 1

    daily_outputsize = args.daily_outputsize
    if args.provider == "alphavantage" and start_date and daily_outputsize == "compact":
        daily_outputsize = "full"
        print("Using daily outputsize=full because --start-date was provided.")
    if args.provider == "yahoo" and args.daily_outputsize != "compact":
        print("--daily-outputsize is ignored when --provider yahoo.")

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
    verification_rows: List[Dict[str, object]] = []

    for cadence in cadences:
        for i, (ticker, name) in enumerate(tickers.items()):
            if i > 0 or cadence != cadences[0]:
                time.sleep(args.sleep)
            verify_summary = update_for_ticker(
                ticker=ticker,
                name=name,
                cadence=cadence,
                api_key=api_key,
                out_dir=args.out_dir,
                provider=args.provider,
                daily_outputsize=daily_outputsize,
                start_date=start_date,
                end_date=end_date,
                verify_against_alphavantage=args.verify_against_alphavantage,
                verify_close_tolerance=args.verify_close_tolerance,
            )
            if verify_summary is not None:
                verification_rows.append(verify_summary)
            print(f"Updated {cadence} for {ticker}")

    if verification_rows:
        mismatch_tickers = [
            row["ticker"] for row in verification_rows if row.get("status") == "mismatch"
        ]
        checked_rows = [row for row in verification_rows if row.get("status") in {"pass", "mismatch"}]
        total_overlap_days = sum(int(row.get("overlap_days") or 0) for row in checked_rows)
        print(
            f"Verification summary: tickers_checked={len(checked_rows)}, "
            f"total_overlap_days={total_overlap_days}, mismatched_tickers={len(mismatch_tickers)}"
        )
        if mismatch_tickers:
            print("Mismatched tickers: " + ", ".join(sorted(mismatch_tickers)))

        if args.verify_report:
            write_verification_report(args.verify_report, verification_rows)
            print(f"Verification report written to {args.verify_report}")

        if args.verify_strict and mismatch_tickers:
            print("Verification strict mode failed due to mismatches above tolerance.", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
