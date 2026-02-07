#!/usr/bin/env python3
"""
SEC EDGAR API Client

Fetches financial data from SEC EDGAR (free, official US SEC filings).
Supports both XBRL API and 10-K filing parsing for segment data.
No API key required, but User-Agent header is mandatory.

Rate limit: 10 requests/second
"""

import json
import re
import time
import urllib.request
from html.parser import HTMLParser
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


# Concept stock companies with their CIK numbers
COMPANY_CIK = {
    "NVDA": "0001045810",
    "GOOGL": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "MSFT": "0000789019",
    "AMD": "0000002488",
    "AAPL": "0000320193",
    "ORCL": "0001341439",
    "MU": "0000723125",
    "WDC": "0000106040",
    "QCOM": "0000804328",
    "DELL": "0001571996",
    "HPQ": "0000047217",
}

# Fiscal year end month for each company (used to calculate correct quarter from report date)
# Q1 ends 3 months after FY start, Q2 ends 6 months after, Q3 ends 9 months after
FISCAL_YEAR_END_MONTH = {
    "NVDA": 1,   # Jan - FY ends in January
    "DELL": 1,   # Jan
    "ORCL": 5,   # May
    "MSFT": 6,   # Jun
    "WDC": 6,    # Jun
    "MU": 8,     # Aug
    "AAPL": 9,   # Sep
    "QCOM": 9,   # Sep
    "HPQ": 10,   # Oct
    "GOOGL": 12, # Dec (calendar year)
    "AMZN": 12,  # Dec
    "META": 12,  # Dec
    "AMD": 12,   # Dec
}

# XBRL concepts for income statement metrics
INCOME_CONCEPTS = {
    "total_revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "eps": ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"],
}

# Default User-Agent (SEC requires identification)
DEFAULT_USER_AGENT = "ConceptStocks admin@example.com"


