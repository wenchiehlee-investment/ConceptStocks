#!/usr/bin/env python3
"""
Update Concept Stock Company Financial Data

Fetches income statements and segment revenue from multiple sources:
- SEC EDGAR (primary, free)
- Alpha Vantage (cross-check for income)
- FMP (cross-check for segments)

Output files:
- raw_conceptstock_company_income.csv (Type 54)
- raw_conceptstock_company_revenue.csv (Type 53)
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external.sec_edgar_client import SECEdgarClient, COMPANY_CIK
from src.external.alphavantage_client import AlphaVantageClient, load_api_key as load_av_key
from src.external.fmp_client import FMPClient, load_api_key as load_fmp_key


# Output file names
OUTPUT_INCOME = "raw_conceptstock_company_income.csv"
OUTPUT_REVENUE = "raw_conceptstock_company_revenue.csv"

# Income statement CSV schema (Type 54)
INCOME_FIELDNAMES = [
    "symbol",
    "company_name",
    "fiscal_year",
    "end_date",
    "period",
    "total_revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "eps",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "currency",
    "source",
    "validation_status",
    "file_type",
    "source_file",
    "download_success",
    "download_timestamp",
    "process_timestamp",
    "stage1_process_timestamp",
]

# Segment revenue CSV schema (Type 53)
REVENUE_FIELDNAMES = [
    "symbol",
    "company_name",
    "fiscal_year",
    "end_date",
    "period",
    "segment_name",
    "segment_type",
    "revenue",
    "revenue_yoy_pct",
    "currency",
    "source",
    "file_type",
    "source_file",
    "download_success",
    "download_timestamp",
    "process_timestamp",
    "stage1_process_timestamp",
]

# Company names for output
COMPANY_NAMES = {
    "NVDA": "NVIDIA Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com, Inc.",
    "META": "Meta Platforms, Inc.",
    "MSFT": "Microsoft Corporation",
    "AMD": "Advanced Micro Devices, Inc.",
    "AAPL": "Apple Inc.",
    "ORCL": "Oracle Corporation",
    "MU": "Micron Technology, Inc.",
    "WDC": "Western Digital Corporation",
}


def load_env(path: str) -> Dict[str, str]:
    """Load environment variables from .env file."""
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


def read_existing_csv(path: str, key_fields: List[str]) -> Dict[tuple, Dict]:
    """Read existing CSV into dict keyed by specified fields."""
    if not os.path.exists(path):
        return {}

    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = tuple(row.get(k) for k in key_fields)
            rows[key] = row
    return rows


def write_csv(path: str, fieldnames: List[str], rows: List[Dict]):
    """Write rows to CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure all fields exist
            clean_row = {k: row.get(k) for k in fieldnames}
            writer.writerow(clean_row)


def get_timestamps() -> Dict[str, str]:
    """Get current timestamps for CSV metadata."""
    now = datetime.now()
    return {
        "download_timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "process_timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "stage1_process_timestamp": now.strftime("%Y-%m-%d %H:%M:%S.%f"),
    }


def fetch_income_sec_edgar(
    client: SECEdgarClient, symbol: str, years: int = 10,
    include_quarterly: bool = False
) -> List[Dict[str, Any]]:
    """Fetch income statement from SEC EDGAR."""
    try:
        data = client.get_income_statement(
            symbol, years=years, include_quarterly=include_quarterly
        )
        timestamps = get_timestamps()

        results = []
        for record in data:
            results.append({
                "symbol": symbol,
                "company_name": COMPANY_NAMES.get(symbol, symbol),
                "fiscal_year": record.get("fiscal_year"),
                "end_date": record.get("end_date"),
                "period": record.get("period", "FY"),
                "total_revenue": record.get("total_revenue"),
                "gross_profit": record.get("gross_profit"),
                "operating_income": record.get("operating_income"),
                "net_income": record.get("net_income"),
                "eps": record.get("eps"),
                "gross_margin": record.get("gross_margin"),
                "operating_margin": record.get("operating_margin"),
                "net_margin": record.get("net_margin"),
                "currency": "USD",
                "source": "SEC",
                "validation_status": None,
                "file_type": "INCOME_STATEMENT",
                "source_file": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{COMPANY_CIK.get(symbol, '')}.json",
                "download_success": True,
                **timestamps,
            })
        return results
    except Exception as e:
        print(f"  SEC EDGAR error for {symbol}: {e}", file=sys.stderr)
        return []


