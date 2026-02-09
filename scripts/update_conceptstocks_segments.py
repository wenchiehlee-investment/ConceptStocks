#!/usr/bin/env python3
"""
Generate Concept Stock Annual Segment Revenue Report

This script generates a formatted markdown report showing annual segment revenue
in a trend-chart-friendly format (segment-centric with years as columns).

Data sources:
- raw_conceptstock_company_revenue.csv (FMP + SEC EDGAR annual data)

Output:
- raw_conceptstock_company_segments.md

Usage:
    python scripts/update_conceptstocks_segments.py
    python scripts/update_conceptstocks_segments.py --years 5
"""

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.segment_config import UNIFIED_PRODUCT_SEGMENTS


def load_latest_released_fy(csv_path: str) -> dict:
    """
    Load latest released fiscal year for each company from concept_metadata.csv.

    The 最新財報 column contains values like "FY2026 Q3" or "FY2025 Q4".
    For annual reports, we consider a FY as released if Q4 is released.

    Returns:
        Dict: {symbol: latest_released_fy} e.g., {'NVDA': 2025, 'GOOGL': 2025}
    """
    if not os.path.exists(csv_path):
        return {}

    latest_fy = {}
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
                    # For annual data, FY is complete only if Q4 is released
                    if quarter == 4:
                        latest_fy[ticker] = fy
                    else:
                        latest_fy[ticker] = fy - 1  # Previous FY is complete
    except Exception as e:
        print(f"  Warning: Could not read {csv_path}: {e}")

    return latest_fy


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
    'QCOM': 'Qualcomm Inc.',
    'DELL': 'Dell Technologies Inc.',
    'HPQ': 'HP Inc.',
}

# Companies with FMP segment data available
FMP_SUPPORTED = ['NVDA', 'GOOGL', 'AMZN', 'META', 'MSFT', 'AMD', 'AAPL']

# Companies without FMP segment data (need SEC EDGAR fallback)
SEC_ONLY = ['ORCL', 'MU', 'WDC', 'QCOM', 'DELL', 'HPQ']

# Display order (A-Z alphabetical)
DISPLAY_ORDER = ['AAPL', 'AMD', 'AMZN', 'DELL', 'GOOGL', 'HPQ', 'META', 'MSFT', 'MU', 'NVDA', 'ORCL', 'QCOM', 'WDC']

# Segments to skip (parsing errors, duplicates, or non-revenue items)
SKIP_SEGMENTS = {
    # QCOM - SEC 10-K parsing issues (values in wrong units or non-revenue items)
    'EBT',  # Earnings Before Tax - not a revenue segment
    'Equipment and services',  # Parent segment, overlaps with Handsets+IoT+Automotive
    'RFFE',  # Sub-segment of Handsets
    # MU - Old segment names with parsing errors
    'Compute and Networking',
    'Patent cross-license agreement',
    # WDC - Old geographic segments replaced by new structure
    'China',
    'Hong Kong',
    'Rest of Asia',
    'United States',
    # Common non-revenue items from SEC 10-K parsing
    'EBITDA',
    'Adjusted EBITDA',
    'Cash flow from operations',
    'Free cash flow',
    'Adjusted free cash flow',
    'Products (a)',  # Footnote reference, not actual segment
    'Services (b)',  # Footnote reference, not actual segment
}

# Minimum revenue threshold to filter out parsing errors (values should be > $100M)
MIN_REVENUE_THRESHOLD = 100_000_000

