# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ConceptStocks 是一個概念股價格資料管線專案，用於收集並維護美國概念股（如 NVIDIA、Google、Microsoft 等）的日/週/月股價資料。使用 Alpha Vantage API 作為資料來源。

## Common Commands

```bash
# 更新單一股票的所有週期資料
python3 scripts/update_conceptstocks.py --ticker NVDA --cadence all

# 更新所有股票的週線資料
python3 scripts/update_conceptstocks.py --all --cadence weekly

# 僅同步概念對照表
python3 scripts/update_conceptstocks.py --sync-concepts

# 可用的 cadence 選項: daily, weekly, monthly, all
# 可用的 ticker: NVDA, GOOGL, AMZN, META, MSFT, AMD, AAPL, ORCL, MU, WDC
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
- `raw_conceptstock_daily.csv` - 日線資料（最近約 100 筆）
- `raw_conceptstock_weekly.csv` - 週線資料（完整歷史）
- `raw_conceptstock_monthly.csv` - 月線資料（完整歷史）

### CSV Schema 結構
```
[stock_code, company_name, 日期欄位, 開盤_價格_元, 收盤_價格_元, 漲跌_價格_元, 漲跌_pct, metadata...]
```
- 日期欄位依週期不同：`交易日期`（日）、`交易週`（週）、`交易月份`（月）
- 詳細欄位定義參見 `raw_column_definition.md`

### 概念股對照
概念欄位命名規則為 `X概念`，例如：`nVidia概念`、`Microsoft概念`、`AMD概念`。概念對照表從外部 GoodInfo 儲存庫同步。

## API 限制

- Alpha Vantage 免費方案：約 25 requests/day
- 腳本內建 1.2 秒延遲以符合速率限制
- 若遇到速率限制錯誤，會在輸出中顯示警告

## GitHub Actions

排程任務定義於 `.github/workflows/update_conceptstocks.yml`：
- 每週日 0:00 UTC - 同步概念對照表
- 週一至週五 22:15 UTC - 更新日線資料
- 週五 22:45 UTC - 更新週線資料
- 每月 1 日 23:15 UTC - 更新月線資料

需設定 Repository Secret: `ALPHAVANTAGE_API_KEY`

## Configuration

API Key 設定方式：
1. 複製 `.env.example` 為 `.env`
2. 填入 `ALPHAVANTAGE_API_KEY=your_key_here`
