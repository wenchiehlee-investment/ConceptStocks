#!/usr/bin/env python3
"""
Generate Concept Stock Segment Revenue Markdown Report

This script generates a formatted markdown report showing:
- 5 years of annual segment revenue
- Quarterly segment revenue (from SEC 10-Q filings where available)

Data sources:
- raw_conceptstock_company_revenue.csv (FMP annual data)
- SEC EDGAR 10-K/10-Q parsing for companies without FMP data

Usage:
    python scripts/update_conceptstocks_segments.py
    python scripts/update_conceptstocks_segments.py --years 5 --include-quarterly
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.external.sec_edgar_client import SECEdgarClient, COMPANY_CIK


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

# Companies with FMP segment data available (free tier - annual only)
FMP_SUPPORTED = ['NVDA', 'GOOGL', 'AMZN', 'META', 'MSFT', 'AMD', 'AAPL']

# Companies without FMP segment data (need SEC EDGAR fallback)
SEC_ONLY = ['ORCL', 'MU', 'WDC']

# Companies with 10-Q segment parsing support
QUARTERLY_SUPPORTED = ['NVDA', 'ORCL', 'WDC']

# Display order
DISPLAY_ORDER = ['NVDA', 'GOOGL', 'AMZN', 'META', 'MSFT', 'AMD', 'AAPL', 'ORCL', 'MU', 'WDC']


def fmt_revenue(val):
    """Format revenue value for display."""
    if val is None:
        return "N/A"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e9:
        return f"{sign}${abs_val/1e9:.1f}B"
    elif abs_val >= 1e6:
        return f"{sign}${abs_val/1e6:.1f}M"
    else:
        return f"{sign}${abs_val:,.0f}"


def load_segment_data(csv_path: str, years: int = 5) -> dict:
    """
    Load segment revenue data from CSV file.

    Returns:
        Dict: {symbol: {year: {period: {'product': [(name, rev), ...], 'geography': [...]}}}}
    """
    if not os.path.exists(csv_path):
        return {}

    segments = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            segments.append(row)

    # Group by symbol -> fiscal_year -> period
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'product': [], 'geography': []})))

    for seg in segments:
        symbol = seg.get('symbol')
        fy = int(seg.get('fiscal_year') or 0)
        period = seg.get('period', 'annual')
        seg_type = seg.get('segment_type')
        seg_name = seg.get('segment_name')
        revenue = float(seg.get('revenue') or 0)

        if seg_type == 'product':
            data[symbol][fy][period]['product'].append((seg_name, revenue))
        elif seg_type == 'geography':
            data[symbol][fy][period]['geography'].append((seg_name, revenue))

    # Sort segments by revenue (descending) and filter to recent years
    result = {}
    for symbol, fy_data in data.items():
        fy_list = sorted(fy_data.keys(), reverse=True)[:years]
        result[symbol] = {}
        for fy in fy_list:
            result[symbol][fy] = {}
            for period, seg_data in fy_data[fy].items():
                seg_data['product'].sort(key=lambda x: x[1], reverse=True)
                seg_data['geography'].sort(key=lambda x: x[1], reverse=True)
                result[symbol][fy][period] = seg_data

    return result


def fetch_sec_quarterly_segments(symbols: list, quarters: int = 20) -> dict:
    """
    Fetch quarterly segment revenue from SEC EDGAR 10-Q filings.

    Returns:
        Dict: {symbol: {year: {period: {'product': [...], 'geography': [...]}}}}
    """
    client = SECEdgarClient()
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'product': [], 'geography': []})))

    for symbol in symbols:
        if symbol not in COMPANY_CIK:
            continue
        try:
            print(f"  Fetching 10-Q segments for {symbol}...")
            segments = client.get_segment_revenue_from_10q(symbol, quarters=quarters)

            for seg in segments:
                fy = seg.get('fiscal_year')
                period = seg.get('period', 'Q?')
                seg_type = seg.get('segment_type', 'product')
                seg_name = seg.get('segment_name')
                revenue = seg.get('revenue', 0) or 0

                # Skip zero-value segments
                if revenue <= 0:
                    continue

                if seg_type == 'geography':
                    result[symbol][fy][period]['geography'].append((seg_name, revenue))
                else:
                    result[symbol][fy][period]['product'].append((seg_name, revenue))

            # Sort by revenue
            for fy in result[symbol]:
                for period in result[symbol][fy]:
                    result[symbol][fy][period]['product'].sort(key=lambda x: x[1], reverse=True)
                    result[symbol][fy][period]['geography'].sort(key=lambda x: x[1], reverse=True)

            count = sum(1 for fy in result[symbol] for p in result[symbol][fy])
            print(f"    Found {count} quarter-periods with data")

        except Exception as e:
            print(f"  Warning: Could not fetch 10-Q segments for {symbol}: {e}")

    return dict(result)


def generate_markdown(
    annual_data: dict,
    quarterly_data: dict,
    years: int = 5,
    include_quarterly: bool = True
) -> str:
    """Generate markdown content from segment data."""
    lines = []

    # Header
    lines.append("# Concept Stock Segment Revenue")
    lines.append("")
    lines.append(f"> Last updated: {datetime.now().strftime('%Y-%m-%d')}")
    sources = "FMP (annual segments), SEC EDGAR 10-K/10-Q (segment parsing)"
    lines.append(f"> Data sources: {sources}")
    lines.append(f"> Coverage: {years} fiscal years" + (" + quarterly data" if include_quarterly else ""))
    lines.append("")

    # Summary table - latest annual data
    lines.append("## Summary (Latest Fiscal Year)")
    lines.append("")
    lines.append("| Symbol | Company | FY | Top Product Segment | Revenue | Source |")
    lines.append("|--------|---------|----|--------------------|---------|--------|")

    for symbol in DISPLAY_ORDER:
        data = annual_data.get(symbol, {})
        if not data:
            lines.append(f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | - | No data | - | - |")
            continue

        latest_fy = max(data.keys()) if data else 0
        fy_data = data.get(latest_fy, {}).get('annual', {})
        products = fy_data.get('product', [])

        if products:
            top_seg = products[0]
            source = "SEC" if symbol in SEC_ONLY else "FMP"
            lines.append(
                f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | "
                f"FY{latest_fy} | {top_seg[0]} | {fmt_revenue(top_seg[1])} | {source} |"
            )
        else:
            lines.append(f"| {symbol} | {COMPANY_NAMES.get(symbol, symbol)} | FY{latest_fy} | No segment data | - | - |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed sections for each company
    for symbol in DISPLAY_ORDER:
        company_name = COMPANY_NAMES.get(symbol, symbol)
        lines.append(f"## {symbol} - {company_name}")
        lines.append("")

        annual = annual_data.get(symbol, {})
        quarterly = quarterly_data.get(symbol, {})

        if not annual and not quarterly:
            lines.append("*No segment data available*")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        # Get all fiscal years with data
        all_years = sorted(set(list(annual.keys()) + list(quarterly.keys())), reverse=True)[:years]

        for fy in all_years:
            lines.append(f"### Fiscal Year {fy}")
            lines.append("")

            # Annual data
            fy_annual = annual.get(fy, {}).get('annual', {})
            if fy_annual.get('product'):
                total_product = sum(r for _, r in fy_annual['product'])
                lines.append("#### Annual Product Segments")
                lines.append("")
                lines.append("| Segment | Revenue | % |")
                lines.append("|---------|---------|---|")
                for name, rev in fy_annual['product'][:10]:  # Top 10
                    pct = (rev / total_product * 100) if total_product > 0 else 0
                    lines.append(f"| {name} | {fmt_revenue(rev)} | {pct:.1f}% |")
                lines.append(f"| **Total** | **{fmt_revenue(total_product)}** | |")
                lines.append("")

            # Quarterly data
            if include_quarterly and quarterly.get(fy):
                fy_quarterly = quarterly[fy]
                quarters = sorted([q for q in fy_quarterly.keys() if q.startswith('Q')],
                                  key=lambda x: int(x[1]) if x[1:].isdigit() else 0)

                if quarters:
                    lines.append("#### Quarterly Segments")
                    lines.append("")

                    # Build a table with quarters as columns
                    all_seg_names = set()
                    for q in quarters:
                        for name, _ in fy_quarterly[q].get('product', []):
                            all_seg_names.add(name)
                        for name, _ in fy_quarterly[q].get('geography', []):
                            all_seg_names.add(name)

                    if all_seg_names:
                        # Header
                        header = "| Segment | " + " | ".join(quarters) + " |"
                        sep = "|---------|" + "|".join(["------" for _ in quarters]) + "|"
                        lines.append(header)
                        lines.append(sep)

                        # Rows - sort by total revenue across quarters
                        seg_totals = {}
                        for name in all_seg_names:
                            total = 0
                            for q in quarters:
                                for n, r in fy_quarterly[q].get('product', []) + fy_quarterly[q].get('geography', []):
                                    if n == name:
                                        total += r
                            seg_totals[name] = total

                        sorted_segs = sorted(all_seg_names, key=lambda x: seg_totals.get(x, 0), reverse=True)[:8]

                        for name in sorted_segs:
                            row = f"| {name[:40]} |"
                            for q in quarters:
                                rev = 0
                                for n, r in fy_quarterly[q].get('product', []) + fy_quarterly[q].get('geography', []):
                                    if n == name:
                                        rev = r
                                        break
                                row += f" {fmt_revenue(rev) if rev > 0 else '-'} |"
                            lines.append(row)

                        lines.append("")

            lines.append("")

        lines.append("---")
        lines.append("")

    return '\n'.join(lines)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate concept stock segment revenue markdown report"
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
    parser.add_argument(
        "--include-quarterly",
        action="store_true",
        default=True,
        help="Include quarterly segment data from 10-Q filings"
    )
    parser.add_argument(
        "--no-quarterly",
        action="store_true",
        help="Skip quarterly segment data"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()
    include_quarterly = args.include_quarterly and not args.no_quarterly

    print("Generating concept stock segment revenue report...")
    print(f"  Years: {args.years}, Include quarterly: {include_quarterly}")

    # Load annual segment data from CSV
    csv_path = os.path.join(args.out_dir, "raw_conceptstock_company_revenue.csv")
    print(f"  Loading annual segment data from {csv_path}")
    annual_data = load_segment_data(csv_path, years=args.years)

    if not annual_data:
        print("  Warning: No annual segment data found. Run update_company_financials.py first.")
    else:
        print(f"  Loaded data for {len(annual_data)} companies")

    # Fetch quarterly segments from 10-Q
    quarterly_data = {}
    if include_quarterly:
        print(f"  Fetching quarterly segments from SEC 10-Q for: {', '.join(QUARTERLY_SUPPORTED)}")
        quarterly_data = fetch_sec_quarterly_segments(
            QUARTERLY_SUPPORTED,
            quarters=args.years * 4  # 4 quarters per year
        )

    # Generate markdown
    print("  Generating markdown...")
    markdown_content = generate_markdown(
        annual_data,
        quarterly_data,
        years=args.years,
        include_quarterly=include_quarterly
    )

    # Write output file
    output_path = os.path.join(args.out_dir, "raw_conceptstock_company_segments.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"  Wrote {output_path}")
    print("Done!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
