# Design Document: Concept Stock Price Pipeline

## Goal
Generate US concept stock price series (daily, weekly, monthly) with a consistent schema and incremental update workflow.

## Scope
- Tickers: Dynamically loaded from `concept.csv` (13 concept columns as of 2026-02)
- See `concept_metadata.csv` for full list with ticker, CIK, and segment info
- OpenAI has no public ticker and is excluded. Lenovo is HK-listed.
- Outputs: `raw_conceptstock_daily.csv`, `raw_conceptstock_weekly.csv`, `raw_conceptstock_monthly.csv`.

## Data Source
- Provider: Alpha Vantage (free tier for now).
- Endpoints:
  - `TIME_SERIES_DAILY` (compact for daily incremental refresh)
  - `TIME_SERIES_WEEKLY` (native weekly series)
  - `TIME_SERIES_MONTHLY` (native monthly series)
- API key: stored in `.env` as `ALPHAVANTAGE_API_KEY` (see `.env.example`).

## Output Schema
Common columns:
- Metadata prefix: `stock_code`, `company_name`
- Date key: `交易日期` (daily), `交易週` (weekly), `交易月份` (monthly)
- `開盤_價格_元`
- `收盤_價格_元`
- `漲跌_價格_元`
- `漲跌_pct`
- Metadata suffix: `file_type`, `source_file`, `download_success`, `download_timestamp`, `process_timestamp`, `stage1_process_timestamp`

## Calculations
- `漲跌_價格_元 = 本期收盤 - 上期收盤`
- `漲跌_pct = 漲跌_價格_元 / 上期收盤`
- “上期” follows the cadence (previous trading day/week/month).

## Incremental Update Strategy
- Daily: call `TIME_SERIES_DAILY` with `outputsize=compact` (latest ~100 points). Merge new rows by `交易日期`.
- Weekly/Monthly: full series is returned; replace or merge by `交易週` / `交易月份`.
- Store the latest date per ticker to avoid unnecessary rewrites.
- Script: `scripts/update_conceptstocks.py` supports `--ticker` or `--all` and recomputes `漲跌_價格_元` / `漲跌_pct` per ticker after merge.
- Automation: `.github/workflows/update_conceptstocks.yml` runs scheduled updates and commits CSV changes.

## Rate Limits and Reliability
- Free tier: ~25 requests/day, 1 request/second burst limit.
- Add a minimum 1–2 second delay between requests and retry on rate-limit responses.

## Data Validity Range
- Determined per ticker and cadence by min/max date in the retrieved series.
- Record the range in logs or a small summary report per refresh run.

## Future Extensions
- Add validation checks (no negative open/close, monotonic dates).
- Optional: include `最高_價格_元`, `最低_價格_元`, volume fields.
- Add a mapping layer for "concept → tickers" and metadata joins from company info.

---

## Future Extensions: Concept Stock Company Additional Data (概念股公司額外資料)

### Goal
為概念股公司（NVDA、MSFT、AMD 等）取得分項營收（Segment Revenue）及損益表等額外財務資料。

**需求**: 10 年歷史資料、分項營收、可程式化存取

### Concept Stock Company List (概念股公司清單)

> 概念股清單由 `concept_metadata.csv` 維護，透過 `python scripts/update_conceptstocks.py --sync-concepts` 同步更新到 README.md。