def fetch_income_alphavantage(
    client: AlphaVantageClient, symbol: str,
    include_quarterly: bool = False
) -> List[Dict[str, Any]]:
    """Fetch income statement from Alpha Vantage for cross-checking."""
    try:
        data = client.get_income_statement(symbol, annual_only=not include_quarterly)
        timestamps = get_timestamps()

        results = []
        for record in data:
            results.append({
                "symbol": symbol,
                "company_name": COMPANY_NAMES.get(symbol, symbol),
                "fiscal_year": record.get("fiscal_year"),
                "end_date": record.get("end_date"),
                "period": record.get("period", "FY"),
                "total_revenue": record.get("total_revenue"),
                "gross_profit": record.get("gross_profit"),
                "operating_income": record.get("operating_income"),
                "net_income": record.get("net_income"),
                "eps": None,
                "gross_margin": record.get("gross_margin"),
                "operating_margin": record.get("operating_margin"),
                "net_margin": record.get("net_margin"),
                "currency": "USD",
                "source": "AlphaVantage",
                "validation_status": None,
                "file_type": "INCOME_STATEMENT",
                "source_file": record.get("source_url", ""),
                "download_success": True,
                **timestamps,
            })
        return results
    except Exception as e:
        print(f"  Alpha Vantage error for {symbol}: {e}", file=sys.stderr)
        return []


def fetch_income_fmp(
    client: FMPClient, symbol: str, limit: int = 10,
    include_quarterly: bool = False
) -> List[Dict[str, Any]]:
    """Fetch income statement from FMP for cross-checking."""
    try:
        all_data = []
        all_data.extend(client.get_income_statement(symbol, limit=limit, period="annual"))
        if include_quarterly:
            all_data.extend(client.get_income_statement(symbol, limit=limit * 4, period="quarter"))
        data = all_data
        timestamps = get_timestamps()

        results = []
        for record in data:
            results.append({
                "symbol": symbol,
                "company_name": COMPANY_NAMES.get(symbol, symbol),
                "fiscal_year": record.get("fiscal_year"),
                "end_date": record.get("date"),
                "period": record.get("period", "FY"),
                "total_revenue": record.get("total_revenue"),
                "gross_profit": record.get("gross_profit"),
                "operating_income": record.get("operating_income"),
                "net_income": record.get("net_income"),
                "eps": record.get("eps"),
                "gross_margin": record.get("gross_margin"),
                "operating_margin": record.get("operating_margin"),
                "net_margin": record.get("net_margin"),
                "currency": "USD",
                "source": "FMP",
                "validation_status": None,
                "file_type": "INCOME_STATEMENT",
                "source_file": record.get("source_url", ""),
                "download_success": True,
                **timestamps,
            })
        return results
    except Exception as e:
        print(f"  FMP error for {symbol}: {e}", file=sys.stderr)
        return []


