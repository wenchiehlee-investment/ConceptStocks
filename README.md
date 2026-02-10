# ConceptStocks

Working space for ConceptStocks.

## What is 「概念股」 in this repo?
This repository uses the GoodInfo company dataset to tag **concept themes**. A company is considered a **「概念股」** for a theme when the corresponding concept column is marked as `1`. The free-text column `相關概念` lists the concepts as a semicolon-separated string and mirrors these binary flags.

### Concept columns (end with 「概念」)

Update time: 2026-02-07 20:48:07 CST
| 概念欄位 | 公司名稱 | Ticker | CIK | 最新財報 | 即將發布 | 發布時間 | 產品區段 |
|----------|----------|--------|-----|----------|----------|----------|----------|
| TSMC概念 | Taiwan Semiconductor | TSM | 美國ADR | - | - | - | - |
| nVidia概念 | NVIDIA Corporation | NVDA | 0001045810 | FY2026 Q3 | FY2026 Q4 | 2026年2月底 | Data Center, Gaming, Automotive, Professional Visualization |
| Google概念 | Alphabet Inc. | GOOGL | 0001652044 | FY2025 Q4 | FY2026 Q1 | 2026年4月 | Google Cloud, Google Services |
| Amazon概念 | Amazon.com Inc. | AMZN | 0001018724 | FY2025 Q4 | FY2026 Q1 | 2026年4月 | AWS, North America, International |
| Meta概念 | Meta Platforms Inc. | META | 0001326801 | FY2025 Q4 | FY2026 Q1 | 2026年4月 | Family of Apps, Reality Labs |
| OpenAI概念 | OpenAI | - | 私人公司 | - | - | - | - |
| Microsoft概念 | Microsoft Corporation | MSFT | 0000789019 | FY2026 Q2 | FY2026 Q3 | 2026年4月 | Intelligent Cloud, More Personal Computing, PBP |
| AMD概念 | Advanced Micro Devices | AMD | 0000002488 | FY2025 Q4 | FY2026 Q1 | 2026年4月 | Data Center, Client, Gaming, Embedded |
| Apple概念 | Apple Inc. | AAPL | 0000320193 | FY2026 Q1 | FY2026 Q2 | 2026年4月 | iPhone, Mac, iPad, Services, Wearables |
| Oracle概念 | Oracle Corporation | ORCL | 0001341439 | FY2026 Q2 | FY2026 Q3 | 2026年3月 | Cloud services, Hardware, Services |
| Micro概念 | Micron Technology | MU | 0000723125 | FY2026 Q1 | FY2026 Q2 | 2026年3月 | Cloud Memory, Mobile and Client, Core Data Center |
| SanDisk概念 | Western Digital | WDC | 0000106040 | FY2026 Q2 | FY2026 Q3 | 2026年4月 | Cloud, Client, Consumer, Flash, HDD |
| Qualcomm概念 | Qualcomm Inc. | QCOM | 0000804328 | FY2026 Q1 | FY2026 Q2 | 2026年4月 | Handsets, IoT, Licensing, Automotive |
| Lenovo概念 | Lenovo Group | LNVGY | 美國ADR | FY2026 Q3 | FY2026 Q4 | 2026年5月 | - |
| Dell概念 | Dell Technologies | DELL | 0001571996 | FY2026 Q3 | FY2026 Q4 | 2026年2月底 | Servers and networking, Storage |
| HP概念 | HP Inc. | HPQ | 0000047217 | FY2025 Q4 | FY2026 Q1 | 2026年2月底 | - |

> 概念欄位來源：`concept.csv` 中以「概念」結尾的欄位（共 16 個）
> 概念 metadata：`concept_metadata.csv`


### 財年制度說明

美國公司財年 (Fiscal Year) 以結束年份命名，不一定是曆年制 (1-12月)。

**欄位說明**：
- **最新財報**：已發布的最新季度財報
- **即將發布**：下一季財報
- **發布時間**：預計發布月份

**各公司財年結束月**：
| 財年結束月 | 公司 |
|-----------|------|
| 1月 | NVDA, DELL |
| 5月 | ORCL |
| 6月 | MSFT, WDC |
| 8月 | MU |
| 9月 | AAPL, QCOM |
| 10月 | HPQ |
| 12月 | GOOGL, AMZN, META, AMD |
| 3月 | Lenovo |

**財年命名規則**：
- MSFT FY2026 = 2025年7月 ~ 2026年6月 (結束於2026年)
- AAPL FY2026 = 2025年10月 ~ 2026年9月 (結束於2026年)
- NVDA FY2026 = 2025年2月 ~ 2026年1月 (結束於2026年)

**52/53週制**：部分公司 (NVDA, DELL, AMD, AAPL, MU, WDC, QCOM) 採用52週制，財年結束日每年略有變動。


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
