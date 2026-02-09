#!/usr/bin/env python3
"""
Generate Quarterly Product Segment Data for Charts

This script generates CSV data suitable for creating quarterly trend charts.
Only companies with available quarterly product segment data are included.

Output: raw_conceptstock_company_quarterly_segments.csv

Usage:
    python scripts/generate_quarterly_segments.py
    python scripts/generate_quarterly_segments.py --years 5
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import datetime


def load_latest_released_quarter(csv_path: str) -> dict:
    """
    Load latest released fiscal quarter for each company from concept_metadata.csv.

    Returns:
        Dict: {symbol: (fy, quarter)} e.g., {'NVDA': (2026, 3), 'GOOGL': (2025, 4)}
    """
    if not os.path.exists(csv_path):
        return {}

    latest_q = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Ticker', '')
                latest_report = row.get('最新財報', '')

                if not ticker or ticker == '-' or not latest_report:
                    continue

                # Parse "FY2026 Q3" format
                match = re.match(r'FY(\d{4})\s+Q(\d)', latest_report)
                if match:
                    fy = int(match.group(1))
                    quarter = int(match.group(2))
                    latest_q[ticker] = (fy, quarter)
    except Exception as e:
        print(f"  Warning: Could not read {csv_path}: {e}")

    return latest_q


def is_quarter_released(fy: int, quarter: int, latest_fy: int, latest_q: int) -> bool:
    """Check if a given quarter has been released based on latest released quarter."""
    if fy < latest_fy:
        return True
    elif fy == latest_fy:
        return quarter <= latest_q
    else:
        return False


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external.sec_edgar_client import SECEdgarClient, COMPANY_CIK
from src.segment_config import UNIFIED_PRODUCT_SEGMENTS


# Companies with quarterly product segment data available from 10-Q parsing
QUARTERLY_PRODUCT_SUPPORTED = ['AMD', 'ORCL', 'WDC']

# Companies with quarterly data from 8-K earnings press releases
QUARTERLY_8K_SUPPORTED = ['NVDA', 'GOOGL', 'MSFT', 'AAPL', 'AMZN', 'META', 'MU', 'DELL', 'QCOM', 'HPQ']

# Company names
COMPANY_NAMES = {
    'NVDA': 'NVIDIA Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com, Inc.',
    'META': 'Meta Platforms, Inc.',
    'MSFT': 'Microsoft Corporation',
    'AMD': 'Advanced Micro Devices, Inc.',
    'AAPL': 'Apple Inc.',
    'ORCL': 'Oracle Corporation',
    'MU': 'Micron Technology, Inc.',
    'WDC': 'Western Digital Corporation',
    'DELL': 'Dell Technologies Inc.',
    'QCOM': 'Qualcomm Inc.',
    'HPQ': 'HP Inc.',
}

# Segment name normalization map (quarterly -> annual standard name)
# This ensures consistency between quarterly and annual reports
SEGMENT_NAME_MAP = {
    # QCOM - remove QCT prefix to match annual report
    'QCT Handsets': 'Handsets',
    'QCT Automotive': 'Automotive',
    'QCT IoT': 'IoT',
    # MU - normalize abbreviations to match annual report
    'Automotive and Embedded': 'Automotive and Edge',
    # ORCL - keep original names (quarterly and annual use same names)
    # AMD - keep old segment names as-is (different org structure pre-2022)
    # MSFT - keep full names as-is (Intelligent Cloud, More Personal Computing, etc.)
    # GOOGL - keep Google Services/Cloud as-is (8-K specific grouping)
    # AMZN - keep AWS/International/North America as-is (8-K specific grouping)
}


def normalize_segment_name(name: str) -> str:
    """Normalize segment name for consistency between quarterly and annual reports."""
    return SEGMENT_NAME_MAP.get(name, name)


def fetch_quarterly_segments(symbols: list, quarters: int = 20) -> list:
    """
    Fetch quarterly product segment data from SEC 10-Q filings.

    Returns:
        List of dicts with: symbol, fiscal_year, quarter, segment_name, revenue, end_date
    """
    client = SECEdgarClient()
    results = []

    for symbol in symbols:
        if symbol not in COMPANY_CIK:
            continue

        print(f"  Fetching 10-Q segments for {symbol}...")
        try:
            segments = client.get_segment_revenue_from_10q(symbol, quarters=quarters)

            # Filter to product segments with reasonable revenue
            # Revenue < $10M is likely a parsing error (unit conversion issue)
            MIN_REVENUE = 10_000_000  # $10M minimum for real segment revenue
            for seg in segments:
                if seg.get('segment_type') != 'product':
                    continue
                revenue = seg.get('revenue', 0) or 0
                if revenue < MIN_REVENUE:
                    continue

                results.append({
                    'symbol': symbol,
                    'company_name': COMPANY_NAMES.get(symbol, symbol),
                    'fiscal_year': seg.get('fiscal_year'),
                    'quarter': seg.get('period', 'Q?'),
                    'segment_name': normalize_segment_name(seg.get('segment_name', '')),
                    'revenue': revenue,
                    'end_date': seg.get('end_date'),
                })

            count = len([r for r in results if r['symbol'] == symbol])
            print(f"    Found {count} product segment records")

        except Exception as e:
            print(f"    Error: {e}")

    return results


def fetch_8k_segments(symbols: list, quarters: int = 20) -> list:
    """
    Fetch quarterly product segment data from SEC 8-K earnings press releases.

    This is useful for companies like NVDA that don't have segment tables
    in their 10-Q filings but do report segments in earnings press releases.

    Returns:
        List of dicts with: symbol, fiscal_year, quarter, segment_name, revenue, end_date
    """
    client = SECEdgarClient()
    results = []

    for symbol in symbols:
        if symbol not in COMPANY_CIK:
            continue

        print(f"  Fetching 8-K segments for {symbol}...")
        try:
            segments = client.get_segment_revenue_from_8k(symbol, quarters=quarters)

            # Filter to product segments with reasonable revenue
            MIN_REVENUE = 10_000_000  # $10M minimum
            for seg in segments:
                if seg.get('segment_type') != 'product':
                    continue
                revenue = seg.get('revenue', 0) or 0
                if revenue < MIN_REVENUE:
                    continue

                results.append({
                    'symbol': symbol,
                    'company_name': COMPANY_NAMES.get(symbol, symbol),
                    'fiscal_year': seg.get('fiscal_year'),
                    'quarter': seg.get('period', 'Q?'),
                    'segment_name': normalize_segment_name(seg.get('segment_name', '')),
                    'revenue': revenue,
                    'end_date': seg.get('end_date'),
                })

            count = len([r for r in results if r['symbol'] == symbol])
            print(f"    Found {count} product segment records")

        except Exception as e:
            print(f"    Error: {e}")

    return results


def load_annual_segments(csv_path: str, symbols: list) -> list:
    """
    Load annual segment data from CSV to fill Q4 gaps.

    10-Q only has Q1-Q3, Q4 is in 10-K (annual).
    We can estimate Q4 = FY - (Q1+Q2+Q3) if we have the FY total.
    """
    if not os.path.exists(csv_path):
        return []

    results = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('symbol') not in symbols:
                continue
            if row.get('segment_type') != 'product':
                continue
            if row.get('period', 'annual') not in ('annual', 'FY'):
                continue

            revenue = float(row.get('revenue') or 0)
            if revenue <= 0:
                continue

            results.append({
                'symbol': row['symbol'],
                'company_name': row.get('company_name', row['symbol']),
                'fiscal_year': int(row.get('fiscal_year', 0)),
                'quarter': 'FY',  # Full year
                'segment_name': row.get('segment_name'),
                'revenue': revenue,
                'end_date': row.get('end_date'),
            })

    return results


def calculate_q4(quarterly_data: list, annual_data: list) -> list:
    """
    Calculate Q4 values: Q4 = FY - (Q1 + Q2 + Q3)

    Returns additional Q4 records.
    """
    q4_results = []

    # Group quarterly by (symbol, fiscal_year, segment_name)
    q_totals = defaultdict(lambda: {'Q1': 0, 'Q2': 0, 'Q3': 0})
    for r in quarterly_data:
        key = (r['symbol'], r['fiscal_year'], r['segment_name'])
        q = r['quarter']
        if q in ('Q1', 'Q2', 'Q3'):
            q_totals[key][q] = r['revenue']

    # Group annual by (symbol, fiscal_year, segment_name)
    fy_totals = {}
    for r in annual_data:
        key = (r['symbol'], r['fiscal_year'], r['segment_name'])
        fy_totals[key] = r['revenue']

    # Calculate Q4
    for key, q_vals in q_totals.items():
        symbol, fy, seg_name = key

        # Only calculate Q4 if ALL of Q1, Q2, Q3 have data
        # This prevents inflated Q4 when some quarters are missing
        if q_vals['Q1'] == 0 or q_vals['Q2'] == 0 or q_vals['Q3'] == 0:
            continue

        q1_q3_sum = q_vals['Q1'] + q_vals['Q2'] + q_vals['Q3']

        if key in fy_totals:
            fy_total = fy_totals[key]
            q4 = fy_total - q1_q3_sum

            if q4 > 0:  # Only add if positive
                q4_results.append({
                    'symbol': symbol,
                    'company_name': COMPANY_NAMES.get(symbol, symbol),
                    'fiscal_year': fy,
                    'quarter': 'Q4',
                    'segment_name': seg_name,
                    'revenue': q4,
                    'end_date': None,  # We don't have exact date
                    'is_calculated': True,
                })

    return q4_results


def generate_csv(data: list, output_path: str):
    """Write data to CSV file."""
    if not data:
        print("  No data to write")
        return

    fieldnames = [
        'symbol', 'company_name', 'fiscal_year', 'quarter',
        'segment_name', 'revenue', 'end_date', 'is_calculated'
    ]

    # Sort by symbol, fiscal_year, quarter, segment
    quarter_order = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4, 'FY': 5}
    data.sort(key=lambda x: (
        x['symbol'],
        x['fiscal_year'],
        quarter_order.get(x['quarter'], 9),
        x['segment_name']
    ))

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Ensure all fields exist
            row.setdefault('is_calculated', False)
            writer.writerow(row)

    print(f"  Wrote {len(data)} records to {output_path}")


def generate_markdown_report(data: list, output_path: str, latest_q_map: dict = None):
    """Generate markdown report with each segment on one line, quarters as columns."""
    if latest_q_map is None:
        latest_q_map = {}

    lines = []

    lines.append("# Quarterly Product Segment Revenue")
    lines.append("")
    lines.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("> Data source: SEC EDGAR 10-Q/10-K filings")
    lines.append("> Format: Columns show YYQn (e.g., 26Q1 = FY2026 Q1)")
    lines.append("> Legend: `-` = not yet released, `x` = released but not available")
    lines.append("> Note: Q4 values are calculated as FY - (Q1+Q2+Q3)")
    lines.append("")

    # Group by symbol
    by_symbol = defaultdict(list)
    for r in data:
        by_symbol[r['symbol']].append(r)

    for symbol in sorted(by_symbol.keys()):
        company_name = COMPANY_NAMES.get(symbol, symbol)
        lines.append(f"## {symbol} - {company_name}")
        lines.append("")

        records = by_symbol[symbol]

        # Get years from data
        years = sorted(set(r['fiscal_year'] for r in records), reverse=True)[:5]

        # Use unified segment list for consistency with annual report
        if symbol in UNIFIED_PRODUCT_SEGMENTS:
            segments = UNIFIED_PRODUCT_SEGMENTS[symbol]
        else:
            # Fallback: use segments from data
            all_segments = sorted(set(r['segment_name'] for r in records))
            segments = []
            for seg in all_segments:
                seg_records = [r for r in records if r['segment_name'] == seg]
                if len(seg_records) >= 2:
                    segments.append(seg)

        if not segments or not years:
            lines.append("No segment data available.")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Build list of all quarters (newest first): 26Q4, 26Q3, 26Q2, 26Q1, 25Q4, ...
        all_quarters = []
        for fy in years:
            for q in [4, 3, 2, 1]:
                all_quarters.append((fy, f"Q{q}"))

        # Get latest released quarter for this symbol
        latest_info = latest_q_map.get(symbol)
        latest_fy = latest_info[0] if latest_info else None
        latest_q_num = latest_info[1] if latest_info else None

        # Format helper with "-" for not released, "x" for released but not available
        def fmt(v, fy=None, q=None):
            if v is None or v == 0:
                # Determine if released or not
                if fy is not None and q is not None and latest_fy is not None and latest_q_num is not None:
                    q_num = int(q[1]) if q.startswith('Q') else 0
                    if is_quarter_released(fy, q_num, latest_fy, latest_q_num):
                        return "x"  # Released but not available
                    else:
                        return "-"  # Not yet released
                return "-"
            if v >= 1e9:
                return f"${v/1e9:.1f}B"
            return f"${v/1e6:.0f}M"

        # Build header with quarters
        header = "| Segment |"
        separator = "|---------|"
        for fy, q in all_quarters:
            # Format: 26Q4, 26Q3, etc.
            header += f" {fy % 100}{q} |"
            separator += "------|"
        lines.append(header)
        lines.append(separator)

        # Build rows - one segment per line with all quarters
        for seg in segments:
            # Build lookup for this segment
            seg_records = [r for r in records if r['segment_name'] == seg]
            q_vals = {}
            for r in seg_records:
                key = (r['fiscal_year'], r['quarter'])
                q_vals[key] = r['revenue']

            row = f"| {seg} |"
            for fy, q in all_quarters:
                val = q_vals.get((fy, q), 0)
                row += f" {fmt(val, fy=fy, q=q)} |"
            lines.append(row)

        lines.append("")
        lines.append("---")
        lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  Wrote markdown report to {output_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate quarterly product segment data for charts"
    )
    parser.add_argument(
        "--out-dir",
        default=os.getcwd(),
        help="Output directory"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Number of years to include"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("Generating quarterly product segment data...")
    print(f"  Years: {args.years}")

    # Load latest released quarter for each company
    metadata_path = os.path.join(args.out_dir, "concept_metadata.csv")
    latest_q_map = load_latest_released_quarter(metadata_path)
    if latest_q_map:
        print(f"  Loaded latest released quarter for {len(latest_q_map)} companies")

    quarters = args.years * 4
    all_symbols = QUARTERLY_PRODUCT_SUPPORTED + QUARTERLY_8K_SUPPORTED

    # Fetch quarterly data from 10-Q (AMD, ORCL, WDC)
    quarterly_data = fetch_quarterly_segments(QUARTERLY_PRODUCT_SUPPORTED, quarters=quarters)
    print(f"  10-Q records: {len(quarterly_data)}")

    # Fetch quarterly data from 8-K (NVDA, etc.)
    quarterly_8k = fetch_8k_segments(QUARTERLY_8K_SUPPORTED, quarters=quarters)
    print(f"  8-K records: {len(quarterly_8k)}")
    quarterly_data.extend(quarterly_8k)

    print(f"  Total quarterly records: {len(quarterly_data)}")

    # Load annual data for Q4 calculation
    annual_csv = os.path.join(args.out_dir, "raw_conceptstock_company_revenue.csv")
    annual_data = load_annual_segments(annual_csv, all_symbols)
    print(f"  Loaded {len(annual_data)} annual records for Q4 calculation")

    # Calculate Q4 values
    q4_data = calculate_q4(quarterly_data, annual_data)
    print(f"  Calculated {len(q4_data)} Q4 records")

    # Combine all data
    all_data = quarterly_data + q4_data

    # Deduplicate: prefer calculated Q4 over parsed Q4, or higher revenue
    seen = {}
    for r in all_data:
        key = (r['symbol'], r['fiscal_year'], r['quarter'], r['segment_name'])
        if key not in seen:
            seen[key] = r
        else:
            existing = seen[key]
            # Prefer calculated Q4 (more reliable)
            if r.get('is_calculated') and not existing.get('is_calculated'):
                seen[key] = r
            elif not r.get('is_calculated') and existing.get('is_calculated'):
                pass  # Keep existing calculated value
            elif r['revenue'] > existing['revenue']:
                # Same type, prefer higher revenue
                seen[key] = r
    all_data = list(seen.values())
    print(f"  After deduplication: {len(all_data)} records")

    # Write CSV
    csv_path = os.path.join(args.out_dir, "raw_conceptstock_company_quarterly_segments.csv")
    generate_csv(all_data, csv_path)

    # Write markdown report
    md_path = os.path.join(args.out_dir, "raw_conceptstock_company_quarterly_segments.md")
    generate_markdown_report(all_data, md_path, latest_q_map=latest_q_map)

    print("Done!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