def _filter_parent_segments(
    records: List[Dict], segment_type: str, symbol: str = ""
) -> List[Dict]:
    """
    Remove overlapping parent segments from FMP data.

    FMP sometimes returns both parent and child segments (e.g., "Google Advertising Revenue"
    alongside "Google Search & Other" + "YouTube Advertising Revenue" + "Google Network").

    Detection methods:
    1. Subset-sum match: segment value ≈ sum of 2-4 other segments (within 0.5%)
    2. Company name match: segment name matches company name/ticker
    3. Duplicate value: two segments with exact same value → remove the less specific one
    """
    from itertools import combinations
    from collections import defaultdict

    typed = [r for r in records if r.get("segment_type") == segment_type]
    if len(typed) <= 2:
        return records

    groups = defaultdict(list)
    for r in typed:
        groups[(r.get("fiscal_year"), r.get("period", "annual"))].append(r)

    parents_to_remove = set()

    # Company name patterns to filter
    company_names_lower = {
        "GOOGL": ["google inc", "alphabet"],
        "AAPL": ["apple inc"],
        "MSFT": ["microsoft corp"],
        "META": ["meta platforms"],
        "AMZN": ["amazon.com", "amazon inc"],
        "NVDA": ["nvidia corp"],
        "AMD": ["advanced micro"],
    }
    name_patterns = company_names_lower.get(symbol, [])

    for key, items in groups.items():
        if len(items) <= 2:
            continue
        sorted_items = sorted(items, key=lambda x: x.get("revenue") or 0, reverse=True)
        revs = [(x.get("segment_name"), x.get("revenue") or 0) for x in sorted_items]

        # Check 1: Duplicate values - run FIRST on all items
        # If two segments have exact same revenue AND the value is large (>15% of group total),
        # both are suspicious (one is parent/mislabel). Small coincidental matches are ignored.
        group_total = sum(r for _, r in revs if r > 0)
        rev_to_names = defaultdict(list)
        for name, rev in revs:
            if rev > 0:
                rev_to_names[rev].append(name)
        for rev, names in rev_to_names.items():
            if len(names) > 1 and group_total > 0 and rev / group_total > 0.15:
                # Remove ALL segments with duplicate large values
                for name in names:
                    parents_to_remove.add((key, name))

        # Check 2: Company name match
        for cname, crev in revs:
            if crev <= 0:
                continue
            cname_lower = cname.lower()
            if any(p in cname_lower for p in name_patterns):
                parents_to_remove.add((key, cname))

        # Check 3: Subset-sum with tight tolerance (0.5%)
        # Only remove if value is large (>10% of total) to avoid false positives
        remaining = [(n, r) for n, r in revs if (key, n) not in parents_to_remove]
        for i, (cname, crev) in enumerate(remaining):
            if crev <= 0:
                continue
            # Skip small segments - coincidental matches are common
            if group_total > 0 and crev / group_total < 0.10:
                continue
            others = [(n, r) for j, (n, r) in enumerate(remaining) if j != i and r > 0 and r < crev]
            if len(others) >= 2:
                found_parent = False
                for size in range(2, min(len(others) + 1, 5)):
                    for combo in combinations(others, size):
                        combo_sum = sum(r for _, r in combo)
                        if combo_sum > 0 and abs(combo_sum - crev) / crev < 0.005:
                            found_parent = True
                            break
                    if found_parent:
                        break
                if found_parent:
                    parents_to_remove.add((key, cname))

    if not parents_to_remove:
        return records

    return [
        r for r in records
        if (
            (r.get("fiscal_year"), r.get("period", "annual")),
            r.get("segment_name"),
        ) not in parents_to_remove
    ]


def fetch_segments_fmp(
    client: FMPClient, symbol: str, include_quarterly: bool = False
) -> List[Dict[str, Any]]:
    """Fetch segment revenue from FMP."""
    try:
        # Get both product and geographic segments
        product_data = client.get_revenue_segments(symbol, period="annual")
        geo_data = client.get_geographic_segments(symbol, period="annual")
        if include_quarterly:
            product_data += client.get_revenue_segments(symbol, period="quarter")
            geo_data += client.get_geographic_segments(symbol, period="quarter")

        timestamps = get_timestamps()
        results = []

        for record in product_data + geo_data:
            results.append({
                "symbol": symbol,
                "company_name": COMPANY_NAMES.get(symbol, symbol),
                "fiscal_year": record.get("fiscal_year"),
                "end_date": record.get("date"),
                "period": record.get("period", "annual"),
                "segment_name": record.get("segment_name"),
                "segment_type": record.get("segment_type"),
                "revenue": record.get("revenue"),
                "revenue_yoy_pct": None,  # Calculate later
                "currency": "USD",
                "source": "FMP",
                "file_type": "SEGMENT_REVENUE",
                "source_file": record.get("source_url", ""),
                "download_success": True,
                **timestamps,
            })

        # Filter overlapping parent segments (e.g., GOOGL "Google Advertising Revenue")
        results = _filter_parent_segments(results, "product", symbol)
        results = _filter_parent_segments(results, "geography", symbol)

        return results
    except Exception as e:
        print(f"  FMP segments error for {symbol}: {e}", file=sys.stderr)
        return []