# Segment name normalization mapping
# Maps variant names to canonical names for consistent trend tracking
SEGMENT_NAME_MAP = {
    # GOOGL
    'YouTube Advertising Revenue': 'YouTube Ads',
    'Google Subscriptions, Platforms, And Devices': 'Google Subscriptions',
    'Google Subscriptions\n, Platforms, And Devices': 'Google Subscriptions',
    "Google Subscriptions\n": 'Google Subscriptions',
    'Google Network Members\' Properties': 'Google Network',
    'Google Properties': 'Google Search & Other',
    'Other Bets Revenues': 'Other Bets',
    # MSFT
    'Xbox': 'Gaming',
    'Microsoft Three Six Five Commercial Products And Cloud Services': 'Microsoft Office',
    'Microsoft Three Six Five Consumer Products and Cloud Services': 'Microsoft Office',
    'Microsoft Office System': 'Microsoft Office',
    'Consulting And Product Support Services': 'Enterprise Services',
    # AMD - Note: AMD changed segment structure in 2022
    # Pre-2022: "Computing and Graphics" + "Enterprise, Embedded and Semi-Custom"
    # Post-2022: "Data Center" + "Client" + "Gaming" + "Embedded"
    # We don't map old names as they represent different organizational structures
    # AAPL
    'Service': 'Services',
    # MU
    'CMBU': 'Cloud Memory',
    'MCBU': 'Mobile and Client',
    'CDBU': 'Core Data Center',
    'AEBU': 'Automotive and Edge',
    'CNBU': 'Compute and Networking',
    'MBU': 'Mobile',
    'EBU': 'Embedded',
    'SBU': 'Storage',
    # QCOM
    'IoT (internet of things)': 'IoT',
}


def normalize_segment_name(name: str) -> str:
    """Normalize segment name to canonical form."""
    # Clean up whitespace
    name = ' '.join(name.split())
    return SEGMENT_NAME_MAP.get(name, name)


def fmt_revenue(val, fy: int = None, latest_released_fy: int = None):
    """
    Format revenue value for display.

    Args:
        val: Revenue value
        fy: Fiscal year of the data
        latest_released_fy: Latest released fiscal year for the company

    Returns:
        str: Formatted value, "-" for not yet released, "x" for released but not available
    """
    if val is None or val == 0:
        # Determine if it's "not yet released" or "released but not available"
        if fy is not None and latest_released_fy is not None:
            if fy > latest_released_fy:
                return "-"  # Not yet released
            else:
                return "x"  # Released but not available
        return "-"  # Default to "-" if we don't have FY info

    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}${abs_val/1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"{sign}${abs_val/1e6:.0f}M"
    else:
        return f"{sign}${abs_val:,.0f}"


def load_override_data(csv_path: str) -> dict:
    """
    Load manual override data for missing segments.

    Returns:
        Dict: {(symbol, fiscal_year, segment_name): revenue}
    """
    if not os.path.exists(csv_path):
        return {}

    overrides = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('symbol')
            fy = int(row.get('fiscal_year') or 0)
            seg_name = normalize_segment_name(row.get('segment_name', ''))
            seg_type = row.get('segment_type', 'product')
            revenue = float(row.get('revenue') or 0)

            if symbol and fy and seg_name and revenue > 0:
                key = (symbol, fy, seg_type, seg_name)
                overrides[key] = revenue

    return overrides


def load_quarterly_as_annual(csv_path: str) -> dict:
    """
    Load quarterly segment data and aggregate to annual totals.

    This is used for companies where annual data is missing or uses different
    segment names (e.g., DELL, HPQ).

    Returns:
        Dict: {symbol: {segment_type: {segment_name: {year: revenue}}}}
    """
    if not os.path.exists(csv_path):
        return {}

    # Structure: symbol -> segment_type -> segment_name -> year -> quarter -> revenue
    quarterly = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict))))

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('symbol')
            fy = int(row.get('fiscal_year') or 0)
            quarter = row.get('quarter', '')
            seg_name = row.get('segment_name', '')
            revenue = float(row.get('revenue') or 0)
            is_calculated = row.get('is_calculated', 'False') == 'True'

            if not symbol or not fy or not seg_name or not quarter:
                continue

            # Only include Q1-Q4 data (not FY totals)
            if quarter not in ('Q1', 'Q2', 'Q3', 'Q4'):
                continue

            # Skip calculated Q4 values that seem wrong (>50% of FY total estimate)
            if is_calculated and quarter == 'Q4':
                # Skip this - we'll calculate from Q1-Q3 if we have all of them
                continue

            seg_name = normalize_segment_name(seg_name)
            quarterly[symbol]['product'][seg_name][fy][quarter] = revenue

    # Aggregate to annual totals (only if we have Q1-Q4 or Q1-Q3)
    annual = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for symbol in quarterly:
        for seg_type in quarterly[symbol]:
            for seg_name in quarterly[symbol][seg_type]:
                for fy in quarterly[symbol][seg_type][seg_name]:
                    q_data = quarterly[symbol][seg_type][seg_name][fy]

                    # Calculate annual total from available quarters
                    quarters_available = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if q_data.get(q, 0) > 0]

                    if len(quarters_available) >= 3:
                        # Sum available quarters
                        total = sum(q_data.get(q, 0) for q in quarters_available)
                        if total > MIN_REVENUE_THRESHOLD:
                            annual[symbol][seg_type][seg_name][fy] = total

    return dict(annual)


