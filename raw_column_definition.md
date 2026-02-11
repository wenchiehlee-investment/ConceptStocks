---
source: https://raw.githubusercontent.com/wenchiehlee-investment/ConceptStocks/refs/heads/main/raw_column_definition.md
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/raw_column_definition.md
---

# Raw CSV Column Definitions - ConceptStocks v1.1.0
## Based on Alpha Vantage Time Series Outputs

### Version History:
- **v1.1.0** (2026-02-11): Align numbering with GoodInfo (No.30-36); add quarterly_segments (No.35) and segment_overrides (No.36); align common metadata with GoodInfo standard
- **v1.0.0** (2026-01-18): Initial definitions for concept stock daily/weekly/monthly price series

## Common Metadata Columns

The common metadata schema follows the same convention as [Python-Actions.GoodInfo.Analyzer](https://github.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer).

### Column Order Specification:
```
[stock_code, company_name, ...data_columns..., file_type, source_file, download_success, download_timestamp, process_timestamp, stage1_process_timestamp]
```

| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `stock_code` | **Column 1** | string | 4-digit Taiwan stock code or US stock ticker | `2330`, `1587` or `NVDA`, `AAPL` |
| `company_name` | **Column 2** | string | Company name extracted from filename | `台積電`, `日月光` or `NVIDIA Corporation` |
| `file_type` | **Last -5** | string | Source data type identifier | `TIME_SERIES_DAILY`, `33`, `34` |
| `source_file` | **Last -4** | string | Source URL or filename | `https://www.alphavantage.co/query?...` |
| `download_success` | **Last -3** | boolean/null | Whether download succeeded | `True`, `False`, or `null` |
| `download_timestamp` | **Last -2** | datetime/null | When data was downloaded | `2026-01-18 16:10:00` or `null` |
| `process_timestamp` | **Last -1** | datetime/null | When the file was processed | `2026-01-18 16:10:00` or `null` |
| `stage1_process_timestamp` | **Last** | datetime | When stage 1 pipeline ran | `2026-01-18 16:10:00.123456` |

### Column Insertion Logic:
- **Beginning columns**: `stock_code` and `company_name` are always first and second
- **Data columns**: All extracted data columns occupy the middle positions
- **Metadata suffix**: The final 6 metadata columns are always appended at the end in fixed order

### Applicability:

| CSV | Column 1 | Common metadata suffix |
|-----|----------|----------------------|
| No. 30-32 (price) | `stock_code` | Yes |
| No. 33-34 (revenue, income) | `symbol` | Yes |
| No. 35-36 (quarterly_segments, segment_overrides) | `symbol` | No (standalone files) |

> Note: No. 33-34 use `symbol` instead of `stock_code` as Column 1 name but serve the same role.
> No. 35-36 are standalone CSV files without the common metadata suffix.

---

## raw_conceptstock_daily.csv (Daily Concept Stock Prices)
**No:** 30
**Source:** Alpha Vantage `TIME_SERIES_DAILY`
**Extraction Strategy:** Use Alpha Vantage daily series (compact for incremental updates). Compute change vs prior close.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `交易日期` | date | Trading date | Time Series key | `YYYY-MM-DD` |
| `開盤_價格_元` | float | Open price (USD) | `1. open` | Native daily open |
| `收盤_價格_元` | float | Close price (USD) | `4. close` | Native daily close |
| `漲跌_價格_元` | float | Price change (USD) | Derived | `收盤_價格_元 - 上一日收盤_價格_元` |
| `漲跌_pct` | float | Price change (%) | Derived | `漲跌_價格_元 / 上一日收盤_價格_元` |

---

## raw_conceptstock_weekly.csv (Weekly Concept Stock Prices)
**No:** 31
**Source:** Alpha Vantage `TIME_SERIES_WEEKLY`
**Extraction Strategy:** Use native weekly series. Compute change vs prior week close.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `交易週` | date | Week ending date | Time Series key | `YYYY-MM-DD` (week end) |
| `開盤_價格_元` | float | Open price (USD) | `1. open` | Native weekly open |
| `收盤_價格_元` | float | Close price (USD) | `4. close` | Native weekly close |
| `漲跌_價格_元` | float | Price change (USD) | Derived | `收盤_價格_元 - 上一週收盤_價格_元` |
| `漲跌_pct` | float | Price change (%) | Derived | `漲跌_價格_元 / 上一週收盤_價格_元` |

---

## raw_conceptstock_monthly.csv (Monthly Concept Stock Prices)
**No:** 32
**Source:** Alpha Vantage `TIME_SERIES_MONTHLY`
**Extraction Strategy:** Use native monthly series. Compute change vs prior month close.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `交易月份` | string | Trading month | Time Series key | `YYYY-MM` |
| `開盤_價格_元` | float | Open price (USD) | `1. open` | Native monthly open |
| `收盤_價格_元` | float | Close price (USD) | `4. close` | Native monthly close |
| `漲跌_價格_元` | float | Price change (USD) | Derived | `收盤_價格_元 - 上一月收盤_價格_元` |
| `漲跌_pct` | float | Price change (%) | Derived | `漲跌_價格_元 / 上一月收盤_價格_元` |

---

## raw_conceptstock_company_revenue.csv (Concept Stock Company Segment Revenue)
**No:** 33
**Source:** Financial Modeling Prep (FMP) or SEC EDGAR (10-K HTML parsing)
**Extraction Strategy:** Fetch product/geographic segment revenue from FMP API (primary) or parse SEC 10-K HTML tables (fallback for ORCL/MU/WDC/QCOM/DELL).

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `fiscal_year` | integer | Fiscal year | API response | e.g., `2025` |
| `end_date` | date | Fiscal period end date | API response | `YYYY-MM-DD` |
| `period` | string | Period type | API response | `annual` |
| `segment_name` | string | Segment name | API response | e.g., `Intelligent Cloud` |
| `segment_type` | string | Segment category | API response | `product` or `geography` |
| `revenue` | float | Revenue (USD) | API response | Raw value in USD |
| `revenue_yoy_pct` | float | Year-over-year growth | Derived | Decimal format (0.29 = 29%) |
| `currency` | string | Currency code | API response | Always `USD` |
| `source` | string | Data source | System | `FMP` or `SEC` |

> Column 1-2: `stock_code` (`symbol`), `company_name` — see Common Metadata Columns
> Plus common metadata suffix (see above)

---

## raw_conceptstock_company_income.csv (Concept Stock Company Income Statement)
**No:** 34
**Source:** SEC EDGAR XBRL (primary) + Alpha Vantage / FMP (cross-check)
**Extraction Strategy:** Fetch income statement from SEC EDGAR XBRL API (primary). Cross-check with Alpha Vantage and FMP.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `fiscal_year` | integer | Fiscal year | API response | e.g., `2025` |
| `end_date` | date | Fiscal period end date | API response | `YYYY-MM-DD` |
| `period` | string | Period type | API response | `FY`, `Q1`, `Q2`, `Q3` |
| `total_revenue` | float | Total revenue (USD) | API response | Top-line revenue |
| `gross_profit` | float | Gross profit (USD) | API response | Revenue - COGS |
| `operating_income` | float | Operating income (USD) | API response | EBIT |
| `net_income` | float | Net income (USD) | API response | Bottom-line profit |
| `eps` | float | Earnings per share | API response | Diluted EPS |
| `gross_margin` | float | Gross margin | Derived | `gross_profit / total_revenue` |
| `operating_margin` | float | Operating margin | Derived | `operating_income / total_revenue` |
| `net_margin` | float | Net margin | Derived | `net_income / total_revenue` |
| `currency` | string | Currency code | API response | Always `USD` |
| `source` | string | Data source | System | `SEC`, `AlphaVantage`, `FMP` |
| `validation_status` | string | Cross-check result | System | e.g., `SEC_only`, `matched` |

> Column 1-2: `stock_code` (`symbol`), `company_name` — see Common Metadata Columns
> Plus common metadata suffix (see above)

---

## raw_conceptstock_company_quarterly_segments.csv (Quarterly Product Segment Revenue)
**No:** 35
**Source:** SEC EDGAR 10-Q (Q1-Q3) and 8-K press releases (all quarters)
**Extraction Strategy:** Parse segment revenue from SEC 10-Q filings and 8-K press releases. Q4 is calculated as FY - (Q1+Q2+Q3).

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `fiscal_year` | integer | Fiscal year | Parsed | e.g., `2026` |
| `quarter` | string | Fiscal quarter | Parsed | `Q1`, `Q2`, `Q3`, `Q4` |
| `segment_name` | string | Product segment name | Parsed | e.g., `Data Center`, `Gaming` |
| `revenue` | float | Segment revenue (USD) | Parsed | Raw value in USD |
| `end_date` | date | Quarter end date | Parsed | `YYYY-MM-DD` |
| `is_calculated` | boolean | Whether Q4 was calculated | System | `True` if Q4 = FY-(Q1+Q2+Q3) |

> Column 1-2: `stock_code` (`symbol`), `company_name` — see Common Metadata Columns
> No common metadata suffix (standalone file)

---

## raw_conceptstock_company_segment_overrides.csv (Manual Segment Revenue Overrides)
**No:** 36
**Source:** Manual entry from 10-K filings
**Extraction Strategy:** Hand-curated data to fill gaps or fix errors in FMP/SEC automated parsing.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `fiscal_year` | integer | Fiscal year | Manual | e.g., `2025` |
| `period` | string | Period type | Manual | Always `annual` |
| `segment_name` | string | Segment name | Manual | e.g., `Handsets`, `Microsoft Office` |
| `segment_type` | string | Segment category | Manual | `product` or `geography` |
| `revenue` | float | Revenue (USD) | Manual | Raw value in USD |
| `source` | string | Data source | Manual | e.g., `10-K` |
| `notes` | string | Explanation | Manual | Why this override is needed |

> Column 1: `stock_code` (`symbol`) — see Common Metadata Columns (no `company_name` column)
> No common metadata suffix (hand-curated file)