def fetch_segments_sec_10k(
    client: SECEdgarClient, symbol: str, years: int = 5
) -> List[Dict[str, Any]]:
    """Fetch segment revenue from SEC EDGAR 10-K filings."""
    try:
        data = client.get_segment_revenue_from_10k(symbol, years=years)
        timestamps = get_timestamps()

        results = []
        for record in data:
            results.append({
                "symbol": symbol,
                "company_name": COMPANY_NAMES.get(symbol, symbol),
                "fiscal_year": record.get("fiscal_year"),
                "end_date": record.get("end_date"),
                "period": "annual",
                "segment_name": record.get("segment_name"),
                "segment_type": record.get("segment_type", "product"),
                "revenue": record.get("revenue"),
                "revenue_yoy_pct": None,
                "currency": "USD",
                "source": "SEC_10K",
                "file_type": "SEGMENT_REVENUE",
                "source_file": f"SEC EDGAR 10-K ({symbol})",
                "download_success": True,
                **timestamps,
            })
        return results
    except Exception as e:
        print(f"  SEC 10-K segments error for {symbol}: {e}", file=sys.stderr)
        return []


def cross_check_income(
    sec_data: List[Dict], av_data: List[Dict], threshold: float = 0.05
) -> List[Dict]:
    """
    Cross-check SEC EDGAR data with Alpha Vantage data.
    Flag discrepancies > threshold (5% default).
    """
    # Index Alpha Vantage data by (symbol, fiscal_year)
    av_index = {}
    for record in av_data:
        key = (record.get("symbol"), record.get("fiscal_year"))
        av_index[key] = record

    # Check each SEC record
    for record in sec_data:
        key = (record.get("symbol"), record.get("fiscal_year"))
        av_record = av_index.get(key)

        if av_record:
            # Compare revenue
            sec_rev = record.get("total_revenue")
            av_rev = av_record.get("total_revenue")

            if sec_rev and av_rev and sec_rev > 0:
                diff_pct = abs(sec_rev - av_rev) / sec_rev
                if diff_pct > threshold:
                    record["validation_status"] = f"DISCREPANCY: SEC={sec_rev:,.0f} vs AV={av_rev:,.0f} ({diff_pct:.1%})"
                else:
                    record["validation_status"] = "VALIDATED"
            else:
                record["validation_status"] = "PARTIAL_DATA"
        else:
            record["validation_status"] = "NO_CROSSCHECK"

    return sec_data


def calculate_yoy(rows: List[Dict], value_field: str, yoy_field: str) -> List[Dict]:
    """Calculate year-over-year percentage change."""
    # Group by (symbol, segment_name, segment_type)
    groups = {}
    for row in rows:
        key = (row.get("symbol"), row.get("segment_name"), row.get("segment_type"))
        if key not in groups:
            groups[key] = []
        groups[key].append(row)

    # Calculate YoY for each group
    for key, group_rows in groups.items():
        # Sort by fiscal year
        group_rows.sort(key=lambda x: x.get("fiscal_year") or 0)

        prev_value = None
        for row in group_rows:
            current = row.get(value_field)
            if prev_value and current and prev_value > 0:
                row[yoy_field] = (current - prev_value) / prev_value
            prev_value = current

    return rows


