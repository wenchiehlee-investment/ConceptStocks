#!/usr/bin/env python3
"""
Alpha Vantage API Client for Income Statements

Provides income statement data for cross-checking against SEC EDGAR.
Free tier: 25 requests/day, so use sparingly.
"""

import json
import os
import re
import subprocess
import time
import urllib.request
from typing import Dict, List, Optional, Any
from datetime import datetime


def mask_api_key(url: str) -> str:
    """Mask API key in URL for safe storage."""
    return re.sub(r'apikey=[^&]+', 'apikey=***MASKED***', url, flags=re.IGNORECASE)


class AlphaVantageClient:
    """Client for Alpha Vantage API (income statements)."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        """
        Initialize Alpha Vantage client.

        Args:
            api_key: Alpha Vantage API key
        """
        self.api_key = api_key
        self._last_request_time = 0.0
        self._min_request_interval = 1.2  # Free tier rate limit

    def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _fetch_json(self, url: str) -> Dict:
        """Fetch JSON from Alpha Vantage API."""
        self._rate_limit()

        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Fallback to curl for SSL issues
            result = subprocess.check_output(["curl", "-sSL", url])
            return json.loads(result.decode("utf-8"))

    def get_income_statement(
        self, symbol: str, annual_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get income statement data for a company.

        Args:
            symbol: Stock ticker symbol
            annual_only: If True, return only annual reports

        Returns:
            List of income statement records
        """
        url = f"{self.BASE_URL}?function=INCOME_STATEMENT&symbol={symbol}&apikey={self.api_key}"

        data = self._fetch_json(url)

        # Check for errors
        if "Information" in data:
            raise RuntimeError(f"API limit reached: {data['Information']}")
        if "Error Message" in data:
            raise RuntimeError(f"API error: {data['Error Message']}")

        results = []

        # Collect reports based on mode
        report_sets = []
        if annual_only:
            report_sets.append(("FY", data.get("annualReports", [])))
        else:
            report_sets.append(("FY", data.get("annualReports", [])))
            report_sets.append(("Q", data.get("quarterlyReports", [])))

        for period_prefix, reports in report_sets:
            for report in reports:
                fiscal_date = report.get("fiscalDateEnding")

                # Extract metrics
                total_revenue = self._safe_float(report.get("totalRevenue"))
                gross_profit = self._safe_float(report.get("grossProfit"))
                operating_income = self._safe_float(report.get("operatingIncome"))
                net_income = self._safe_float(report.get("netIncome"))

                # Calculate margins
                gross_margin = None
                operating_margin = None
                net_margin = None

                if total_revenue and total_revenue > 0:
                    if gross_profit is not None:
                        gross_margin = gross_profit / total_revenue
                    if operating_income is not None:
                        operating_margin = operating_income / total_revenue
                    if net_income is not None:
                        net_margin = net_income / total_revenue

                # Determine period label
                period = "FY"
                if period_prefix == "Q" and fiscal_date:
                    # Derive quarter from reportedDate if available
                    month = int(fiscal_date[5:7])
                    # Map ending month to quarter (approximate)
                    quarter_map = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4",
                                   1: "Q1", 2: "Q1", 4: "Q2", 5: "Q2",
                                   7: "Q3", 8: "Q3", 10: "Q4", 11: "Q4"}
                    period = quarter_map.get(month, "Q4")

                results.append({
                    "symbol": symbol,
                    "fiscal_year": int(fiscal_date[:4]) if fiscal_date else None,
                    "period": period,
                    "end_date": fiscal_date,
                    "total_revenue": total_revenue,
                    "gross_profit": gross_profit,
                    "operating_income": operating_income,
                    "net_income": net_income,
                    "gross_margin": gross_margin,
                    "operating_margin": operating_margin,
                    "net_margin": net_margin,
                    "source": "AlphaVantage",
                    "source_url": mask_api_key(url),
                })

        return results

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == "None":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


def load_api_key() -> str:
    """Load API key from .env or environment."""
    # Try .env file first
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ALPHAVANTAGE_API_KEY="):
                    return line.split("=", 1)[1].strip()

    # Fall back to environment variable
    return os.environ.get("ALPHAVANTAGE_API_KEY", "")


# CLI for testing
if __name__ == "__main__":
    import sys

    api_key = load_api_key()
    if not api_key:
        print("Error: ALPHAVANTAGE_API_KEY not found in .env or environment")
        sys.exit(1)

    client = AlphaVantageClient(api_key)

    symbol = sys.argv[1] if len(sys.argv) > 1 else "MSFT"
    print(f"Fetching income statement for {symbol} from Alpha Vantage...")

    try:
        income = client.get_income_statement(symbol)
        print(f"\nIncome Statement ({len(income)} years):")
        for record in income[:5]:
            revenue = record.get('total_revenue')
            net_income = record.get('net_income')
            revenue_str = f"{revenue:,.0f}" if revenue else "N/A"
            net_income_str = f"{net_income:,.0f}" if net_income else "N/A"
            print(f"  FY{record.get('fiscal_year')}: Revenue={revenue_str}, Net Income={net_income_str}")
    except RuntimeError as e:
        print(f"Error: {e}")