def load_segment_data(csv_path: str, override_path: str = None, quarterly_path: str = None) -> dict:
    """
    Load segment revenue data from CSV file with optional overrides.

    Args:
        csv_path: Path to annual segment revenue CSV
        override_path: Path to manual override CSV
        quarterly_path: Path to quarterly segment CSV (for aggregating to annual)

    Returns:
        Dict: {symbol: {segment_type: {segment_name: {year: revenue}}}}
    """
    if not os.path.exists(csv_path):
        return {}

    # Load manual overrides first
    overrides = {}
    if override_path:
        overrides = load_override_data(override_path)
        if overrides:
            print(f"  Loaded {len(overrides)} manual override records")

    # Load quarterly data aggregated to annual (for DELL, HPQ, etc.)
    quarterly_annual = {}
    if quarterly_path:
        quarterly_annual = load_quarterly_as_annual(quarterly_path)
        if quarterly_annual:
            print(f"  Loaded quarterly data for {len(quarterly_annual)} companies")

    # Structure: symbol -> segment_type -> segment_name -> year -> revenue
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('symbol')
            fy = int(row.get('fiscal_year') or 0)
            period = row.get('period', 'annual')
            seg_type = row.get('segment_type', 'product')
            seg_name = row.get('segment_name', '')
            revenue = float(row.get('revenue') or 0)

            # Only include annual data
            if period not in ('annual', 'FY'):
                continue

            if seg_name and revenue > 0:
                # Normalize segment name for consistent tracking
                seg_name = normalize_segment_name(seg_name)
                # Merge if same normalized name exists
                if fy in data[symbol][seg_type][seg_name]:
                    # Keep the larger value (in case of duplicates)
                    data[symbol][seg_type][seg_name][fy] = max(
                        data[symbol][seg_type][seg_name][fy], revenue
                    )
                else:
                    data[symbol][seg_type][seg_name][fy] = revenue

    # Apply manual overrides (fill gaps, or replace if override value is higher)
    for (symbol, fy, seg_type, seg_name), revenue in overrides.items():
        existing = data[symbol][seg_type][seg_name].get(fy, 0)
        if existing == 0:
            data[symbol][seg_type][seg_name][fy] = revenue
            print(f"    Applied override: {symbol} FY{fy} {seg_name}")
        elif revenue > existing * 1.05:  # Override if >5% higher (likely more complete)
            data[symbol][seg_type][seg_name][fy] = revenue
            print(f"    Applied override (replaced): {symbol} FY{fy} {seg_name} ({existing/1e9:.1f}B -> {revenue/1e9:.1f}B)")

    # Merge quarterly-aggregated annual data for companies with missing/different segments
    # Priority: use quarterly data if annual data is missing or uses different segment names
    QUARTERLY_PRIORITY = ['DELL', 'HPQ']  # Companies where 8-K quarterly data is more accurate

    for symbol in quarterly_annual:
        for seg_type in quarterly_annual[symbol]:
            for seg_name in quarterly_annual[symbol][seg_type]:
                for fy, revenue in quarterly_annual[symbol][seg_type][seg_name].items():
                    existing = data[symbol][seg_type][seg_name].get(fy, 0)

                    if symbol in QUARTERLY_PRIORITY:
                        # For these companies, prefer quarterly aggregated data
                        if existing == 0 or revenue > existing * 0.5:  # Use quarterly if missing or seems valid
                            data[symbol][seg_type][seg_name][fy] = revenue
                            if existing == 0:
                                print(f"    Added from quarterly: {symbol} FY{fy} {seg_name} = ${revenue/1e9:.1f}B")
                    else:
                        # For other companies, only fill gaps
                        if existing == 0:
                            data[symbol][seg_type][seg_name][fy] = revenue
                            print(f"    Added from quarterly: {symbol} FY{fy} {seg_name} = ${revenue/1e9:.1f}B")

    return dict(data)