def update_income_statements(
    symbols: List[str],
    sources: List[str],
    out_dir: str,
    years: int = 10,
    sleep: float = 1.0,
    cross_check: bool = True,
    include_quarterly: bool = False,
) -> None:
    """Update income statement data for specified symbols."""
    period_label = "annual + quarterly" if include_quarterly else "annual"
    print(f"Updating income statements ({period_label}) for {len(symbols)} symbols...")

    # Initialize clients
    sec_client = SECEdgarClient()
    av_client = None
    fmp_client = None

    if "alphavantage" in sources or cross_check:
        av_key = load_av_key()
        if av_key:
            av_client = AlphaVantageClient(av_key)
        else:
            print("  Warning: Alpha Vantage API key not found", file=sys.stderr)

    if "fmp" in sources:
        fmp_key = load_fmp_key()
        if fmp_key:
            fmp_client = FMPClient(fmp_key)
        else:
            print("  Warning: FMP API key not found", file=sys.stderr)

    # Load existing data - include period in key for quarterly support
    out_path = os.path.join(out_dir, OUTPUT_INCOME)
    existing = read_existing_csv(out_path, ["symbol", "fiscal_year", "period", "source"])

    all_data = []

    for i, symbol in enumerate(symbols):
        if i > 0:
            time.sleep(sleep)

        print(f"  Fetching {symbol}...")

        # SEC EDGAR (primary)
        if "sec-edgar" in sources:
            sec_data = fetch_income_sec_edgar(
                sec_client, symbol, years, include_quarterly=include_quarterly
            )

            # Cross-check with Alpha Vantage if enabled (annual only)
            if cross_check and av_client:
                time.sleep(sleep)
                av_data = fetch_income_alphavantage(av_client, symbol)
                sec_data = cross_check_income(sec_data, av_data)

            all_data.extend(sec_data)

        # Alpha Vantage (standalone)
        if "alphavantage" in sources and av_client:
            av_data = fetch_income_alphavantage(
                av_client, symbol, include_quarterly=include_quarterly
            )
            all_data.extend(av_data)

        # FMP (standalone)
        if "fmp" in sources and fmp_client:
            fmp_data = fetch_income_fmp(
                fmp_client, symbol, years, include_quarterly=include_quarterly
            )
            all_data.extend(fmp_data)

    # Merge with existing data (keyed by symbol, fiscal_year, period, source)
    for row in all_data:
        key = (row.get("symbol"), str(row.get("fiscal_year")),
               row.get("period", "FY"), row.get("source"))
        existing[key] = row

    # Convert to list and sort
    period_sort = {"FY": "0", "Q1": "1", "Q2": "2", "Q3": "3", "Q4": "4"}
    final_rows = list(existing.values())
    final_rows.sort(key=lambda x: (
        x.get("symbol", ""),
        str(x.get("fiscal_year", "")),
        period_sort.get(x.get("period", "FY"), "9"),
        x.get("source", "")
    ))

    # Write output
    write_csv(out_path, INCOME_FIELDNAMES, final_rows)
    print(f"  Wrote {len(final_rows)} records to {out_path}")