class TableParser(HTMLParser):
    """HTML parser to extract tables from SEC filings."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.current_table = []
        self.current_row = []
        self.current_cell = ""
        self.in_table = False
        self.in_row = False
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.current_table = []
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.current_row:
                self.current_table.append(self.current_row)
            self.current_row = []
        elif tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
            self.current_cell = ""

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def parse_money(text: str) -> Optional[float]:
    """Parse money value from text (handles $, commas, parentheses for negative)."""
    if not text:
        return None
    # Remove whitespace and common characters
    text = text.strip().replace(",", "").replace("$", "").replace(" ", "")
    # Handle parentheses for negative numbers
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    # Handle em-dash or hyphen for zero/missing
    if text in ("—", "-", "–", ""):
        return None
    try:
        value = float(text)
        return -value if negative else value
    except ValueError:
        return None


def get_fiscal_quarter_from_report_date(report_date: str, symbol: str) -> Tuple[int, str]:
    """
    Calculate fiscal year and quarter from a 10-Q report date.

    Args:
        report_date: Period end date in YYYY-MM-DD format (e.g., "2024-08-31")
        symbol: Stock ticker to look up fiscal year end month

    Returns:
        Tuple of (fiscal_year, quarter) e.g., (2025, "Q1")

    Example for Oracle (FY ends May):
        - Report date 2024-08-31 (Q1 ends Aug) -> FY2025 Q1
        - Report date 2024-11-30 (Q2 ends Nov) -> FY2025 Q2
        - Report date 2025-02-28 (Q3 ends Feb) -> FY2025 Q3
    """
    if not report_date or symbol not in FISCAL_YEAR_END_MONTH:
        return (0, "Q?")

    try:
        year, month, _ = map(int, report_date.split("-"))
    except (ValueError, AttributeError):
        return (0, "Q?")

    fy_end_month = FISCAL_YEAR_END_MONTH[symbol]

    # Calculate months after FY start
    # FY starts the month after FY end month of previous year
    # e.g., Oracle FY ends May (5), so FY starts June (6)
    fy_start_month = (fy_end_month % 12) + 1  # Month after FY end

    # Calculate how many months into the fiscal year the report date is
    if month >= fy_start_month:
        # Same calendar year as FY start
        months_into_fy = month - fy_start_month + 1
        fiscal_year = year + 1 if fy_end_month < 12 else year
    else:
        # Report month is in the year after FY start
        months_into_fy = (12 - fy_start_month + 1) + month
        fiscal_year = year if fy_end_month < 12 else year

    # Determine quarter from months into FY
    # Q1: months 1-3, Q2: months 4-6, Q3: months 7-9, Q4: months 10-12
    if months_into_fy <= 3:
        quarter = "Q1"
    elif months_into_fy <= 6:
        quarter = "Q2"
    elif months_into_fy <= 9:
        quarter = "Q3"
    else:
        quarter = "Q4"

    return (fiscal_year, quarter)


class SECEdgarClient:
    """Client for SEC EDGAR XBRL API."""

    BASE_URL = "https://data.sec.gov/api/xbrl"

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        """
        Initialize SEC EDGAR client.

        Args:
            user_agent: Required by SEC. Format: "Company/App contact@email.com"
        """
        self.user_agent = user_agent
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # 10 requests/second max

    def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _fetch_json(self, url: str) -> Dict:
        """Fetch JSON from SEC EDGAR API with proper headers."""
        self._rate_limit()

        request = urllib.request.Request(url)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}  # Company or concept not found
            raise RuntimeError(f"SEC EDGAR API error {e.code}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch from SEC EDGAR: {e}")

    def get_company_facts(self, cik: str) -> Dict:
        """
        Get all XBRL facts for a company.

        Args:
            cik: Company CIK number (with leading zeros)

        Returns:
            Dict with all company facts
        """
        # Ensure CIK has proper format (10 digits with leading zeros)
        cik = cik.zfill(10)
        url = f"{self.BASE_URL}/companyfacts/CIK{cik}.json"
        return self._fetch_json(url)

    def get_company_concept(self, cik: str, taxonomy: str, concept: str) -> Dict:
        """
        Get specific XBRL concept data for a company.

        Args:
            cik: Company CIK number
            taxonomy: XBRL taxonomy (e.g., "us-gaap", "dei")
            concept: Concept name (e.g., "Revenues")

        Returns:
            Dict with concept data
        """
        cik = cik.zfill(10)
        url = f"{self.BASE_URL}/companyconcept/CIK{cik}/{taxonomy}/{concept}.json"
        return self._fetch_json(url)

    def _extract_annual_data(self, units_data: Dict, use_max: bool = False) -> List[Dict]:
        """
        Extract annual (10-K) data from units response.

        Args:
            units_data: The 'units' section of a concept response
            use_max: If True, use maximum value per fiscal year (for revenue)

        Returns:
            List of annual data points
        """
        return self._extract_period_data(units_data, use_max=use_max, quarterly=False)

    def _extract_quarterly_data(self, units_data: Dict, use_max: bool = False) -> List[Dict]:
        """
        Extract quarterly (10-Q) data from units response.

        Returns:
            List of quarterly data points with 'period' field (Q1, Q2, Q3, Q4)
        """
        return self._extract_period_data(units_data, use_max=use_max, quarterly=True)

    def _extract_period_data(
        self, units_data: Dict, use_max: bool = False, quarterly: bool = False
    ) -> List[Dict]:
        """
        Extract annual or quarterly data from units response.

        Args:
            units_data: The 'units' section of a concept response
            use_max: If True, use maximum value per period (for revenue)
            quarterly: If True, extract 10-Q quarterly data; else 10-K annual

        Returns:
            List of data points
        """
        if quarterly:
            valid_forms = {"10-Q", "10-Q/A"}
            valid_fps = {"Q1", "Q2", "Q3", "Q4"}
        else:
            valid_forms = {"10-K", "10-K/A"}
            valid_fps = {"FY"}

        # Collect items by (fiscal_year, period) key
        by_key = {}

        for unit_type in ["USD", "USD/shares", "pure"]:
            if unit_type not in units_data:
                continue

            for item in units_data[unit_type]:
                form = item.get("form", "")
                if form not in valid_forms:
                    continue

                if "fy" not in item or "fp" not in item:
                    continue

                fp = item.get("fp")
                if fp not in valid_fps:
                    continue

                fy = item.get("fy")
                key = (fy, fp)
                if key not in by_key:
                    by_key[key] = []

                by_key[key].append({
                    "fiscal_year": fy,
                    "period": fp,
                    "start_date": item.get("start"),
                    "end_date": item.get("end"),
                    "value": item.get("val"),
                    "form": form,
                    "filed": item.get("filed"),
                    "accn": item.get("accn"),
                })

        # Select best item per key
        results = []
        for key, items in by_key.items():
            if quarterly:
                # For quarterly: prefer the shortest-duration item (standalone quarter)
                # over cumulative (YTD) values. Calculate duration from start/end dates.
                def _duration_days(it):
                    s, e = it.get("start_date", ""), it.get("end_date", "")
                    if s and e and len(s) >= 10 and len(e) >= 10:
                        try:
                            from datetime import datetime as _dt
                            d = (_dt.strptime(e[:10], "%Y-%m-%d") - _dt.strptime(s[:10], "%Y-%m-%d")).days
                            return d
                        except Exception:
                            pass
                    return 999  # Unknown duration, sort last

                # 1. Find shortest duration (standalone quarter, ~90 days)
                # 2. Among those, pick latest end_date (current period, not prior-year comparative)
                # 10-Q filings include comparative data from prior year with same fy/fp tags
                min_dur = min(_duration_days(x) for x in items)
                candidates = [x for x in items if _duration_days(x) == min_dur]
                best = max(candidates, key=lambda x: x.get("end_date") or "")
            elif use_max:
                best = max(items, key=lambda x: x.get("value") or 0)
            else:
                best = max(items, key=lambda x: x.get("filed") or "")
            results.append(best)

        # Sort by fiscal year + period descending
        period_order = {"FY": 5, "Q4": 4, "Q3": 3, "Q2": 2, "Q1": 1}
        results.sort(
            key=lambda x: (x.get("fiscal_year", 0), period_order.get(x.get("period", ""), 0)),
            reverse=True
        )

        return results

    def get_income_statement(
        self, symbol: str, years: int = 10, include_quarterly: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get income statement data for a company.

        Args:
            symbol: Stock ticker symbol
            years: Number of years of data to fetch
            include_quarterly: If True, also include quarterly (10-Q) data

        Returns:
            List of income statement records
        """
        if symbol not in COMPANY_CIK:
            raise ValueError(f"Unknown symbol: {symbol}. Add CIK to COMPANY_CIK.")

        cik = COMPANY_CIK[symbol]
        company_facts = self.get_company_facts(cik)

        if not company_facts:
            return []

        facts = company_facts.get("facts", {})
        us_gaap = facts.get("us-gaap", {})

        # Extract each income metric for annual + optional quarterly
        periods_to_fetch = ["annual"]
        if include_quarterly:
            periods_to_fetch.append("quarterly")

        all_results = []

        for period_type in periods_to_fetch:
            income_data = {}  # (fiscal_year, period) -> metrics dict

            for metric_name, concept_list in INCOME_CONCEPTS.items():
                for concept in concept_list:
                    if concept not in us_gaap:
                        continue

                    concept_data = us_gaap[concept]
                    units = concept_data.get("units", {})
                    use_max = metric_name == "total_revenue"

                    if period_type == "quarterly":
                        period_data = self._extract_quarterly_data(units, use_max=use_max)
                    else:
                        period_data = self._extract_annual_data(units, use_max=use_max)

                    for item in period_data:
                        fy = item.get("fiscal_year")
                        fp = item.get("period", "FY")
                        key = (fy, fp)
                        if key not in income_data:
                            income_data[key] = {
                                "fiscal_year": fy,
                                "period": fp,
                                "end_date": item.get("end_date"),
                                "filed": item.get("filed"),
                            }

                        if metric_name not in income_data[key]:
                            income_data[key][metric_name] = item.get("value")

            # Convert to list and calculate margins
            for key in sorted(income_data.keys(), reverse=True):
                fy, fp = key
                if fy < (max(k[0] for k in income_data.keys()) - years + 1):
                    continue

                record = income_data[key]

                total_revenue = record.get("total_revenue")
                gross_profit = record.get("gross_profit")
                operating_income = record.get("operating_income")
                net_income = record.get("net_income")

                if total_revenue and total_revenue > 0:
                    if gross_profit is not None:
                        record["gross_margin"] = gross_profit / total_revenue
                    if operating_income is not None:
                        record["operating_margin"] = operating_income / total_revenue
                    if net_income is not None:
                        record["net_margin"] = net_income / total_revenue

                record["symbol"] = symbol
                record["source"] = "SEC"
                all_results.append(record)

        return all_results

    def get_segment_revenue(
        self, symbol: str, years: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get segment revenue breakdown for a company.

        Note: Segment data varies significantly by company and may require
        company-specific parsing logic.

        Args:
            symbol: Stock ticker symbol
            years: Number of years of data to fetch

        Returns:
            List of segment revenue records
        """
        if symbol not in COMPANY_CIK:
            raise ValueError(f"Unknown symbol: {symbol}. Add CIK to COMPANY_CIK.")

        cik = COMPANY_CIK[symbol]
        company_facts = self.get_company_facts(cik)

        if not company_facts:
            return []

        facts = company_facts.get("facts", {})
        us_gaap = facts.get("us-gaap", {})

        # Look for segment-related concepts
        segment_concepts = [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ]

        results = []

        for concept in segment_concepts:
            if concept not in us_gaap:
                continue

            concept_data = us_gaap[concept]
            units = concept_data.get("units", {})

            if "USD" not in units:
                continue

            for item in units["USD"]:
                # Only 10-K filings
                form = item.get("form", "")
                if form not in ["10-K", "10-K/A"]:
                    continue

                # Check for segment dimension
                # Segments are indicated by presence of 'segment' key
                segment = item.get("segment")
                if not segment:
                    continue

                # Parse segment info
                # Format is like: "us-gaap:StatementBusinessSegmentsAxis=nvda:DataCenterMember"
                segment_name = None
                segment_type = "product"  # default

                if isinstance(segment, dict):
                    for axis, member in segment.items():
                        if "GeographyAxis" in axis or "Geographic" in axis:
                            segment_type = "geography"
                        # Extract readable segment name
                        segment_name = member.split(":")[-1].replace("Member", "")
                elif isinstance(segment, str):
                    segment_name = segment.split(":")[-1].replace("Member", "")

                if not segment_name:
                    continue

                results.append({
                    "symbol": symbol,
                    "fiscal_year": item.get("fy"),
                    "end_date": item.get("end"),
                    "segment_name": segment_name,
                    "segment_type": segment_type,
                    "revenue": item.get("val"),
                    "form": form,
                    "filed": item.get("filed"),
                    "source": "SEC",
                })

        # Remove duplicates and sort
        seen = set()
        unique_results = []
        for r in results:
            key = (r["symbol"], r["fiscal_year"], r["segment_name"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        unique_results.sort(
            key=lambda x: (x.get("fiscal_year", 0), x.get("segment_name", "")),
            reverse=True
        )

        return unique_results[:years * 10]  # Approximate limit

    def get_filing_list(self, cik: str, form_type: str = "10-K", count: int = 10) -> List[Dict]:
        """
        Get list of filings for a company.

        Args:
            cik: Company CIK number
            form_type: Type of filing (e.g., "10-K", "10-Q")
            count: Number of filings to retrieve

        Returns:
            List of filing metadata
        """
        cik = cik.zfill(10)
        # Use SEC's submissions API
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        data = self._fetch_json(url)

        if not data:
            return []

        filings = []
        recent = data.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])
        report_dates = recent.get("reportDate", [])  # Period end date

        for i, form in enumerate(forms):
            if form == form_type or form == f"{form_type}/A":
                if len(filings) >= count:
                    break
                filings.append({
                    "form": form,
                    "accession": accessions[i] if i < len(accessions) else None,
                    "date": dates[i] if i < len(dates) else None,
                    "primary_doc": primary_docs[i] if i < len(primary_docs) else None,
                    "report_date": report_dates[i] if i < len(report_dates) else None,
                    "cik": cik,
                })

        return filings

    def get_filing_document(self, cik: str, accession: str, document: str) -> str:
        """
        Download a specific filing document.

        Args:
            cik: Company CIK number
            accession: Accession number (e.g., "0001193125-24-123456")
            document: Document filename

        Returns:
            Document content as string
        """
        cik = cik.zfill(10)
        accession_clean = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{document}"

        self._rate_limit()

        request = urllib.request.Request(url)
        request.add_header("User-Agent", self.user_agent)

        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch filing document: {e}")

    def parse_segment_tables(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse segment revenue tables from 10-K HTML content.

        Args:
            html_content: HTML content of the filing

        Returns:
            List of segment revenue records
        """
        parser = TableParser()
        try:
            parser.feed(html_content)
        except Exception:
            return []

        results = []
        table_counter = 0

        for table in parser.tables:
            if len(table) < 4:
                continue

            # Join table text for pattern matching
            table_text = " ".join(" ".join(str(c) for c in row) for row in table[:12])

            # Look for revenue tables with:
            # 1. Revenue-related patterns
            # 2. Large numbers (indicating billions in millions format like 44,029)
            revenue_patterns = [
                "Revenues:", "Total revenues", "Total revenue",
                "Revenue by end market", "Revenue by geography",
                "Net revenue", "Revenue, net"
            ]
            has_revenue_header = any(p in table_text for p in revenue_patterns)
            has_large_numbers = bool(re.search(r'\d{1,2},\d{3}', table_text))

            if not (has_revenue_header and has_large_numbers):
                continue

            # Find header row with years
            header_row_idx = None
            year_positions = []  # List of (column_index, year)

            for i, row in enumerate(table[:5]):
                years_in_row = []
                for j, cell in enumerate(row):
                    cell_str = str(cell).strip()
                    year_match = re.search(r'20[12][0-9]', cell_str)
                    if year_match:
                        years_in_row.append((j, int(year_match.group())))

                if len(years_in_row) >= 1:  # Need at least 1 year
                    header_row_idx = i
                    year_positions = years_in_row
                    break

            if header_row_idx is None:
                continue

            # Check if this table has "(in millions)" indicator
            is_millions = "(in millions" in table_text.lower() or "(dollars in millions" in table_text.lower()

            # Parse data rows
            for row in table[header_row_idx + 1:]:
                if len(row) < 2:
                    continue

                # Extract segment name (first text cell)
                segment_name = ""
                name_col_idx = 0
                for idx, cell in enumerate(row):
                    cell_text = str(cell).strip()
                    # Skip empty, $, numbers, and parenthetical notes
                    if (cell_text and
                        cell_text != "$" and
                        not cell_text.replace(",", "").replace(".", "").replace("-", "").replace("(", "").replace(")", "").isdigit() and
                        not cell_text.startswith("(") and
                        len(cell_text) > 1):
                        segment_name = cell_text.rstrip(":")
                        name_col_idx = idx
                        break

                if not segment_name or len(segment_name) > 80:
                    continue

                # Skip non-revenue rows
                skip_patterns = [
                    "total", "subtotal", "elimination", "operating expense",
                    "margin", "percent", "(in millions)", "(dollars",
                    "expenses", "cost", "income", "loss", "depreciation",
                    "amortization", "restructur", "research and development",
                    "sales and marketing", "general and administrative",
                    "selling", "interest", "stock-based", "provision",
                    "diluted", "basic", "earnings", "profit", "revenue, net",
                    "net revenue", "exabytes", "impairment", "compensation",
                    "weighted", "shares outstanding", "litigation",
                    "realignment", "charges", "acquisition",
                    "tax", "dividend", "other",
                ]
                if any(skip in segment_name.lower() for skip in skip_patterns):
                    continue

                # Extract values for each year
                for year_col, year in year_positions:
                    # Find numeric value after the segment name
                    # Values often have "$" in a separate cell
                    value = None

                    # Search in cells after name_col_idx, near year_col position
                    search_start = max(name_col_idx + 1, year_col - 2)
                    search_end = min(len(row), year_col + 3)

                    for idx in range(search_start, search_end):
                        if idx >= len(row):
                            break
                        cell_val = str(row[idx]).strip()
                        if cell_val == "$":
                            continue
                        parsed = parse_money(cell_val)
                        if parsed is not None and parsed > 100:  # At least 100 (million)
                            value = parsed
                            break

                    if value is not None:
                        # Convert to actual value (multiply by 1M if in millions)
                        if is_millions:
                            value = value * 1_000_000

                        # Clean footnote markers like (1), (2) from name
                        clean_name = re.sub(r'\(\d+\)$', '', segment_name).strip()

                        results.append({
                            "segment_name": clean_name,
                            "fiscal_year": year,
                            "revenue": value,
                            "source": "SEC_10K",
                            "table_index": table_counter,
                        })

            table_counter += 1

        # Also parse horizontal format tables (segments as columns)
        # Pattern: "For the year ended YYYY" with segment columns
        for table in parser.tables:
            if len(table) < 4:
                continue

            table_text = " ".join(" ".join(str(c) for c in row) for row in table[:5])

            # Look for horizontal segment table pattern
            year_match = re.search(r'(?:year ended|fiscal)\s*(\d{4})', table_text.lower())
            if not year_match:
                continue

            year = int(year_match.group(1))

            # Find the header row with segment names (might not be row 0)
            header_row = None
            header_row_idx = -1
            for i, row in enumerate(table[:5]):
                non_empty = [str(c).strip() for c in row if str(c).strip()]
                # Header should have multiple items and include segment-like names
                if len(non_empty) >= 3:
                    header_row = row
                    header_row_idx = i
                    break

            if header_row is None:
                continue

            # Find segment columns (skip year/total columns)
            segment_cols = []
            for idx, cell in enumerate(header_row):
                cell_text = str(cell).strip()
                if cell_text and cell_text not in ["", "Total", "Unallocated", "All Other"]:
                    # Check if it looks like a segment name (not a year or label)
                    if not re.match(r'^(for|year|fiscal|\d{4}|in millions)', cell_text.lower()):
                        segment_cols.append((idx, cell_text))

            if len(segment_cols) < 2:
                continue

            # Find revenue row (after header)
            for row in table[header_row_idx + 1:]:
                row_text = " ".join(str(c) for c in row).lower()
                if "revenue" in row_text and "cost" not in row_text and "deferred" not in row_text:
                    # Extract ALL numeric values from this row in order
                    numeric_values = []
                    for cell in row:
                        cell_val = str(cell).strip()
                        if cell_val in ("$", "", "Revenue", "Net revenue"):
                            continue
                        parsed = parse_money(cell_val)
                        if parsed is not None and abs(parsed) > 1:
                            numeric_values.append(parsed)

                    # Map values positionally to segments
                    for i, (col_idx, segment_name) in enumerate(segment_cols):
                        if i < len(numeric_values):
                            value = numeric_values[i] * 1_000_000  # Convert millions
                            if value > 0:
                                clean_name = re.sub(r'\(\d+\)$', '', segment_name).strip()
                                results.append({
                                    "segment_name": clean_name,
                                    "fiscal_year": year,
                                    "revenue": value,
                                    "source": "SEC_10K",
                                    "table_index": table_counter,
                                })
                    break  # Found revenue row, move to next table

        # For each fiscal year, only keep segments from the first table
        # (the first table is usually the high-level revenue breakdown)
        # Group by fiscal year to find the first table_index per year
        first_table_by_year = {}
        for r in results:
            fy = r["fiscal_year"]
            ti = r.get("table_index", 0)
            if fy not in first_table_by_year or ti < first_table_by_year[fy]:
                first_table_by_year[fy] = ti

        # Keep only results from the first table per fiscal year
        filtered = [
            r for r in results
            if r.get("table_index", 0) == first_table_by_year.get(r["fiscal_year"], 0)
        ]

        # Deduplicate - keep highest value for same segment/year
        best_results = {}
        for r in filtered:
            key = (r["segment_name"], r["fiscal_year"])
            if key not in best_results or r["revenue"] > best_results[key]["revenue"]:
                best_results[key] = r

        return list(best_results.values())

    def get_segment_revenue_from_10k(
        self, symbol: str, years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get segment revenue by parsing 10-K filings directly.

        This is a fallback for companies where XBRL segment data is not available.

        Args:
            symbol: Stock ticker symbol
            years: Number of years to look back

        Returns:
            List of segment revenue records
        """
        if symbol not in COMPANY_CIK:
            raise ValueError(f"Unknown symbol: {symbol}. Add CIK to COMPANY_CIK.")

        cik = COMPANY_CIK[symbol]

        # Get recent 10-K filings
        filings = self.get_filing_list(cik, "10-K", count=years)

        if not filings:
            return []

        results = []

        for filing in filings:
            accession = filing.get("accession")
            primary_doc = filing.get("primary_doc")
            filing_date = filing.get("date")

            if not accession or not primary_doc:
                continue

            try:
                print(f"    Parsing 10-K filed {filing_date}...")
                content = self.get_filing_document(cik, accession, primary_doc)
                segments = self.parse_segment_tables(content)

                geo_keywords = [
                    "america", "europe", "asia", "china", "japan",
                    "international", "emea", "united states", "hong kong",
                    "rest of", "middle east", "africa", "apac", "pacific",
                    "singapore", "taiwan", "korea", "india", "uk",
                    "united kingdom", "germany", "canada",
                ]
                for seg in segments:
                    seg["symbol"] = symbol
                    seg["end_date"] = filing_date
                    seg["segment_type"] = "product"  # Default
                    if any(geo in seg["segment_name"].lower() for geo in geo_keywords):
                        seg["segment_type"] = "geography"

                results.extend(segments)

            except Exception as e:
                print(f"    Warning: Could not parse filing {accession}: {e}")
                continue

        # Remove duplicates
        seen = set()
        unique_results = []
        for r in results:
            key = (r["symbol"], r["fiscal_year"], r["segment_name"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results

    def get_segment_revenue_from_10q(
        self, symbol: str, quarters: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get segment revenue by parsing 10-Q filings directly.

        Args:
            symbol: Stock ticker symbol
            quarters: Number of quarters to look back (default 20 = 5 years)

        Returns:
            List of segment revenue records with period field (Q1, Q2, Q3)
        """
        if symbol not in COMPANY_CIK:
            raise ValueError(f"Unknown symbol: {symbol}. Add CIK to COMPANY_CIK.")

        cik = COMPANY_CIK[symbol]

        # Get recent 10-Q filings
        filings = self.get_filing_list(cik, "10-Q", count=quarters)

        if not filings:
            return []

        results = []

        for filing in filings:
            accession = filing.get("accession")
            primary_doc = filing.get("primary_doc")
            filing_date = filing.get("date")

            if not accession or not primary_doc:
                continue

            try:
                print(f"    Parsing 10-Q filed {filing_date}...")
                content = self.get_filing_document(cik, accession, primary_doc)
                segments = self.parse_segment_tables(content)

                # IMPORTANT: 10-Q tables contain BOTH current year AND prior year
                # comparative data. We only want the CURRENT year (max fiscal_year).
                # Filter to keep only the maximum fiscal year from this filing.
                if segments:
                    max_fy = max(seg.get("fiscal_year", 0) for seg in segments)
                    segments = [seg for seg in segments if seg.get("fiscal_year") == max_fy]

                geo_keywords = [
                    "america", "europe", "asia", "china", "japan",
                    "international", "emea", "united states", "hong kong",
                    "rest of", "middle east", "africa", "apac", "pacific",
                    "singapore", "taiwan", "korea", "india", "uk",
                    "united kingdom", "germany", "canada",
                ]

                # Determine quarter from report_date (period end date)
                # This correctly handles non-calendar fiscal years (e.g., Oracle ends May)
                report_date = filing.get("report_date")
                fiscal_year, period = get_fiscal_quarter_from_report_date(report_date, symbol)

                for seg in segments:
                    seg["symbol"] = symbol
                    seg["end_date"] = report_date or filing_date  # Prefer report_date
                    seg["period"] = period
                    # Override fiscal_year if we calculated it from report_date
                    if fiscal_year > 0:
                        seg["fiscal_year"] = fiscal_year
                    seg["segment_type"] = "product"  # Default
                    if any(geo in seg["segment_name"].lower() for geo in geo_keywords):
                        seg["segment_type"] = "geography"

                results.extend(segments)

            except Exception as e:
                print(f"    Warning: Could not parse filing {accession}: {e}")
                continue

        # Remove duplicates (key includes period now)
        seen = set()
        unique_results = []
        for r in results:
            key = (r["symbol"], r["fiscal_year"], r.get("period", ""), r["segment_name"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results


    def get_segment_revenue_from_8k(
        self, symbol: str, quarters: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get quarterly segment revenue from 8-K earnings press releases.

        This is useful for companies like NVDA that don't have segment tables
        in their 10-Q filings but do report segments in earnings press releases.

        Args:
            symbol: Stock ticker symbol
            quarters: Number of quarters to look back

        Returns:
            List of segment revenue records with period field (Q1, Q2, Q3, Q4)
        """
        if symbol not in COMPANY_CIK:
            raise ValueError(f"Unknown symbol: {symbol}. Add CIK to COMPANY_CIK.")

        cik = COMPANY_CIK[symbol]

        # Get recent 8-K filings
        filings = self.get_filing_list(cik, "8-K", count=quarters * 2)

        if not filings:
            return []

        results = []

        for filing in filings:
            accession = filing.get("accession")
            filing_date = filing.get("date")

            if not accession:
                continue

            try:
                # Find press release exhibit (usually 99.1)
                pr_doc = self._find_press_release(cik, accession, symbol)
                if not pr_doc:
                    continue

                print(f"    Parsing 8-K press release filed {filing_date}...")
                content = self.get_filing_document(cik, accession, pr_doc)

                # Parse segments from press release
                segments = self._parse_8k_segments(content, symbol)

                for seg in segments:
                    seg["symbol"] = symbol
                    seg["end_date"] = filing_date
                    seg["source"] = "SEC_8K"

                if segments:
                    print(f"      Found {len(segments)} segments")
                    results.extend(segments)

            except Exception as e:
                print(f"    Warning: Could not parse 8-K {accession}: {e}")
                continue

        # Remove duplicates
        seen = set()
        unique_results = []
        for r in results:
            key = (r["symbol"], r["fiscal_year"], r.get("period", ""), r["segment_name"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results

    def _find_press_release(self, cik: str, accession: str, symbol: str) -> Optional[str]:
        """Find the press release document in an 8-K filing."""
        # Common press release naming patterns (prioritized)
        patterns = [
            r"q\dfy\d{2}pr",      # NVDA style: q2fy26pr.htm
            r"ex99[-_]?1",        # ex99-1.htm, ex991.htm, ex99_1.htm
            r"exhibit99[-_]?1",
            r"pressrelease",
            r"earnings",
            r"press.*release",
        ]

        try:
            # Fetch the filing index page
            cik_clean = cik.lstrip("0")
            acc_clean = accession.replace("-", "")
            index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/{accession}-index.htm"

            req = urllib.request.Request(index_url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")

            # Find links to potential press release files
            # Links can be full paths like /Archives/edgar/data/.../file.htm
            link_pattern = re.compile(r'href="([^"]*\.htm)"', re.IGNORECASE)
            candidates = []

            for match in link_pattern.finditer(content):
                href = match.group(1)
                # Skip index and navigation links
                if href in ("/index.htm", "index.htm") or "ix?doc=" in href:
                    continue
                filename = href.split("/")[-1].lower()
                candidates.append(filename)

            # Try each pattern in priority order
            for pattern in patterns:
                for filename in candidates:
                    if re.search(pattern, filename):
                        return filename

        except Exception as e:
            print(f"      _find_press_release error: {e}")

        return None

    def _strip_html(self, content: str) -> str:
        """Strip HTML tags and normalize whitespace for easier regex matching."""
        import html as html_module
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', content)
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean)
        # Unescape HTML entities
        clean = html_module.unescape(clean)
        return clean

    def _parse_8k_segments(self, content: str, symbol: str) -> List[Dict[str, Any]]:
        """
        Parse segment revenue from 8-K press release content.

        Different companies have different formats, so we use company-specific parsers.
        """
        # Strip HTML for cleaner parsing
        clean_content = self._strip_html(content)

        if symbol == "NVDA":
            return self._parse_nvda_8k(clean_content)
        elif symbol == "GOOGL":
            return self._parse_googl_8k(clean_content)
        elif symbol == "MSFT":
            return self._parse_msft_8k(clean_content)
        elif symbol == "AMZN":
            return self._parse_amzn_8k(clean_content)
        elif symbol == "META":
            return self._parse_meta_8k(clean_content)
        elif symbol == "AAPL":
            return self._parse_aapl_8k(clean_content)
        elif symbol == "MU":
            return self._parse_mu_8k(clean_content)
        else:
            return []

    def _parse_nvda_8k(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse NVIDIA 8-K press release for segment revenue.

        NVDA format example:
        "Data Center revenue of $41.1 billion, up 5% from Q1 and up 56% from a year ago"
        """
        results = []

        # Extract fiscal year and quarter from content
        # Pattern: "NVIDIA Announces Financial Results for Second Quarter Fiscal 2026"
        fy_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter\s+(?:of\s+)?Fiscal\s+(\d{4})',
            content, re.IGNORECASE
        )
        if not fy_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
        quarter = quarter_map.get(fy_match.group(1).lower(), "Q?")
        fiscal_year = int(fy_match.group(2))

        # NVDA segment names to look for
        nvda_segments = [
            "Data Center",
            "Gaming",
            "Gaming and AI PC",
            "Professional Visualization",
            "Automotive",
            "Automotive and Robotics",
            "OEM and Other",
        ]

        # Pattern variations:
        # FY2025+: "Data Center revenue of $41.1 billion" or "Gaming revenue was $4.3 billion"
        # FY2024:  "Gaming — Third-quarter revenue was $2.86 billion"
        for seg_name in nvda_segments:
            seg_pattern = re.escape(seg_name)
            # Try multiple patterns
            patterns = [
                # Direct: "Gaming revenue of/was $X billion"
                seg_pattern + r'\s+revenue\s+(?:of|was)\s+\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million)',
                # With quarter prefix: "Gaming — Third-quarter revenue was $X billion"
                seg_pattern + r'[^.]*?(?:quarter|Q\d)\s+revenue\s+(?:of|was)\s+\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million)',
            ]

            match = None
            for p in patterns:
                match = re.search(p, content, re.IGNORECASE)
                if match:
                    break

            if match:
                amount = float(match.group(1).replace(",", ""))
                unit = match.group(2).lower()

                if unit == "billion":
                    revenue = amount * 1_000_000_000
                else:
                    revenue = amount * 1_000_000

                results.append({
                    "segment_name": seg_name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results

    def _parse_googl_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Google/Alphabet 8-K press release for segment revenue.

        Format: "Google Services revenues increased 14% to $95.9 billion"
        or "Google Cloud ... revenues increased 48% to $17.7 billion"
        """
        results = []

        # Extract quarter and year
        # Pattern: "Fourth Quarter 2025" or "Three Months Ended December 31, 2025"
        fy_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter\s+(\d{4})',
            content, re.IGNORECASE
        )
        if not fy_match:
            # Try "Three Months Ended" format
            month_match = re.search(
                r'Three\s+Months\s+Ended\s+(March|June|September|December)\s+\d{1,2},?\s+(\d{4})',
                content, re.IGNORECASE
            )
            if month_match:
                month_to_quarter = {"march": "Q1", "june": "Q2", "september": "Q3", "december": "Q4"}
                quarter = month_to_quarter.get(month_match.group(1).lower(), "Q4")
                fiscal_year = int(month_match.group(2))
            else:
                return []
        else:
            quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
            quarter = quarter_map.get(fy_match.group(1).lower(), "Q?")
            fiscal_year = int(fy_match.group(2))

        # Google segments - actual format from press releases:
        # "Google Services revenues increased 14% to $95.9 billion"
        # "Google Cloud revenues increased 34% to $15.2 billion"
        # "Google Cloud saw ... revenues increased 48% to $17.7 billion"
        # Note: Be careful not to match across sentences - use [^.]* instead of .*
        segment_patterns = [
            (r'Google\s+Services\s+revenues\s+(?:increased|decreased|grew)[^.]*?to\s+\$([\d.]+)\s*billion', "Google Services"),
            # Google Cloud - two formats: direct "revenues increased" or with descriptive text
            (r'Google\s+Cloud\s+revenues\s+(?:increased|decreased|grew)[^.]*?to\s+\$([\d.]+)\s*billion', "Google Cloud"),
            (r'Google\s+Cloud\s+(?:saw|had|achieved|reported|posted)[^.]*?revenues\s+(?:increased|decreased|grew)[^.]*?to\s+\$([\d.]+)\s*billion', "Google Cloud"),
        ]

        seen_segments = set()
        for pattern, name in segment_patterns:
            if name in seen_segments:
                continue
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                revenue = float(match.group(1)) * 1_000_000_000
                seen_segments.add(name)

                results.append({
                    "segment_name": name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results

    def _parse_msft_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Microsoft 8-K press release for segment revenue.

        Format: "Revenue in Productivity and Business Processes was $34.1 billion"
        """
        results = []

        # Extract quarter - multiple formats
        # "Second Quarter Fiscal Year 2026" or "Second Quarter Results" + separate year
        quarter_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter',
            content, re.IGNORECASE
        )
        if not quarter_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
        quarter = quarter_map.get(quarter_match.group(1).lower(), "Q?")

        # Extract fiscal year - look for "Fiscal Year 2026" or "fiscal year" + date context
        fy_match = re.search(r'Fiscal\s+(?:Year\s+)?(\d{4})', content, re.IGNORECASE)
        if fy_match:
            fiscal_year = int(fy_match.group(1))
        else:
            # Try to extract from date like "December 31, 2025" (end of fiscal Q2)
            # MSFT fiscal year ends in June, so Dec 2025 = FY2026 Q2
            date_match = re.search(r'(?:quarter\s+ended|December|March|September|June)\s+\d{1,2},?\s+(\d{4})', content, re.IGNORECASE)
            if date_match:
                year = int(date_match.group(1))
                # MSFT fiscal year: Jul-Jun. Dec=Q2, Mar=Q3, Jun=Q4, Sep=Q1
                if 'december' in content.lower()[:500]:
                    fiscal_year = year + 1  # Dec 2025 = FY2026
                elif 'march' in content.lower()[:500]:
                    fiscal_year = year  # Mar 2026 = FY2026
                elif 'june' in content.lower()[:500]:
                    fiscal_year = year  # Jun 2026 = FY2026
                else:  # September
                    fiscal_year = year + 1  # Sep 2025 = FY2026
            else:
                return []

        # Microsoft segments - HTML is now stripped, so patterns are simpler
        # Format: "Revenue in Productivity and Business Processes was $34.1 billion"
        segment_patterns = [
            (r'Revenue\s+in\s+Productivity\s+and\s+Business\s+Processes\s+was\s+\$([\d.]+)\s*billion', "Productivity and Business Processes"),
            (r'Revenue\s+in\s+Intelligent\s+Cloud\s+was\s+\$([\d.]+)\s*billion', "Intelligent Cloud"),
            (r'Revenue\s+in\s+More\s+Personal\s+Computing\s+was\s+\$([\d.]+)\s*billion', "More Personal Computing"),
        ]

        for pattern, name in segment_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                revenue = float(match.group(1)) * 1_000_000_000

                results.append({
                    "segment_name": name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results

    def _parse_amzn_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Amazon 8-K press release for segment revenue.

        Format: "North America segment sales increased 10% year-over-year to $127.1 billion"
        """
        results = []

        # Extract quarter and year - "Fourth Quarter 2025"
        fy_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter\s+(\d{4})',
            content, re.IGNORECASE
        )
        if not fy_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
        quarter = quarter_map.get(fy_match.group(1).lower(), "Q?")
        fiscal_year = int(fy_match.group(2))

        # Amazon segments - actual format:
        # "North America segment sales increased 10% year-over-year to $127.1 billion"
        # "AWS segment sales increased 24% year-over-year to $35.6 billion"
        segment_patterns = [
            (r'North\s+America\s+segment\s+sales\s+(?:increased|decreased).*?to\s+\$([\d.]+)\s*billion', "North America"),
            (r'International\s+segment\s+sales\s+(?:increased|decreased).*?to\s+\$([\d.]+)\s*billion', "International"),
            (r'AWS\s+segment\s+sales\s+(?:increased|decreased).*?to\s+\$([\d.]+)\s*billion', "AWS"),
        ]

        for pattern, name in segment_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                revenue = float(match.group(1)) * 1_000_000_000

                results.append({
                    "segment_name": name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results

    def _parse_meta_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Meta 8-K press release for segment revenue.

        Meta uses table format with values in millions:
        "Family of Apps 58,938 48,013"
        "Reality Labs 955 372"
        """
        results = []

        # Extract quarter and year
        fy_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter\s+(\d{4})',
            content, re.IGNORECASE
        )
        if not fy_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
        quarter = quarter_map.get(fy_match.group(1).lower(), "Q?")
        fiscal_year = int(fy_match.group(2))

        # Meta segments - table format in millions
        # Pattern: "Family of Apps 58,938 48,013" (current, prior year)
        segment_patterns = [
            (r'Family\s+of\s+Apps\s+([0-9,]+)\s', "Family of Apps"),
            (r'Reality\s+Labs\s+([0-9,]+)\s', "Reality Labs"),
        ]

        for pattern, name in segment_patterns:
            match = re.search(pattern, content)
            if match:
                # Values are in millions
                revenue = float(match.group(1).replace(",", "")) * 1_000_000

                results.append({
                    "segment_name": name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results

    def _parse_aapl_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Apple 8-K press release for segment revenue.

        Apple 8-K uses table format with values in millions:
        "iPhone 46,222 50,231"
        "Mac 8,386 8,987"
        "Services 30,013 26,340"

        Note: Apple only reports Products (total) and Services in 8-K.
        Individual products (iPhone, Mac, iPad) are in 10-Q XBRL.
        """
        results = []

        # Extract quarter and year - multiple Apple formats:
        # "fiscal 2026 first quarter" or "Q1 FY26"
        fy_match = re.search(
            r'(?:Q([1-4])\s*FY\s*(\d{2,4})|'
            r'fiscal\s+(\d{4})\s+(first|second|third|fourth)\s+quarter|'
            r'(first|second|third|fourth)\s+(?:fiscal\s+)?quarter.*?fiscal\s+(\d{4}))',
            content, re.IGNORECASE
        )
        if not fy_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}

        if fy_match.group(1):  # Q1 FY25 format
            quarter = f"Q{fy_match.group(1)}"
            fy = fy_match.group(2)
            fiscal_year = int(fy) if len(fy) == 4 else 2000 + int(fy)
        elif fy_match.group(3):  # "fiscal 2026 first quarter" format
            fiscal_year = int(fy_match.group(3))
            quarter = quarter_map.get(fy_match.group(4).lower(), "Q?")
        else:  # "first quarter of fiscal 2025" format
            quarter = quarter_map.get(fy_match.group(5).lower(), "Q?")
            fiscal_year = int(fy_match.group(6))

        # Apple 8-K table format - values in MILLIONS
        # Pattern: "iPhone 46,222 50,231" (current quarter, prior year)
        # Or: "Services 30,013 26,340"
        segment_patterns = [
            (r'iPhone\s+([\d,]+)\s', "iPhone"),
            (r'\bMac\s+([\d,]+)\s', "Mac"),
            (r'iPad\s+([\d,]+)\s', "iPad"),
            (r'Wearables,?\s*Home\s+and\s+Accessories\s+([\d,]+)\s', "Wearables, Home and Accessories"),
            (r'Services\s+([\d,]+)\s', "Services"),
        ]

        for pattern, name in segment_patterns:
            match = re.search(pattern, content)
            if match:
                # Values are in millions
                revenue = float(match.group(1).replace(",", "")) * 1_000_000

                # Sanity check: Apple segments should be at least $1B
                if revenue >= 1_000_000_000:
                    results.append({
                        "segment_name": name,
                        "fiscal_year": fiscal_year,
                        "period": quarter,
                        "revenue": revenue,
                        "segment_type": "product",
                    })

        return results

    def _parse_mu_8k(self, content: str) -> List[Dict[str, Any]]:
        """Parse Micron 8-K press release for segment revenue.

        Micron reports by Business Unit in table format (values in millions):
        "Cloud Memory Business Unit Revenue $ 5,284"
        "Mobile and Client Business Unit Revenue $ 4,255"
        """
        results = []

        # Extract quarter and year
        fy_match = re.search(
            r'(First|Second|Third|Fourth)\s+Quarter\s+(?:of\s+)?Fiscal\s+(\d{4})',
            content, re.IGNORECASE
        )
        if not fy_match:
            return []

        quarter_map = {"first": "Q1", "second": "Q2", "third": "Q3", "fourth": "Q4"}
        quarter = quarter_map.get(fy_match.group(1).lower(), "Q?")
        fiscal_year = int(fy_match.group(2))

        # Micron Business Units - current segment names (as of FY2026)
        # Format: "Cloud Memory Business Unit Revenue $ 5,284"
        segment_patterns = [
            (r'Cloud\s+Memory\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Cloud Memory"),
            (r'Core\s+Data\s+Center\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Core Data Center"),
            (r'Mobile\s+and\s+Client\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Mobile and Client"),
            (r'Automotive\s+and\s+Embedded\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Automotive and Embedded"),
            # Legacy segment names (pre-FY2025)
            (r'Compute\s+and\s+Networking\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Compute and Networking"),
            (r'Storage\s+Business\s+Unit\s+Revenue[^0-9]{0,10}([0-9,]+)', "Storage"),
        ]

        for pattern, name in segment_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Values are in millions
                revenue = float(match.group(1).replace(",", "")) * 1_000_000

                results.append({
                    "segment_name": name,
                    "fiscal_year": fiscal_year,
                    "period": quarter,
                    "revenue": revenue,
                    "segment_type": "product",
                })

        return results


def mask_url(url: str) -> str:
    """Mask URL for safe storage (SEC EDGAR doesn't use API keys, but for consistency)."""
    return url


# CLI for testing
if __name__ == "__main__":
    import sys

    client = SECEdgarClient()

    symbol = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    print(f"Fetching income statement for {symbol}...")

    income = client.get_income_statement(symbol, years=5)
    print(f"\nIncome Statement ({len(income)} years):")
    for record in income:
        revenue = record.get('total_revenue')
        net_income = record.get('net_income')
        revenue_str = f"{revenue:,}" if revenue else "N/A"
        net_income_str = f"{net_income:,}" if net_income else "N/A"
        print(f"  FY{record.get('fiscal_year')}: Revenue={revenue_str}, Net Income={net_income_str}")

    print(f"\nFetching segment revenue for {symbol}...")
    segments = client.get_segment_revenue(symbol, years=3)
    print(f"\nSegment Revenue ({len(segments)} records):")
    for record in segments[:10]:
        revenue = record.get('revenue')
        revenue_str = f"{revenue:,}" if revenue else "N/A"
        print(f"  FY{record.get('fiscal_year')} {record.get('segment_name')}: {revenue_str}")
