# Design Document: Concept Stock Price Pipeline

## Goal
Generate US concept stock price series (daily, weekly, monthly) with a consistent schema and incremental update workflow.

## Scope
- Tickers: NVDA, GOOG/GOOGL, AMZN, META, MSFT, AMD, AAPL, ORCL.
- OpenAI has no public ticker and is excluded or mapped via proxy rules.
- Outputs: `raw_conceptstock_daily.csv`, `raw_conceptstock_weekly.csv`, `raw_conceptstock_monthly.csv`.

## Data Source
- Provider: Alpha Vantage (free tier for now).
- Endpoints:
  - `TIME_SERIES_DAILY` (compact for daily incremental refresh)
  - `TIME_SERIES_WEEKLY` (native weekly series)
  - `TIME_SERIES_MONTHLY` (native monthly series)

## Output Schema
Common columns:
- Date key: `交易日期` (daily), `交易週` (weekly), `交易月份` (monthly)
- `代號` (ticker)
- `名稱` (company name)
- `開盤_價格_元`
- `收盤_價格_元`
- `漲跌_價格_元`
- `漲跌_pct`

## Calculations
- `漲跌_價格_元 = 本期收盤 - 上期收盤`
- `漲跌_pct = 漲跌_價格_元 / 上期收盤`
- “上期” follows the cadence (previous trading day/week/month).

## Incremental Update Strategy
- Daily: call `TIME_SERIES_DAILY` with `outputsize=compact` (latest ~100 points). Merge new rows by `交易日期`.
- Weekly/Monthly: full series is returned; replace or merge by `交易週` / `交易月份`.
- Store the latest date per ticker to avoid unnecessary rewrites.

## Rate Limits and Reliability
- Free tier: ~25 requests/day, 1 request/second burst limit.
- Add a minimum 1–2 second delay between requests and retry on rate-limit responses.

## Data Validity Range
- Determined per ticker and cadence by min/max date in the retrieved series.
- Record the range in logs or a small summary report per refresh run.

## Future Extensions
- Add validation checks (no negative open/close, monotonic dates).
- Optional: include `最高_價格_元`, `最低_價格_元`, volume fields.
- Add a mapping layer for “concept → tickers” and metadata joins from company info.
