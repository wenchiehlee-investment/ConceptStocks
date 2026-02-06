#!/usr/bin/env python3
"""
Financial Modeling Prep (FMP) API Client

Provides segment revenue and income statement data for cross-checking.
Free tier: 250 requests/day, 5-year history.
"""

import json
import os
import re
import time
import urllib.request
from typing import Dict, List, Optional, Any
from datetime import datetime


def mask_api_key(url: str) -> str:
    """Mask API key in URL for safe storage."""
    return re.sub(r'apikey=[^&]+', 'apikey=***MASKED***', url, flags=re.IGNORECASE)


class FMPClient:
    """Client for Financial Modeling Prep API."""

    BASE_URL = "https://financialmodelingprep.com"

    def __init__(self, api_key: str):
        """
        Initialize FMP client.

        Args:
            api_key: FMP API key
        """
        self.api_key = api_key
        self._last_request_time = 0.0
        self._min_request_interval = 0.5  # Be conservative with rate limits

    def _rate_limit(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _fetch_json(self, url: str) -> Any:
        """Fetch JSON from FMP API."""
        self._rate_limit()

        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise RuntimeError("Invalid FMP API key")
            if e.code == 403:
                raise RuntimeError("FMP API access denied (check subscription)")
            raise RuntimeError(f"FMP API error {e.code}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch from FMP: {e}")

    def get_revenue_segments(
        self, symbol: str, period: str = "annual"
    ) -> List[Dict[str, Any]]:
        """
        Get product segment revenue breakdown.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"

        Returns:
            List of segment revenue records
        """
        # Use stable API endpoint
        url = f"{self.BASE_URL}/stable/revenue-product-segmentation?symbol={symbol}&period={period}&apikey={self.api_key}"

        data = self._fetch_json(url)

        if not data or not isinstance(data, list):
            return []

        results = []
        for item in data:
            # New stable API format: {symbol, fiscalYear, period, date, data: {segment: value}}
            fiscal_year = item.get("fiscalYear")
            date = item.get("date")
            segments = item.get("data", {})

            if isinstance(segments, dict):
                for segment_name, revenue in segments.items():
                    results.append({
                        "symbol": symbol,
                        "date": date,
                        "fiscal_year": fiscal_year,
                        "period": period,
                        "segment_name": segment_name,
                        "segment_type": "product",
                        "revenue": self._safe_float(revenue),
                        "source": "FMP",
                        "source_url": mask_api_key(url),
                    })

        return results

    def get_geographic_segments(
        self, symbol: str, period: str = "annual"
    ) -> List[Dict[str, Any]]:
        """
        Get geographic segment revenue breakdown.

        Args:
            symbol: Stock ticker symbol
            period: "annual" or "quarter"

        Returns:
            List of geographic segment revenue records
        """
        # Use stable API endpoint
        url = f"{self.BASE_URL}/stable/revenue-geographic-segmentation?symbol={symbol}&period={period}&apikey={self.api_key}"

        data = self._fetch_json(url)

        if not data or not isinstance(data, list):
            return []

        results = []
        for item in data:
            # New stable API format: {symbol, fiscalYear, period, date, data: {segment: value}}
            fiscal_year = item.get("fiscalYear")
            date = item.get("date")
            segments = item.get("data", {})

            if isinstance(segments, dict):
                for segment_name, revenue in segments.items():
                    results.append({
                        "symbol": symbol,
                        "date": date,
                        "fiscal_year": fiscal_year,
                        "period": period,
                        "segment_name": segment_name,
                        "segment_type": "geography",
                        "revenue": self._safe_float(revenue),
                        "source": "FMP",
                        "source_url": mask_api_key(url),
                    })

        return results

    def get_income_statement(
        self, symbol: str, limit: int = 10, period: str = "annual"
    ) -> List[Dict[str, Any]]:
        """
        Get income statement data.

        Args:
            symbol: Stock ticker symbol
            limit: Number of records to fetch
            period: "annual" or "quarter"

        Returns:
            List of income statement records
        """
        # Use stable API endpoint
        url = f"{self.BASE_URL}/stable/income-statement?symbol={symbol}&limit={limit}&period={period}&apikey={self.api_key}"

        data = self._fetch_json(url)

        if not data or not isinstance(data, list):
            return []

        results = []
        for report in data:
            fiscal_date = report.get("date")

            total_revenue = self._safe_float(report.get("revenue"))
            gross_profit = self._safe_float(report.get("grossProfit"))
            operating_income = self._safe_float(report.get("operatingIncome"))
            net_income = self._safe_float(report.get("netIncome"))
            eps = self._safe_float(report.get("epsdiluted"))

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

            results.append({
                "symbol": symbol,
                "date": fiscal_date,
                "fiscal_year": int(fiscal_date[:4]) if fiscal_date else None,
                "period": report.get("period", "FY"),
                "total_revenue": total_revenue,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "net_income": net_income,
                "eps": eps,
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
                "source": "FMP",
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
                if line.startswith("FMP_API_KEY="):
                    return line.split("=", 1)[1].strip()

    # Fall back to environment variable
    return os.environ.get("FMP_API_KEY", "")


# CLI for testing
if __name__ == "__main__":
    import sys

    api_key = load_api_key()
    if not api_key:
        print("Error: FMP_API_KEY not found in .env or environment")
        sys.exit(1)

    client = FMPClient(api_key)

    symbol = sys.argv[1] if len(sys.argv) > 1 else "MSFT"

    print(f"Fetching data for {symbol} from FMP...")

    # Test income statement
    print("\n--- Income Statement ---")
    try:
        income = client.get_income_statement(symbol, limit=5)
        print(f"Income Statement ({len(income)} years):")
        for record in income[:5]:
            revenue = record.get('total_revenue')
            net_income = record.get('net_income')
            revenue_str = f"{revenue:,.0f}" if revenue else "N/A"
            net_income_str = f"{net_income:,.0f}" if net_income else "N/A"
            print(f"  {record.get('date')}: Revenue={revenue_str}, Net Income={net_income_str}")
    except RuntimeError as e:
        print(f"Error: {e}")

    # Test segment revenue
    print("\n--- Product Segments ---")
    try:
        segments = client.get_revenue_segments(symbol)
        print(f"Product Segments ({len(segments)} records):")
        for record in segments[:10]:
            revenue = record.get('revenue')
            revenue_str = f"{revenue:,.0f}" if revenue else "N/A"
            print(f"  {record.get('date')} {record.get('segment_name')}: {revenue_str}")
    except RuntimeError as e:
        print(f"Error: {e}")

    # Test geographic segments
    print("\n--- Geographic Segments ---")
    try:
        geo = client.get_geographic_segments(symbol)
        print(f"Geographic Segments ({len(geo)} records):")
        for record in geo[:10]:
            revenue = record.get('revenue')
            revenue_str = f"{revenue:,.0f}" if revenue else "N/A"
            print(f"  {record.get('date')} {record.get('segment_name')}: {revenue_str}")
    except RuntimeError as e:
        print(f"Error: {e}")
