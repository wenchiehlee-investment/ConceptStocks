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
import sys
from collections import defaultdict
from datetime import datetime


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
}

# Companies with FMP segment data available
FMP_SUPPORTED = ['NVDA', 'GOOGL', 'AMZN', 'META', 'MSFT', 'AMD', 'AAPL']

# Companies without FMP segment data (need SEC EDGAR fallback)
SEC_ONLY = ['ORCL', 'MU', 'WDC']

# Display order
DISPLAY_ORDER = ['NVDA', 'GOOGL', 'AMZN', 'META', 'MSFT', 'AMD', 'AAPL', 'ORCL', 'MU', 'WDC']

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
    'Microsoft Three Six Five Commercial Products And Cloud Services': 'Microsoft 365 Commercial',
    'Microsoft Three Six Five Consumer Products and Cloud Services': 'Microsoft 365 Consumer',
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
}


def normalize_segment_name(name: str) -> str:
    """Normalize segment name to canonical form."""
    # Clean up whitespace
    name = ' '.join(name.split())
    return SEGMENT_NAME_MAP.get(name, name)


def fmt_revenue(val):
    """Format revenue value for display."""
    if val is None or val == 0:
        return "-"
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


def load_segment_data(csv_path: str, override_path: str = None) -> dict:
    """
    Load segment revenue data from CSV file with optional overrides.

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

    # Apply manual overrides (fill gaps, don't replace existing data)
    for (symbol, fy, seg_type, seg_name), revenue in overrides.items():
        if fy not in data[symbol][seg_type][seg_name]:
            data[symbol][seg_type][seg_name][fy] = revenue
            print(f"    Applied override: {symbol} FY{fy} {seg_name}")

    return dict(data)


def generate_markdown(data: dict, years: int = 5) -> str:
    """Generate markdown content in trend-chart format."""
    lines = []

    # Header
    lines.append("# Annual Product Segment Revenue")
    lines.append("")
    lines.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("> Data sources: FMP (annual segments), SEC EDGAR 10-K (ORCL/MU/WDC)")
    lines.append(f"> Coverage: {years} fiscal years")
    lines.append("> Format: Segment-centric with years as columns (suitable for trend charts)")
    lines.append("> Note: Segment names are normalized for consistent trend tracking (e.g., 'YouTube Ads' = 'YouTube Advertising Revenue')")
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

        # Find top segment by revenue in latest year
        top_seg = None
        top_rev = 0
        for seg_name, year_data in product_data.items():
            rev = year_data.get(latest_fy, 0)
            if rev > top_rev:
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

            # Sort years and limit to requested number
            sorted_years = sorted(all_years, reverse=True)[:years]
            sorted_years = sorted(sorted_years)  # Ascending for display

            # Sort segments by total revenue (descending)
            seg_totals = {}
            for seg_name, year_data in type_data.items():
                seg_totals[seg_name] = sum(year_data.values())

            sorted_segments = sorted(type_data.keys(), key=lambda x: seg_totals.get(x, 0), reverse=True)

            # Limit to top 10 segments
            sorted_segments = sorted_segments[:10]

            lines.append(f"### {type_label}")
            lines.append("")

            # Generate table for each segment
            for seg_name in sorted_segments:
                year_data = type_data[seg_name]

                # Skip segments with too few data points
                valid_years = [y for y in sorted_years if year_data.get(y, 0) > 0]
                if len(valid_years) < 2:
                    continue

                lines.append(f"#### {seg_name}")
                lines.append("")

                # Table header with years
                header = "| FY |"
                for fy in sorted_years:
                    header += f" {fy} |"
                lines.append(header)

                sep = "|----" + "|----" * len(sorted_years) + "|"
                lines.append(sep)

                # Revenue row
                row = "| Revenue |"
                for fy in sorted_years:
                    rev = year_data.get(fy, 0)
                    row += f" {fmt_revenue(rev)} |"
                lines.append(row)

                # YoY change (dollar amount)
                row = "| Change |"
                prev_rev = None
                for fy in sorted_years:
                    rev = year_data.get(fy, 0)
                    if prev_rev and prev_rev > 0 and rev > 0:
                        change = rev - prev_rev
                        row += f" {fmt_revenue(change) if change >= 0 else fmt_revenue(change)} |"
                    else:
                        row += " - |"
                    prev_rev = rev if rev > 0 else prev_rev
                lines.append(row)

                # YoY growth (percentage)
                row = "| YoY % |"
                prev_rev = None
                for fy in sorted_years:
                    rev = year_data.get(fy, 0)
                    if prev_rev and prev_rev > 0 and rev > 0:
                        yoy = (rev - prev_rev) / prev_rev * 100
                        row += f" {yoy:+.0f}% |"
                    else:
                        row += " - |"
                    prev_rev = rev if rev > 0 else prev_rev
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

    # Load annual segment data from CSV with manual overrides
    csv_path = os.path.join(args.out_dir, "raw_conceptstock_company_revenue.csv")
    override_path = os.path.join(args.out_dir, "segment_overrides.csv")
    print(f"  Loading segment data from {csv_path}")
    data = load_segment_data(csv_path, override_path=override_path)

    if not data:
        print("  Warning: No segment data found. Run update_company_financials.py first.")
    else:
        print(f"  Loaded data for {len(data)} companies")

    # Generate markdown
    print("  Generating markdown...")
    markdown_content = generate_markdown(data, years=args.years)

    # Write output file
    output_path = os.path.join(args.out_dir, "raw_conceptstock_company_segments.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  Wrote {output_path}")
    print("Done!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