def update_segment_revenue(
    symbols: List[str],
    sources: List[str],
    out_dir: str,
    sleep: float = 1.0,
    years: int = 10,
    include_quarterly: bool = False,
) -> None:
    """Update segment revenue data for specified symbols."""
    period_label = "annual + quarterly" if include_quarterly else "annual"
    print(f"Updating segment revenue ({period_label}) for {len(symbols)} symbols...")

    # Initialize clients
    sec_client = SECEdgarClient() if "sec-edgar" in sources else None
    fmp_client = None
    if "fmp" in sources:
        fmp_key = load_fmp_key()
        if fmp_key:
            fmp_client = FMPClient(fmp_key)
        else:
            print("  Warning: FMP API key not found", file=sys.stderr)

    if not sec_client and not fmp_client:
        print("  No segment revenue source available", file=sys.stderr)
        return

    # Load existing data - include period in key for quarterly support
    out_path = os.path.join(out_dir, OUTPUT_REVENUE)
    existing = read_existing_csv(out_path, ["symbol", "fiscal_year", "period", "segment_name", "source"])

    all_data = []

    for i, symbol in enumerate(symbols):
        if i > 0:
            time.sleep(sleep)

        print(f"  Fetching segments for {symbol}...")

        # Use FMP as primary source; fall back to SEC 10-K if FMP has no data
        symbol_data = []

        # FMP (product & geographic segments)
        if fmp_client:
            segment_data = fetch_segments_fmp(
                fmp_client, symbol, include_quarterly=include_quarterly
            )
            symbol_data.extend(segment_data)

        # SEC EDGAR 10-K parsing only if FMP returned no data for this symbol
        if sec_client and not symbol_data:
            sec_data = fetch_segments_sec_10k(sec_client, symbol, years=min(years, 5))
            symbol_data.extend(sec_data)

        all_data.extend(symbol_data)

    # Calculate YoY
    all_data = calculate_yoy(all_data, "revenue", "revenue_yoy_pct")

    # Merge with existing data
    for row in all_data:
        key = (row.get("symbol"), str(row.get("fiscal_year")),
               row.get("period", "annual"), row.get("segment_name"), row.get("source"))
        existing[key] = row

    # Convert to list and sort
    period_sort = {"annual": "0", "FY": "0", "Q1": "1", "Q2": "2", "Q3": "3", "Q4": "4", "quarter": "5"}
    final_rows = list(existing.values())
    final_rows.sort(key=lambda x: (
        x.get("symbol", ""),
        str(x.get("fiscal_year", "")),
        period_sort.get(x.get("period", "annual"), "9"),
        x.get("segment_type", ""),
        x.get("segment_name", "")
    ))

    # Write output
    write_csv(out_path, REVENUE_FIELDNAMES, final_rows)
    print(f"  Wrote {len(final_rows)} records to {out_path}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update concept stock company financial data from multiple sources"
    )

    # Symbol selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", help="Single stock symbol (e.g., MSFT)")
    group.add_argument("--all", action="store_true", help="Update all concept stock companies")

    # Data type selection
    parser.add_argument(
        "--type",
        choices=["income", "revenue", "all"],
        default="all",
        help="Type of data to update (default: all)",
    )

    # Source selection
    parser.add_argument(
        "--source",
        choices=["sec-edgar", "alphavantage", "fmp", "all"],
        default="all",
        help="Data source to use (default: all)",
    )

    # Options
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Number of years of data to fetch (default: 10)",
    )
    parser.add_argument(
        "--out-dir",
        default=os.getcwd(),
        help="Output directory for CSV files",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.2,
        help="Seconds to sleep between API calls (default: 1.2)",
    )
    parser.add_argument(
        "--no-cross-check",
        action="store_true",
        help="Disable cross-checking with secondary sources",
    )
    parser.add_argument(
        "--period",
        choices=["annual", "quarterly", "all"],
        default="annual",
        help="Period: annual (10-K/FY only), quarterly (include 10-Q), all (both) (default: annual)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine symbols to process
    if args.symbol:
        symbol = args.symbol.upper()
        if symbol not in COMPANY_CIK:
            print(f"Error: Unknown symbol {symbol}. Available: {', '.join(COMPANY_CIK.keys())}", file=sys.stderr)
            return 1
        symbols = [symbol]
    else:
        symbols = list(COMPANY_CIK.keys())

    # Determine sources
    if args.source == "all":
        sources = ["sec-edgar", "alphavantage", "fmp"]
    else:
        sources = [args.source]

    # Determine data types
    data_types = ["income", "revenue"] if args.type == "all" else [args.type]

    # Determine period
    include_quarterly = args.period in ("quarterly", "all")

    print(f"Sources: {', '.join(sources)}")
    print(f"Data types: {', '.join(data_types)}")
    print(f"Period: {args.period}")
    print(f"Symbols: {', '.join(symbols)}")
    print()

    # Update income statements
    if "income" in data_types:
        update_income_statements(
            symbols=symbols,
            sources=sources,
            out_dir=args.out_dir,
            years=args.years,
            sleep=args.sleep,
            cross_check=not args.no_cross_check,
            include_quarterly=include_quarterly,
        )

    # Update segment revenue
    if "revenue" in data_types:
        # FMP + SEC EDGAR 10-K for segment data
        segment_sources = [s for s in sources if s in ("fmp", "sec-edgar")]
        if not segment_sources:
            segment_sources = ["fmp", "sec-edgar"]  # Default to both

        update_segment_revenue(
            symbols=symbols,
            sources=segment_sources,
            out_dir=args.out_dir,
            sleep=args.sleep,
            years=args.years,
            include_quarterly=include_quarterly,
        )

    print("\nDone!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
