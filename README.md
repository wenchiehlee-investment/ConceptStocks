# ConceptStocks

Working space for ConceptStocks.

## What is 「概念股」 in this repo?
This repository uses the GoodInfo company dataset to tag **concept themes**. A company is considered a **「概念股」** for a theme when the corresponding concept column is marked as `1`. The free-text column `相關概念` lists the concepts as a semicolon-separated string and mirrors these binary flags.

### Concept columns (end with 「概念」)
- `相關概念`
- `nVidia概念`
- `Google概念`
- `Amazon概念`
- `Meta概念`
- `OpenAI概念`
- `Microsoft概念`
- `AMD概念`
- `Apple概念`
- `Oracle概念`

## Concept stock price samples (US)
We are producing native **daily / weekly / monthly** price series for US concept stocks. The first review sample is NVDA (NVIDIA Corporation) using Alpha Vantage.

Output files:
- `raw_conceptstock_daily.csv`
- `raw_conceptstock_weekly.csv`
- `raw_conceptstock_monthly.csv`

Schema (all required):
- `交易日期` / `交易週` / `交易月份`
- `代號`, `名稱`
- `開盤_價格_元`, `收盤_價格_元`, `漲跌_價格_元`, `漲跌_pct`

Notes:
- Daily (free tier) returns the most recent 100 points; weekly/monthly return full history.
- OpenAI is private (no ticker). The NVDA sample is used as the first review example.

If you add new concept columns, keep the naming pattern `X概念` and update this list.
