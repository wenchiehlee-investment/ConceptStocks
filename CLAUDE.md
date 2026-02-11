# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ConceptStocks 是一個概念股資料管線專案，用於收集並維護美國概念股（如 NVIDIA、Google、Microsoft 等）的：
- **股價資料**：日/週/月股價（Alpha Vantage API）
- **財務報表**：損益表（SEC EDGAR + Alpha Vantage 交叉驗證）
- **分項營收**：產品/地區營收細分（FMP API）

## Common Commands

### 股價資料更新
```bash
# 更新單一股票的所有週期資料
python scripts/update_conceptstocks.py --ticker NVDA --cadence all

# 更新所有股票的週線資料
python scripts/update_conceptstocks.py --all --cadence weekly

# 僅同步概念對照表
python scripts/update_conceptstocks.py --sync-concepts
```

### 公司財務資料更新
```bash
# 從 SEC EDGAR 更新所有公司的損益表（含 Alpha Vantage 交叉驗證）
python scripts/update_company_financials.py --all --type income --source sec-edgar

# 包含季度資料（FY + Q1-Q3）
python scripts/update_company_financials.py --all --type income --source sec-edgar --period all

# 僅季度資料
python scripts/update_company_financials.py --symbol MSFT --type income --source sec-edgar --period quarterly

# 從 FMP 更新單一公司的分項營收
python scripts/update_company_financials.py --symbol MSFT --type revenue --source fmp

# 更新所有資料（所有來源）
python scripts/update_company_financials.py --all --type all --source all

# 可用的 type: income, revenue, all
# 可用的 source: sec-edgar, alphavantage, fmp, all
# 可用的 period: annual（預設）, quarterly, all
# 可用的 symbol: NVDA, GOOGL, AMZN, META, MSFT, AMD, AAPL, ORCL, MU, WDC
```

## Architecture

### 單一腳本設計
整個資料管線由 `scripts/update_conceptstocks.py` 單一 Python 腳本完成，無外部依賴（僅使用 Python 標準函式庫）。

### 資料流程
1. 從 Alpha Vantage API 取得股價資料
2. 與現有 CSV 檔案合併（以 ticker + date 為 key）
3. 重新計算衍生欄位（漲跌金額、漲跌百分比）
4. 寫入標準化 CSV 輸出

### 輸出檔案

**股價資料：**
- `raw_conceptstock_daily.csv` - 日線資料（最近約 100 筆）
- `raw_conceptstock_weekly.csv` - 週線資料（完整歷史）
- `raw_conceptstock_monthly.csv` - 月線資料（完整歷史）

**公司財務資料：**
- `raw_conceptstock_company_income.csv` - 損益表（Type 34）
- `raw_conceptstock_company_revenue.csv` - 分項營收（Type 33）
- `raw_conceptstock_company_segments.md` - 年度分項營收報告
- `raw_conceptstock_company_quarterly_segments.csv` - 季度產品分項資料
- `raw_conceptstock_company_quarterly_segments.md` - 季度產品分項報告

### CSV Schema 結構
```
[stock_code, company_name, 日期欄位, 開盤_價格_元, 收盤_價格_元, 漲跌_價格_元, 漲跌_pct, metadata...]
```
- 日期欄位依週期不同：`交易日期`（日）、`交易週`（週）、`交易月份`（月）
- 詳細欄位定義參見 `raw_column_definition.md`

### 概念股對照
概念欄位命名規則為 `X概念`，例如：`nVidia概念`、`Microsoft概念`、`AMD概念`。概念對照表從外部 GoodInfo 儲存庫同步。

## API 限制

| API | 免費方案限制 | 用途 |
|-----|-------------|------|
| Alpha Vantage | 25 requests/day | 股價、損益表交叉驗證 |
| SEC EDGAR | 10 requests/second | 損益表（主要來源） |
| FMP | 250 requests/day | 分項營收、損益表交叉驗證 |

腳本內建延遲以符合速率限制。若遇到速率限制錯誤，會在輸出中顯示警告。

## GitHub Actions

### 股價更新 (`update_conceptstocks.yml`)
- 每週日 0:00 UTC - 同步概念對照表
- 週一至週五 22:15 UTC - 更新日線資料
- 週五 22:45 UTC - 更新週線資料
- 每月 1 日 23:15 UTC - 更新月線資料

### 財務資料更新 (`update_company_financials.yml`)
- 每季更新（2/15, 5/15, 8/15, 11/15）- 財報季後

需設定 Repository Secrets:
- `ALPHAVANTAGE_API_KEY` - Alpha Vantage API 金鑰
- `FMP_API_KEY` - Financial Modeling Prep API 金鑰

## Configuration

API Key 設定方式：
1. 複製 `.env.example` 為 `.env`
2. 填入所需的 API Keys：
   ```
   ALPHAVANTAGE_API_KEY=your_key_here
   FMP_API_KEY=your_key_here
   ```
