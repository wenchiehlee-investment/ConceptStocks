---
source: https://raw.githubusercontent.com/wenchiehlee-investment/ConceptStocks/refs/heads/main/raw_column_definition.md
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/raw_column_definition.md
---

# Raw CSV Column Definitions - ConceptStocks v1.0.0
## Based on Alpha Vantage Time Series Outputs

### Version History:
- **v1.0.0** (2026-01-18): Initial definitions for concept stock daily/weekly/monthly price series

## Common Metadata Columns (All Files)

Every raw CSV file includes these standard metadata columns in **specific positions**:

### Column Order Specification:
```
[stock_code, company_name, ...data_columns..., file_type, source_file, download_success, download_timestamp, process_timestamp, stage1_process_timestamp]
```

| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `stock_code` | **Column 1** | string | US stock ticker | `NVDA`, `AAPL` |
| `company_name` | **Column 2** | string | Company name | `NVIDIA Corporation` |
| `file_type` | **Last -5** | string | Alpha Vantage function | `TIME_SERIES_DAILY` |
| `source_file` | **Last -4** | string | Source URL used for fetch | `https://www.alphavantage.co/query?...` |
| `download_success` | **Last -3** | boolean/null | Whether download succeeded | `True` |
| `download_timestamp` | **Last -2** | datetime/null | When data was downloaded | `2026-01-18 16:10:00` |
| `process_timestamp` | **Last -1** | datetime/null | When the file was processed | `2026-01-18 16:10:00` |
| `stage1_process_timestamp` | **Last** | datetime | When stage 1 pipeline ran | `2026-01-18 16:10:00.123456` |

### Column Insertion Logic:
- **Beginning columns**: `stock_code` and `company_name` are always first and second
- **Data columns**: All extracted data columns occupy the middle positions
- **Metadata suffix**: The final 6 metadata columns are always appended at the end in fixed order

---

## raw_conceptstock_daily.csv (Daily Concept Stock Prices)
**No:** 1
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
**No:** 2
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
**No:** 3
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

## raw_concept_company_revenue.csv (Concept Stock Company Segment Revenue) [Planned]
**No:** 53
**Source:** Financial Modeling Prep (FMP) or SEC EDGAR XBRL
**Extraction Strategy:** Fetch product/geographic segment revenue from FMP API or parse SEC XBRL filings.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `symbol` | string | Stock ticker | API response | e.g., `MSFT`, `NVDA` |
| `date` | date | Fiscal period end date | API response | `YYYY-MM-DD` |
| `period` | string | Period type | API response | `annual` or `quarter` |
| `segment_name` | string | Segment name | API response | e.g., `Intelligent Cloud` |
| `segment_type` | string | Segment category | API response | `product` or `geography` |
| `revenue` | float | Revenue (USD) | API response | Raw value in USD |
| `revenue_yoy_pct` | float | Year-over-year growth | Derived | Decimal format (0.29 = 29%) |
| `currency` | string | Currency code | API response | Always `USD` |
| `source` | string | Data source | System | `FMP` or `SEC` |

---

## raw_concept_company_income.csv (Concept Stock Company Income Statement) [Planned]
**No:** 54
**Source:** Financial Modeling Prep (FMP) or SEC EDGAR XBRL
**Extraction Strategy:** Fetch income statement data from FMP API or parse SEC XBRL filings.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `symbol` | string | Stock ticker | API response | e.g., `MSFT`, `NVDA` |
| `date` | date | Fiscal period end date | API response | `YYYY-MM-DD` |
| `period` | string | Period type | API response | `annual` or `quarter` |
| `total_revenue` | float | Total revenue (USD) | API response | Top-line revenue |
| `gross_profit` | float | Gross profit (USD) | API response | Revenue - COGS |
| `operating_income` | float | Operating income (USD) | API response | EBIT |
| `net_income` | float | Net income (USD) | API response | Bottom-line profit |
| `eps` | float | Earnings per share | API response | Diluted EPS |
| `gross_margin` | float | Gross margin | Derived | `gross_profit / total_revenue` |
| `operating_margin` | float | Operating margin | Derived | `operating_income / total_revenue` |
| `net_margin` | float | Net margin | Derived | `net_income / total_revenue` |
| `currency` | string | Currency code | API response | Always `USD` |
| `source` | string | Data source | System | `FMP` or `SEC` |