完整清單請參見 [README.md](README.md#concept-columns-end-with-概念) 或 `concept_metadata.csv`。

當前支援季度區段資料的公司（10 家）：

| Ticker | 公司名稱 | 資料來源 | 季度區段 |
|--------|----------|----------|----------|
| NVDA | NVIDIA Corporation | 8-K | Data Center, Gaming, Automotive, Professional Visualization |
| GOOGL | Alphabet Inc. | 8-K | Google Cloud, Google Services |
| AMZN | Amazon.com Inc. | 8-K | AWS, North America, International |
| META | Meta Platforms Inc. | 8-K | Family of Apps, Reality Labs |
| MSFT | Microsoft Corporation | 8-K | Intelligent Cloud, More Personal Computing, PBP |
| AMD | Advanced Micro Devices | 10-Q | Data Center, Client, Gaming, Embedded |
| AAPL | Apple Inc. | 8-K | iPhone, Mac, iPad, Services, Wearables |
| ORCL | Oracle Corporation | 10-Q | Cloud services, Hardware, Services |
| MU | Micron Technology | 8-K | Cloud Memory, Mobile and Client, etc. |
| WDC | Western Digital | 10-Q | Cloud, Client, Consumer, Flash, HDD |

### Data Source Comparison (資料來源比較)

| 來源 | 分項營收 | 歷史深度 | 免費額度 | 易用性 | 資料格式 |
|------|----------|----------|----------|--------|----------|
| Financial Modeling Prep (FMP) | ✅ 完整 | 30+ 年 | 250/日 | ⭐⭐⭐⭐⭐ | JSON |
| Finnhub | ✅ 有限 | 5-10 年 | 60/分 | ⭐⭐⭐⭐ | JSON |
| SEC EDGAR XBRL | ✅ 需解析 | 10+ 年 | 無限制 | ⭐⭐ | XBRL/JSON |
| Alpha Vantage | ❌ 無 | 5 年 | 25/日 | ⭐⭐⭐⭐ | JSON |
| Yahoo Finance | ❌ 無 | 5 年 | 無限制 | ⭐⭐⭐ | DataFrame |

**Note**: Alpha Vantage 已用於股價資料，但不支援分項營收。

### Recommended Implementation (建議實作方案)

| 方案 | 資料來源 | 費用 | 實作難度 | 適用情境 |
|------|----------|------|----------|----------|
| A | FMP | $19/月起 | 低 | 快速實作、預算允許 |
| B | SEC EDGAR | $0 | 高 | 預算為零、可接受較長開發時間 |
| C | 混合 | 視需求 | 中 | 股價用 Alpha Vantage，分項營收用 FMP |

### Data Source Details (資料來源詳細說明)

#### 1. Financial Modeling Prep (FMP) ⭐ 推薦

**官網**: https://site.financialmodelingprep.com/

**API Endpoints**

| API | 說明 | 端點 |
|-----|------|------|
| Revenue Product Segmentation | 產品分項營收 | `/stable/revenue-product-segmentation` |
| Revenue Geographic Segments | 地區分項營收 | `/stable/revenue-geographic-segments` |
| Income Statement | 損益表 | `/stable/income-statement` |
| Income Statement Growth | 損益表成長率 | `/stable/income-statement-growth` |

**API Examples**

```bash
# 產品分項營收
curl "https://financialmodelingprep.com/stable/revenue-product-segmentation?symbol=MSFT&period=annual&apikey=YOUR_API_KEY"

# 地區分項營收
curl "https://financialmodelingprep.com/stable/revenue-geographic-segments?symbol=NVDA&period=annual&apikey=YOUR_API_KEY"

# 損益表 (10年)
curl "https://financialmodelingprep.com/api/v3/income-statement/AAPL?limit=40&apikey=YOUR_API_KEY"
```

**Pricing**

| 方案 | 價格 | API 請求/日 | 頻寬/月 | 歷史資料 |
|------|------|-------------|---------|----------|
| Free | $0 | 250 | 500MB | 5 年 |
| Starter | $19/月 | 無限制 | 20GB | 30+ 年 |
| Premium | $49/月 | 無限制 | 50GB | 30+ 年 |
| Ultimate | $99/月 | 無限制 | 150GB | 30+ 年 |

**優點**: 直接提供分項營收 API、JSON 格式易處理、30+ 年歷史、學生 30% 折扣

**缺點**: 免費方案功能有限、需付費才能取得完整分項資料

#### 2. Finnhub ⭐⭐ 備選

**官網**: https://finnhub.io/

**API Endpoints**

| API | 說明 | 端點 |
|-----|------|------|
| Revenue Breakdown | 營收分項 | `/api/v1/stock/revenue-breakdown` |
| Basic Financials | 基本財務指標 | `/api/v1/stock/metric` |
| Financials Reported | 財報資料 | `/api/v1/stock/financials-reported` |

**API Example (Python)**

```python
import finnhub

finnhub_client = finnhub.Client(api_key="YOUR_API_KEY")

# 營收分項
revenue = finnhub_client.revenue_breakdown('MSFT')

# 基本財務指標
metrics = finnhub_client.company_basic_financials('NVDA', 'all')
```

**Pricing**

| 方案 | 價格 | API 請求/分 | 功能 |
|------|------|-------------|------|
| Free | $0 | 60 | 基本功能 |
| All-in-one | $49/月 | 300 | 完整功能 |
| Enterprise | 洽詢 | 無限制 | 客製化 |

**優點**: 免費方案功能較完整、Python/JS 官方 SDK、即時資料支援

**缺點**: 分項營收僅限美國公司、歷史深度不如 FMP

#### 3. SEC EDGAR XBRL ⭐⭐⭐ 完全免費但複雜

**官網**: https://www.sec.gov/edgar/searchedgar/companysearch

**API Endpoints**

| API | 說明 | 端點 |
|-----|------|------|
| Company Facts | 公司所有 XBRL 資料 | `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json` |
| Company Concept | 特定概念資料 | `https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json` |
| Frames | 跨公司彙總 | `https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/{unit}/CY{year}.json` |

**API Examples**

```bash
# Microsoft 所有 XBRL 資料
curl "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json"

# NVIDIA 營收資料
curl "https://data.sec.gov/api/xbrl/companyconcept/CIK0001045810/us-gaap/Revenues.json"
```

**XBRL Dimension Axis for Segment Revenue**

| Dimension Axis | 說明 | 範例公司 |
|----------------|------|----------|
| `srt:ProductOrServiceAxis` | 產品/服務分項 | Google (YouTube, Cloud) |
| `us-gaap:StatementBusinessSegmentsAxis` | 業務部門分項 | Microsoft (Intelligent Cloud) |
| `srt:GeographyAxis` | 地區分項 | Apple (Americas, Europe, China) |

**Python Tool (edgartools)**

```python
from edgar import Company, set_identity

# 設定身份 (SEC 要求)
set_identity("YourName your.email@example.com")

msft = Company("MSFT")
filings = msft.get_filings(form="10-K")
latest = filings[0]

# 取得 XBRL 資料
xbrl = latest.xbrl()
```

安裝: `pip install edgartools`

**優點**: 完全免費、官方資料來源、10+ 年歷史 (2009 年起有 XBRL)

**缺點**: XBRL 格式複雜、不同公司使用不同標籤、需自行解析 dimensions、速率限制 10 requests/second

#### 4. Alpha Vantage ⚠️ 無分項營收

目前已用於 ConceptStocks 取得股價資料，但**不支援分項營收**。

| API | 說明 | 支援分項 |
|-----|------|----------|
| INCOME_STATEMENT | 損益表 | ❌ 僅總營收 |
| BALANCE_SHEET | 資產負債表 | ❌ |
| CASH_FLOW | 現金流量表 | ❌ |
| EARNINGS | EPS | ❌ |

#### 5. Yahoo Finance (yfinance) ⚠️ 有限支援

**GitHub**: https://github.com/ranaroussi/yfinance

**缺點**: 無官方 API、可能被封鎖、不提供分項營收、僅 5 年歷史

### Planned Output Files (預計輸出檔案)

**Type 53: raw_conceptstock_company_revenue.csv** - 分項營收

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| symbol | string | 股票代號 | MSFT |
| date | date | 財報日期 | 2024-06-30 |
| period | string | 期間類型 | annual / quarter |
| segment_name | string | 分項名稱 | Intelligent Cloud |
| segment_type | string | 分項類型 | product / geography |
| revenue | float | 營收 (USD) | 32900000000 |
| revenue_yoy_pct | float | YoY 成長率 | 0.29 |

**Type 54: raw_conceptstock_company_income.csv** - 損益表

| 欄位 | 類型 | 說明 | 範例 |
|------|------|------|------|
| symbol | string | 股票代號 | NVDA |
| date | date | 財報日期 | 2025-01-26 |
| period | string | 期間類型 | annual / quarter |
| total_revenue | float | 總營收 | 39300000000 |
| gross_profit | float | 毛利 | 28700000000 |
| operating_income | float | 營業利益 | 25500000000 |
| net_income | float | 淨利 | 22100000000 |
| gross_margin | float | 毛利率 | 0.73 |
| operating_margin | float | 營益率 | 0.65 |
| net_margin | float | 淨利率 | 0.56 |

### Sample Implementation Code (範例程式碼)

#### FMP Client (方案 A)

```python
# src/external/fmp_client.py
import requests
import pandas as pd
from typing import List, Dict

class FMPClient:
    BASE_URL = "https://financialmodelingprep.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_revenue_segments(self, symbol: str, period: str = "annual") -> List[Dict]:
        """取得產品分項營收"""
        url = f"{self.BASE_URL}/stable/revenue-product-segmentation"
        params = {
            "symbol": symbol,
            "period": period,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_geographic_segments(self, symbol: str, period: str = "annual") -> List[Dict]:
        """取得地區分項營收"""
        url = f"{self.BASE_URL}/stable/revenue-geographic-segments"
        params = {
            "symbol": symbol,
            "period": period,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_income_statement(self, symbol: str, limit: int = 40) -> List[Dict]:
        """取得損益表 (最多 40 季/10 年)"""
        url = f"{self.BASE_URL}/api/v3/income-statement/{symbol}"
        params = {
            "limit": limit,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        return response.json()


# 使用範例
if __name__ == "__main__":
    client = FMPClient(api_key="YOUR_API_KEY")

    CONCEPT_COMPANIES = ["NVDA", "MSFT", "AMD", "GOOGL", "META", "AAPL", "AMZN", "ORCL", "MU", "WDC"]

    all_data = []
    for symbol in CONCEPT_COMPANIES:
        segments = client.get_revenue_segments(symbol)
        for record in segments:
            record["symbol"] = symbol
            all_data.append(record)

    df = pd.DataFrame(all_data)
    df.to_csv("raw_conceptstock_company_revenue.csv", index=False)
```

#### SEC EDGAR Extractor (方案 B)

```python
# src/external/edgar_client.py
from edgar import Company, set_identity
import pandas as pd

# 設定身份 (SEC 要求)
set_identity("YourName your.email@example.com")

class EdgarSegmentExtractor:
    # 公司特定的 segment axis 對應
    SEGMENT_MAPPING = {
        "MSFT": {
            "axis": "us-gaap:StatementBusinessSegmentsAxis",
            "segments": {
                "IntelligentCloudMember": "Intelligent Cloud",
                "ProductivityAndBusinessProcessesMember": "Productivity and Business Processes",
                "MorePersonalComputingMember": "More Personal Computing"
            }
        },
        "NVDA": {
            "axis": "us-gaap:StatementBusinessSegmentsAxis",
            "segments": {
                "DataCenterMember": "Data Center",
                "GamingMember": "Gaming",
                "ProfessionalVisualizationMember": "Professional Visualization",
                "AutomotiveMember": "Automotive"
            }
        },
        # ... 其他公司
    }

    def extract_segment_revenue(self, symbol: str, years: int = 10) -> pd.DataFrame:
        """從 10-K 報告提取分項營收"""
        company = Company(symbol)
        filings = company.get_filings(form="10-K").head(years)

        results = []
        for filing in filings:
            try:
                xbrl = filing.xbrl()
                # 解析 segment 資料...
                # (需要根據公司特定的 XBRL 結構)
            except Exception as e:
                print(f"Error processing {symbol} {filing.filing_date}: {e}")

        return pd.DataFrame(results)
```

### GitHub Sync Configuration (同步設定)

如果建立獨立 repo 存放概念股公司資料，可使用以下同步設定：

```yaml
# .github/sync-Python-Actions.GoodInfo.Analyzer.yml
group:
  - files:
      - source: data/raw_conceptstock_company_revenue.csv
        dest:   data/stage1_raw/raw_conceptstock_company_revenue.csv
      - source: data/raw_conceptstock_company_income.csv
        dest:   data/stage1_raw/raw_conceptstock_company_income.csv
    repos: |
        wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer
```

### Action Items (下一步行動)

- [x] 決定採用方案 C：混合方案（SEC EDGAR 為主，FMP 為輔）
- [x] 註冊 API 帳號並取得 API Key（FMP, Alpha Vantage）
- [x] 建立 `src/external/` 目錄與客戶端程式（sec_edgar_client.py, fmp_client.py, alphavantage_client.py）
- [x] 定義 Type 53/54 輸出檔案（raw_conceptstock_company_revenue.csv, raw_conceptstock_company_income.csv）
- [x] 建立 GitHub Actions 定期更新排程（update_company_financials.yml）
- [x] 新增季度區段資料（raw_conceptstock_company_quarterly_segments.csv/md）
- [x] 建立 8-K 新聞稿解析器（NVDA, GOOGL, AMZN, META, MSFT, AAPL, MU）
- [x] 建立 10-Q 區段解析器（AMD, ORCL, WDC）
- [ ] 整合到 Stage 1 Pipeline（待同步到 GoodInfo.Analyzer）

### References (參考資源)

- [Financial Modeling Prep Documentation](https://site.financialmodelingprep.com/developer/docs)
- [Finnhub API Documentation](https://finnhub.io/docs/api)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [EdgarTools Documentation](https://edgartools.readthedocs.io/)
- [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
