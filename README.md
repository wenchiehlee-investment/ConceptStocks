# ConceptStocks

Working space for ConceptStocks.

## What is 「概念股」 in this repo?
This repository uses the GoodInfo company dataset to tag **concept themes**. A company is considered a **「概念股」** for a theme when the corresponding concept column is marked as `1`. The free-text column `相關概念` lists the concepts as a semicolon-separated string and mirrors these binary flags.

### Concept columns (end with 「概念」)

| 概念欄位 | 公司名稱 | Ticker | CIK | 季度區段 |
|----------|----------|--------|-----|----------|
| nVidia概念 | NVIDIA Corporation | NVDA | 0001045810 | Data Center, Gaming, Automotive, Professional Visualization |
| Google概念 | Alphabet Inc. | GOOGL | 0001652044 | Google Cloud, Google Services |
| Amazon概念 | Amazon.com Inc. | AMZN | 0001018724 | AWS, North America, International |
| Meta概念 | Meta Platforms Inc. | META | 0001326801 | Family of Apps, Reality Labs |
| OpenAI概念 | OpenAI | - | 私人公司 | - |
| Microsoft概念 | Microsoft Corporation | MSFT | 0000789019 | Intelligent Cloud, More Personal Computing, Productivity and Business Processes |
| AMD概念 | Advanced Micro Devices | AMD | 0000002488 | Data Center, Client, Gaming, Embedded |
| Apple概念 | Apple Inc. | AAPL | 0000320193 | iPhone, Mac, iPad, Services, Wearables |
| Oracle概念 | Oracle Corporation | ORCL | 0001341439 | Cloud services, Hardware, Services |
| Micro概念 | Micron Technology | MU | 0000723125 | Cloud Memory, Mobile and Client, Core Data Center |
| SanDisk概念 | Western Digital | WDC | 0000106040 | Cloud, Client, Consumer, Flash, HDD |
| Qualcomm概念 | Qualcomm Inc. | QCOM | 0000804328 | - |
| Lenovo概念 | Lenovo Group | 0992.HK | 香港上市 | - |

> 概念欄位來源：`concept.csv` 中以「概念」結尾的欄位（共 13 個）
> 概念 metadata：`concept_metadata.csv`


Additional column: `相關概念` (semicolon-separated list of concepts)

## Concept stock price samples (US)
We are producing native **daily / weekly / monthly** price series for US concept stocks. The first review sample is NVDA (NVIDIA Corporation) using Alpha Vantage.

Output files:
- `raw_conceptstock_daily.csv`
- `raw_conceptstock_weekly.csv`
- `raw_conceptstock_monthly.csv`

Schema (all required):
- Common columns (match GoodInfo raw CSVs): `stock_code`, `company_name`, plus metadata suffix `file_type`, `source_file`, `download_success`, `download_timestamp`, `process_timestamp`, `stage1_process_timestamp`
- Date column: `交易日期` / `交易週` / `交易月份`
- Price columns: `開盤_價格_元`, `收盤_價格_元`, `漲跌_價格_元`, `漲跌_pct`

Notes:
- Daily (free tier) returns the most recent 100 points; weekly/monthly return full history.
- OpenAI is private (no ticker). The NVDA sample is used as the first review example.
- Configure the API key in `.env` (see `.env.example`) as `ALPHAVANTAGE_API_KEY`.
- For GitHub Actions, set a repository secret named `ALPHAVANTAGE_API_KEY`.

### Updating data
Use the updater script to refresh a single ticker or all tickers. Examples:
```
python3 scripts/update_conceptstocks.py --ticker NVDA --cadence all
python3 scripts/update_conceptstocks.py --all --cadence weekly
```

If you add new concept columns, keep the naming pattern `X概念` and update this list.

## Quarterly Product Segment Data

We collect quarterly product segment revenue from SEC EDGAR filings (10-Q and 8-K press releases).

Output files:
- `raw_conceptstock_company_quarterly_segments.csv` - Raw quarterly segment data
- `raw_conceptstock_company_quarterly_segments.md` - Human-readable quarterly report

Data sources by company:
| Company | Source | Segments |
|---------|--------|----------|
| NVDA | 8-K | Data Center, Gaming, Automotive, Professional Visualization |
| GOOGL | 8-K | Google Cloud, Google Services |
| AMZN | 8-K | AWS, North America, International |
| META | 8-K | Family of Apps, Reality Labs |
| MSFT | 8-K | Intelligent Cloud, More Personal Computing, PBP |
| AMD | 10-Q | Data Center, Client, Gaming, Embedded |
| AAPL | 8-K | iPhone, Mac, iPad, Services, Wearables |
| ORCL | 10-Q | Cloud services, Hardware, Services |
| MU | 8-K | Cloud Memory, Mobile and Client, etc. |
| WDC | 10-Q | Cloud, Client, Consumer, Flash, HDD |

### Updating quarterly segments
```bash
python scripts/generate_quarterly_segments.py --years 5
```