def generate_markdown(data: dict, years: int = 5, latest_fy_map: dict = None) -> str:
    """
    Generate markdown content in trend-chart format.

    Args:
        data: Segment revenue data
        years: Number of years to include
        latest_fy_map: Dict mapping symbol to latest released fiscal year
    """
    if latest_fy_map is None:
        latest_fy_map = {}

    lines = []

    # Header
    lines.append("# Annual Product Segment Revenue")
    lines.append("")
    lines.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("> Data sources: FMP (annual segments), SEC EDGAR 10-K (ORCL/MU/WDC)")
    lines.append(f"> Coverage: {years} fiscal years")
    lines.append("> Format: Single table per company with segments as rows, years as columns")
    lines.append("> Legend: `-` = not yet released, `x` = released but not available")
    lines.append("> Note: Segment names are normalized for consistent trend tracking")
    lines.append("")

    # Summary table
    lines.append("## Summary (Latest Fiscal Year)")
    lines.append("")
    lines.append("| Symbol | Company | FY | Top Segment | Revenue | Source |")
    lines.append("|--------|---------|----|--------------------|---------|--------|")

    for symbol in DISPLAY_ORDER:
        symbol_data = data.get(symbol, {})
        product_data = symbol_data.get('product', {})

        if not product_data:
            lines.append(f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | - | No data | - | - |")
            continue

        # Find latest year and top segment
        all_years = set()
        for seg_name, year_data in product_data.items():
            all_years.update(year_data.keys())

        if not all_years:
            lines.append(f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | - | No data | - | - |")
            continue

        latest_fy = max(all_years)

        # Find top segment by revenue in latest year (skip problematic segments)
        top_seg = None
        top_rev = 0
        for seg_name, year_data in product_data.items():
            if seg_name in SKIP_SEGMENTS:
                continue
            rev = year_data.get(latest_fy, 0)
            if rev >= MIN_REVENUE_THRESHOLD and rev > top_rev:
                top_rev = rev
                top_seg = seg_name

        source = "SEC" if symbol in SEC_ONLY else "FMP"
        lines.append(
            f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | "
            f"FY{latest_fy} | {top_seg or 'N/A'} | {fmt_revenue(top_rev)} | {source} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed sections for each company
    for symbol in DISPLAY_ORDER:
        company_name = COMPANY_NAMES.get(symbol, symbol)
        lines.append(f"## {symbol} - {company_name}")
        lines.append("")

        symbol_data = data.get(symbol, {})

        if not symbol_data:
            lines.append("*No segment data available*")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Process each segment type
        for seg_type in ['product', 'geography']:
            type_data = symbol_data.get(seg_type, {})
            if not type_data:
                continue

            type_label = "Product Segments" if seg_type == 'product' else "Geographic Segments"

            # Collect all years across all segments
            all_years = set()
            for seg_name, year_data in type_data.items():
                all_years.update(year_data.keys())

            if not all_years:
                continue

            # Sort years and limit to requested number (newest first)
            sorted_years = sorted(all_years, reverse=True)[:years]

            # Sort segments by latest year revenue (descending)
            latest_fy = max(sorted_years)
            seg_latest_rev = {}
            for seg_name, year_data in type_data.items():
                seg_latest_rev[seg_name] = year_data.get(latest_fy, 0)

            # For product segments, use unified segment list
            if seg_type == 'product' and symbol in UNIFIED_PRODUCT_SEGMENTS:
                # Use unified segments, ordered by revenue
                unified_segs = UNIFIED_PRODUCT_SEGMENTS[symbol]
                filtered_segments = []
                for seg_name in unified_segs:
                    if seg_name in SKIP_SEGMENTS:
                        continue
                    filtered_segments.append(seg_name)
            else:
                # For geographic segments, use existing logic
                sorted_segments = sorted(type_data.keys(), key=lambda x: seg_latest_rev.get(x, 0), reverse=True)

                # Filter segments: must have at least 2 years of valid data
                filtered_segments = []
                for seg_name in sorted_segments:
                    # Skip known problematic segments
                    if seg_name in SKIP_SEGMENTS:
                        continue

                    year_data = type_data.get(seg_name, {})
                    # Count years with valid revenue (above threshold to filter parsing errors)
                    valid_years = [
                        y for y in sorted_years
                        if year_data.get(y, 0) >= MIN_REVENUE_THRESHOLD
                    ]
                    if len(valid_years) >= 2:
                        filtered_segments.append(seg_name)

                # Limit to top 10 segments
                filtered_segments = filtered_segments[:10]

            if not filtered_segments:
                continue

            lines.append(f"### {type_label}")
            lines.append("")

            # Generate single table with all segments as rows
            # Table header with years
            header = "| Segment |"
            for fy in sorted_years:
                header += f" FY{fy} |"
            lines.append(header)

            sep = "|---------|" + "-------:|" * len(sorted_years)
            lines.append(sep)

            # One row per segment
            latest_released = latest_fy_map.get(symbol)
            for seg_name in filtered_segments:
                year_data = type_data.get(seg_name, {})
                row = f"| {seg_name} |"
                for fy in sorted_years:
                    rev = year_data.get(fy, 0)
                    row += f" {fmt_revenue(rev, fy=fy, latest_released_fy=latest_released)} |"
                lines.append(row)

            lines.append("")

        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate concept stock annual segment revenue report"
    )
    parser.add_argument(
        "--out-dir",
        default=os.getcwd(),
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Number of years to include (default: 5)"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    print("Generating annual segment revenue report...")
    print(f"  Years: {args.years}")

    # Load latest released FY for each company from concept_metadata.csv
    metadata_path = os.path.join(args.out_dir, "concept_metadata.csv")
    latest_fy_map = load_latest_released_fy(metadata_path)
    if latest_fy_map:
        print(f"  Loaded latest released FY for {len(latest_fy_map)} companies")

    # Load annual segment data from CSV with manual overrides and quarterly aggregation
    csv_path = os.path.join(args.out_dir, "raw_conceptstock_company_revenue.csv")
    override_path = os.path.join(args.out_dir, "segment_overrides.csv")
    quarterly_path = os.path.join(args.out_dir, "raw_conceptstock_company_quarterly_segments.csv")
    print(f"  Loading segment data from {csv_path}")
    data = load_segment_data(csv_path, override_path=override_path, quarterly_path=quarterly_path)

    if not data:
        print("  Warning: No segment data found. Run update_company_financials.py first.")
    else:
        print(f"  Loaded data for {len(data)} companies")

    # Generate markdown
    print("  Generating markdown...")
    markdown_content = generate_markdown(data, years=args.years, latest_fy_map=latest_fy_map)

    # Write output file
    output_path = os.path.join(args.out_dir, "raw_conceptstock_company_segments.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  Wrote {output_path}")
    print("Done!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
