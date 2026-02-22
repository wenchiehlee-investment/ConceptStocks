---
destination: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.Analyzer/refs/heads/main/raw_column_definition.md
---

# Raw CSV Column Definitions - Revised v2.3.0
## Based on Actual GoodInfo Excel File Structure Analysis

### Version History:
- **v2.3.1** (2026-02-13): Keep full master definition and merge latest ConceptStocks schema update (add No.37 `raw_conceptstock_company_metadata.csv`)
- **v2.3.0** (2025-12-30): Added Type 17 (Weekly K-Line Flow), Type 18 (Daily K-Line Flow), Type 51 (FactSet Analyst Consensus Summary)
- **v2.2.0** (2025-12-24): Added Type 16 (Quarterly Financial Ratio Analysis) - Full-history QRY_TIME pagination with transposed output
- **v2.1.0** (2025-12-05): Added Type 13 (Daily Margin), Type 14 (Weekly Margin), Type 15 (Monthly Margin) - Multi-frequency margin balance data
- **v2.0.0**: Complete 12-type documentation with detailed column definitions
- **v1.0.0**: Initial column definition framework

## Common Metadata Columns (All Files)

Every raw CSV file includes these standard metadata columns in **specific positions**:

### Column Order Specification:
```
[stock_code, company_name, ...data_columns..., file_type, source_file, download_success, download_timestamp, process_timestamp, stage1_process_timestamp]
```



| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `stock_code` | **Column 1** | string | 4-digit Taiwan stock code or US stock ticker| `2330`, `1587` or `NVDA`, `AAPL` |
| `company_name` | **Column 2** | string | Company name extracted from filename | `台積電`, `日月光` or `NVIDIA Corporation` |
| `file_type` | **Last -5** | string | Source data type identifier | `ShowSaleMonChart`, `DividendDetail` |
| `source_file` | **Last -4** | string | Original filename processed | `ShowSaleMonChart_1587_日月光.xls` |
| `download_success` | **Last -3** | boolean/null | Whether download succeeded | `True`, `False`, or `null` |
| `download_timestamp` | **Last -2** | datetime/null | When data was downloaded from GoodInfo.tw | `2025-08-23 16:45:30` or `null` |
| `process_timestamp` | **Last -1** | datetime/null | When downloader processed the stock | `2025-08-23 16:45:10` or `null` |
| `stage1_process_timestamp` | **Last** | datetime | When Stage 1 pipeline ran | `2025-08-27 12:09:33.286390` |

### Column Insertion Logic:
- **Beginning columns**: `stock_code` and `company_name` are always first and second
- **Data columns**: All extracted data columns occupy the middle positions  
- **Metadata suffix**: The final 6 metadata columns are always appended at the end in fixed order


---

## raw_dividends.csv (Dividend Distribution and Yield Data)
**No:**1
**Source:** `DividendDetail/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockDividendPolicy.asp?STOCK_ID={stock_id} 
**Extraction Strategy:** Handle multi-header table with merged cells

### Actual Excel Structure Analysis:
- Columns A-B: 股利發放期間, 股利所屬期間
- Columns C-J: 股利政策 section (現金股利, 股票股利 with 盈餘/公積/合計 sub-columns)
- Columns K-L: 填息/填權花費日數
- Column M: 股價年度
- Columns N-W: 現金殖利率 section (multiple price reference points)

### Revised Columns (Multi-Header Aware):

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|---|
| `股利_發放_期間` | string | Dividend payout period | Column A |Empty rows;"累計" rows; "∟" rows|
| `股利_所屬_期間` | string | Dividend fiscal period | Column B |Empty rows;"累計" rows|
| `現金股利_盈餘` | float | Cash dividend from earnings | Column C ||
| `現金股利_公積` | float | Cash dividend from capital surplus | Column D ||
| `現金股利_合計` | float | Total cash dividend | Column E ||
| `股票股利_盈餘` | float | Stock dividend from earnings | Column F ||
| `股票股利_公積` | float | Stock dividend from capital surplus | Column G ||
| `股票股利_合計` | float | Total stock dividend | Column H ||
| `股利_合計` | float | Total dividend (cash + stock) | Column I ||
| `填息_花費_日數` | int | Ex-dividend recovery days | Column K ||
| `填權_花費_日數` | int | Ex-rights recovery days | Column L ||
| `股價_年度` | string | Stock price reference year | Column M ||
| `現金殖利率_除息前_價格` | float | Dividend yield at pre-ex-dividend price | Column N ||
| `現金殖利率_除息前_利率` | float | Dividend yield percentage at pre-ex-dividend | Column O ||
| `現金殖利率_年均價_價格` | float | Dividend yield at annual average price | Column P ||
| `現金殖利率_年均價_利率` | float | Dividend yield percentage at annual average | Column Q ||
| `現金殖利率_成交價_價格` | float | Dividend yield at trading price | Column R ||
| `現金殖利率_成交價_利率` | float | Dividend yield percentage at trading price | Column S ||
| `現金殖利率_最高價_價格` | float | Dividend yield at highest price | Column T ||
| `現金殖利率_最高價_利率` | float | Dividend yield percentage at highest | Column U ||
| `現金殖利率_最低價_價格` | float | Dividend yield at lowest price | Column V ||
| `現金殖利率_最低價_利率` | float | Dividend yield percentage at lowest | Column W ||

---

## raw_performance.csv (Annual Financial Performance)
**No:**4
**Source:** `StockBzPerformance/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}
**Note:** This structure already matches well with current extraction

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `年度` | string | Financial year/quarter | Column A |Empty rows|
| `股本_億` | float | Share capital (hundred million NT$) | Column B ||
| `財報_評分` | int | Financial report score | Column C ||
| `年度股價_元_收盤` | float | Year-end closing price | Column D ||
| `年度股價_元_平均` | float | Average stock price | Column E ||
| `年度股價_元_漲跌` | float | Stock price change (NT$) | Column F ||
| `年度股價_元_漲跌_pct` | float | Stock price change (%) | Column G ||
| `獲利金額_億_營業_收入` | float | Operating revenue (hundred million NT$) | Column H ||
| `獲利金額_億_營業_毛利` | float | Gross profit (hundred million NT$) | Column I ||
| `獲利金額_億_營業_利益` | float | Operating profit (hundred million NT$) | Column J ||
| `獲利金額_億_業外_損益` | float | Non-operating income (hundred million NT$) | Column K ||
| `獲利金額_億_稅後_淨利` | float | Net income after tax (hundred million NT$) | Column L ||
| `獲利率_pct_營業_毛利` | float | Gross margin (%) | Column M ||
| `獲利率_pct_營業_利益` | float | Operating margin (%) | Column N ||
| `獲利率_pct_業外_損益` | float | Non-operating margin (%) | Column O ||
| `獲利率_pct_稅後_淨利` | float | Net margin (%) | Column P ||
| `roe_pct` | float | Return on equity (%) | Column Q ||
| `roa_pct` | float | Return on assets (%) | Column R ||
| `eps_元_稅後_eps` | float | Earnings per share (NT$) | Column S ||
| `eps_元_年增_元` | float | EPS change from previous year | Column T ||
| `bps_元` | float | Book value per share (NT$) | Column U ||

---

## raw_revenue.csv (Monthly Revenue and Stock Price Data)
**No:**5
**Source:** `ShowSaleMonChart/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/ShowSaleMonChart.asp?STOCK_ID={stock_id}
**Extraction Strategy:** Extract both stock price and revenue data from complex table

### Actual Excel Structure Analysis:
- Column A: 月別 (Month)
- Columns B-G: 當月股價 section (開盤, 收盤, 最高, 最低, 漲跌元, 漲跌%)
- Columns H-L: 營業收入 section (營收億, 月增%, 年增%, 營收億, 年增%)
- Columns M-Q: 合併營業收入 section (營收億, 月增%, 年增%, 營收億, 年增%)

### Revised Columns (Comprehensive Extraction):

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `月別` | string | Month period (YYYY/MM) | Column A |Empty rows|
| `當月股價_開盤` | float | Monthly stock price - Open | Column B ||
| `當月股價_收盤` | float | Monthly stock price - Close | Column C ||
| `當月股價_最高` | float | Monthly stock price - High | Column D ||
| `當月股價_最低` | float | Monthly stock price - Low | Column E ||
| `當月股價_漲跌_元` | float | Monthly price change (NT$) | Column F ||
| `當月股價_漲跌_pct` | float | Monthly price change (%) | Column G ||
| `營業收入_營收_億` | float | Operating revenue (hundred million NT$) | Column H ||
| `營業收入_月增_pct` | float | Operating revenue monthly change (%) | Column I ||
| `營業收入_年增_pct` | float | Operating revenue yearly change (%) | Column J ||
| `營業收入_累計_億` | float | Operating revenue cumulative (hundred million NT$) | Column K ||
| `營業收入_累計年增_pct` | float | Operating revenue cumulative YoY change (%) | Column L ||
| `合併營業收入_營收_億` | float | Consolidated revenue (hundred million NT$) | Column M ||
| `合併營業收入_月增_pct` | float | Consolidated revenue monthly change (%) | Column N ||
| `合併營業收入_年增_pct` | float | Consolidated revenue yearly change (%) | Column O ||
| `合併營業收入_累計_億` | float | Consolidated revenue cumulative (hundred million NT$) | Column P ||
| `合併營業收入_累計年增_pct` | float | Consolidated revenue cumulative YoY change (%) | Column Q ||

---

## raw_equity_distribution.csv (Shareholding Structure and Distribution)
**No:**6
**Source:** `EquityDistribution/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/EquityDistributionCatHis.asp?STOCK_ID={stock_id}
**Extraction Strategy:** Extract shareholding structure and distribution data with detailed institutional breakdown

### Actual Excel Structure Analysis:
- Column A: 年度 (Year)
- Column B: 收盤 (Closing Price)
- Columns C-D: 漲跌元, 漲跌% (Price Changes)
- Columns E-R: Institutional Holdings Breakdown (Government, Financial, Foreign, Domestic)
- Variable columns based on time period and available data

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `年度` | string | Annual period (YYYY) | Column A |Empty rows|
| `收盤_價格_元` | float | Closing stock price (NT$) | Column B ||
| `漲跌_價格_元` | float | Price change (NT$) | Column C ||
| `漲跌_pct` | float | Price change (%) | Column D ||
| `政府公營機構_pct` | float | Government institutions holding (%) | Column E ||
| `金融機構_pct` | float | Financial institutions holding (%) | Column F ||
| `證券投信_pct` | float | Securities investment trust holding (%) | Column G ||
| `僑外投資_僑外_pct` | float | Foreign investment - collective (%) | Column H ||
| `僑外投資_證券_pct` | float | Foreign investment - securities (%) | Column I ||
| `僑外投資_僑外自然人_pct` | float | Foreign investment - individuals (%) | Column J ||
| `僑外投資_合計_pct` | float | Foreign investment - total (%) | Column K ||
| `本國金融機構_金融機構_pct` | float | Domestic financial institutions (%) | Column L ||
| `本國金融機構_證券投信_pct` | float | Domestic securities investment trust (%) | Column M ||
| `本國金融機構_合計_pct` | float | Domestic financial institutions - total (%) | Column N ||
| `本國法人_公司法人_pct` | float | Domestic corporate entities (%) | Column O ||
| `本國法人_其他法人_pct` | float | Other domestic entities (%) | Column P ||
| `本國法人_合計_pct` | float | Domestic entities - total (%) | Column Q ||
| `本國自然人_個人_pct` | float | Domestic individual investors (%) | Column R ||

### File Structure Notes:
- **Annual Frequency**: Data collected on annual basis
- **Institutional Focus**: Detailed breakdown of different investor types
- **Regulatory Context**: Reflects Taiwan stock market shareholding regulations
- **Time Series Data**: Historical shareholding changes over time

---

## raw_performance1.csv (Quarterly Performance Detail)
**No:**7
**Source:** `StockBzPerformance1/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}&YEAR_PERIOD=9999&PRICE_ADJ=F&SCROLL2Y=480&RPT_CAT=M_QUAR 
**Extraction Strategy:** Extract quarterly financial performance data with detailed metrics

### Actual Excel Structure Analysis:
- Column A: 季度 (Quarter)
- Column B: 股本億 (Share Capital)
- Column C: 財報評分 (Financial Report Score)
- Columns D-G: Quarterly Stock Price data (收盤, 平均, 漲跌元, 漲跌%)
- Columns H-L: Profit Amount data (營業收入, 營業毛利, 營業利益, 業外損益, 稅後淨利)
- Columns M-P: Profit Margin data (毛利率, 營業利益率, 業外損益率, 稅後淨利率)
- Columns Q-W: Financial Ratios (ROE, ROA, EPS, BPS)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `季度` | string | Quarter period (YYYY/Q#) | Column A |Empty rows|
| `股本_億` | float | Share capital (hundred million NT$) | Column B ||
| `財報_評分` | int | Financial report score | Column C ||
| `季度股價_元_收盤` | float | Quarterly closing price | Column D ||
| `季度股價_元_平均` | float | Quarterly average price | Column E ||
| `季度股價_元_漲跌` | float | Quarterly price change (NT$) | Column F ||
| `季度股價_元_漲跌_pct` | float | Quarterly price change (%) | Column G ||
| `獲利金額_億_營業_收入` | float | Operating revenue (hundred million NT$) | Column H ||
| `獲利金額_億_營業_毛利` | float | Gross profit (hundred million NT$) | Column I ||
| `獲利金額_億_營業_利益` | float | Operating profit (hundred million NT$) | Column J ||
| `獲利金額_億_業外_損益` | float | Non-operating income (hundred million NT$) | Column K ||
| `獲利金額_億_稅後_淨利` | float | Net income after tax (hundred million NT$) | Column L ||
| `獲利率_pct_營業_毛利` | float | Gross margin (%) | Column M ||
| `獲利率_pct_營業_利益` | float | Operating margin (%) | Column N ||
| `獲利率_pct_業外_損益` | float | Non-operating margin (%) | Column O ||
| `獲利率_pct_稅後_淨利` | float | Net margin (%) | Column P ||
| `單季_roe_pct` | float | Quarterly ROE (%) | Column Q ||
| `年估_roe_pct` | float | Annual estimated ROE (%) | Column R ||
| `單季_roa_pct` | float | Quarterly ROA (%) | Column S ||
| `年估_roa_pct` | float | Annual estimated ROA (%) | Column T ||
| `eps_元_稅後_eps` | float | Earnings per share after tax (NT$) | Column U ||
| `eps_元_年增_元` | float | EPS year-over-year change (NT$) | Column V ||
| `bps_元` | float | Book value per share (NT$) | Column W ||

### File Structure Notes:
- **Quarterly Frequency**: Data collected on quarterly basis
- **Quarterly Focus**: More granular than annual performance data
- **Financial Metrics**: Comprehensive quarterly financial performance tracking
- **Time Series Data**: Historical quarterly trends and comparisons

---

## raw_weekly_flow.csv (Weekly Stock Performance and P/E Analysis)
**No:**8
**Source:** `ShowK_ChartFlow/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id} 
**Extraction Strategy:** Weekly trading data with P/E ratio analysis across multiple price targets

### Actual Excel Structure Analysis:
- Column A: 交易週別 (Trading Week)
- Column B: 收盤價 (Closing Price) 
- Column C: 漲跌價 (Price Change NT$)
- Column D: 漲跌幅 (Price Change %)
- Column E: 河流圖EPS(元) (River Chart EPS)
- Column F: 目前PER(倍) (Current P/E Ratio)
- Columns G-L: 本益比換算價格 (P/E Ratio Target Prices) at different multiples

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `交易_週別` | string | Trading week identifier (YYWxx format) | Column A |Empty rows|
| `收盤價_元` | float | Weekly closing price (NT$) | Column B ||
| `漲跌價_元` | float | Weekly price change (NT$) | Column C ||
| `漲跌幅_pct` | float | Weekly price change percentage | Column D ||
| `河流圖_eps_元` | float | River chart EPS (NT$) | Column E ||
| `目前_per_倍` | float | Current P/E ratio (times) | Column F ||
| `本益比換算價格_15x_元` | float | P/E target price at 15x multiple | Column G ||
| `本益比換算價格_18x_元` | float | P/E target price at 18x multiple | Column H ||
| `本益比換算價格_21x_元` | float | P/E target price at 21x multiple | Column I ||
| `本益比換算價格_24x_元` | float | P/E target price at 24x multiple | Column J ||
| `本益比換算價格_27x_元` | float | P/E target price at 27x multiple | Column K ||
| `本益比換算價格_30x_元` | float | P/E target price at 30x multiple | Column L ||

---

## raw_stock_his_quar.csv (Stock Price History Quarter Analysis)
**No:**9
**Source:** `StockHisAnaQuar/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockHisAnaQuar.asp?STOCK_ID={stock_id}
**Extraction Strategy:** Quarterly stock price analysis with open/close/change data for each quarter

### Actual Excel Structure Analysis:
- Column A: 年度 (Year)
- Columns B-E: 第一季 section (開盤, 收盤, 漲跌, %)
- Columns F-I: 第二季 section (開盤, 收盤, 漲跌, %)
- Columns J-M: 第三季 section (開盤, 收盤, 漲跌, %)
- Columns N-Q: 第四季 section (開盤, 收盤, 漲跌, %)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `年度` | string | Year identifier (YYYY) | Column A |Empty rows;"平均" rows|
| `第一季_開盤_元` | float | Q1 opening price (NT$) | Column B ||
| `第一季_收盤_元` | float | Q1 closing price (NT$) | Column C ||
| `第一季_漲跌_元` | float | Q1 price change (NT$) | Column D ||
| `第一季_漲跌_pct` | float | Q1 price change percentage | Column E ||
| `第二季_開盤_元` | float | Q2 opening price (NT$) | Column F ||
| `第二季_收盤_元` | float | Q2 closing price (NT$) | Column G ||
| `第二季_漲跌_元` | float | Q2 price change (NT$) | Column H ||
| `第二季_漲跌_pct` | float | Q2 price change percentage | Column I ||
| `第三季_開盤_元` | float | Q3 opening price (NT$) | Column J ||
| `第三季_收盤_元` | float | Q3 closing price (NT$) | Column K ||
| `第三季_漲跌_元` | float | Q3 price change (NT$) | Column L ||
| `第三季_漲跌_pct` | float | Q3 price change percentage | Column M ||
| `第四季_開盤_元` | float | Q4 opening price (NT$) | Column N ||
| `第四季_收盤_元` | float | Q4 closing price (NT$) | Column O ||
| `第四季_漲跌_元` | float | Q4 price change (NT$) | Column P ||
| `第四季_漲跌_pct` | float | Q4 price change percentage | Column Q ||

### File Structure Notes:
- **Quarterly Structure:** Data organized by quarters within each year
- **Price Analysis:** Focus on quarterly opening, closing, and change metrics
- **Historical Context:** Multi-year quarterly stock price trends
- **Systematic Layout:** Consistent four-quarter structure per row

---

## raw_equity_class_his.csv (Equity Class Histogram Weekly)
**No:**10
**Source:** `EquityDistributionClassHis/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/EquityDistributionClassHis.asp?STOCK_ID={stock_id}
**Extraction Strategy:** Extract equity class histogram weekly data showing stock price and shareholding distribution across different holding sizes

### Actual Excel Structure Analysis:
- Column A: 週別 (Week)
- Column B: 統計日期 (Statistics Date)
- Columns C-E: 當週股價 section (收盤, 漲跌(元), 漲跌(%))
- Column F: 集保庫存(萬張) (TDCC Inventory in 10k shares)
- Columns G onwards: 各持股等級股東之持有比例(%) (Shareholding distribution by holding class percentages)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `週別` | string | Week identifier (YYWxx format) | Column A |Empty rows|
| `統計_日期` | string | Statistics date | Column B ||
| `當週股價_收盤_元` | float | Weekly closing price (NT$) | Column C ||
| `當週股價_漲跌_元` | float | Weekly price change (NT$) | Column D ||
| `當週股價_漲跌_pct` | float | Weekly price change percentage | Column E ||
| `集保庫存_萬張` | float | TDCC inventory (10k shares) | Column F ||
| `持股_小於等於10張_pct` | float | Holdings ≤10 shares percentage | Column G ||
| `持股_大於10張小於等於50張_pct` | float | Holdings >10 ≤50 shares percentage | Column H ||
| `持股_大於50張小於等於100張_pct` | float | Holdings >50 ≤100 shares percentage | Column I ||
| `持股_大於100張小於等於200張_pct` | float | Holdings >100 ≤200 shares percentage | Column J ||
| `持股_大於200張小於等於400張_pct` | float | Holdings >200 ≤400 shares percentage | Column K ||
| `持股_大於400張小於等於800張_pct` | float | Holdings >400 ≤800 shares percentage | Column L ||
| `持股_大於800張小於等於1千張_pct` | float | Holdings >800 ≤1k shares percentage | Column M ||
| `持股_大於1千張_pct` | float | Holdings >1k shares percentage | Column N ||

### File Structure Notes:
- **Weekly Frequency:** Data collected on weekly basis
- **Shareholding Distribution:** Detailed breakdown by holding size categories
- **TDCC Integration:** Uses Taiwan Depository & Clearing Corporation data
- **Investor Behavior Analysis:** Tracks retail vs institutional holding patterns
- **Market Structure Insight:** Shows concentration/dispersion of shareholdings
- **Price Correlation:** Combines stock price movement with ownership changes

### Data Completeness:
- **Comprehensive Holdings:** All shareholding size categories captured
- **Price Context:** Stock price movement alongside ownership data
- **Regulatory Compliance:** Follows Taiwan stock market reporting standards
- **Time Series Analysis:** Historical trends in ownership concentration

---

## raw_weekly_trading_data.csv (Weekly Trading Data with Institutional Flows)
**No:**11
**Source:** `WeeklyTradingData/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/ShowK_Chart.asp?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=600
**Extraction Strategy:** Comprehensive weekly trading data including OHLC, volume, institutional flows, and margin trading metrics

### Actual Excel Structure Analysis:
- Column A: 交易週別 (Trading Week)
- Column B: 交易日數 (Trading Days)
- Columns C-F: OHLC data (開盤, 最高, 最低, 收盤)
- Columns G-I: Price metrics (漲跌, 漲跌%, 振幅%)
- Columns J-K: Volume data (成交張數, 成交金額)
- Columns L-P: Institutional trading (法人買賣超, 外資, 投信, 自營, 合計)
- Column Q: 外資持股(%)
- Columns R-V: Margin trading (融資增減, 融資餘額, 融券增減, 融券餘額, 券資比%)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `交易_週別` | string | Trading week identifier (YYYY-MM-DD format) | Column A |Empty rows|
| `交易_日數` | int | Number of trading days in the week | Column B ||
| `開盤_價格_元` | float | Week opening price (NT$) | Column C ||
| `最高_價格_元` | float | Week highest price (NT$) | Column D ||
| `最低_價格_元` | float | Week lowest price (NT$) | Column E ||
| `收盤_價格_元` | float | Week closing price (NT$) | Column F ||
| `漲跌_價格_元` | float | Price change from previous week (NT$) | Column G ||
| `漲跌_pct` | float | Price change percentage from previous week | Column H ||
| `振幅_pct` | float | Weekly price range percentage ((High-Low)/Previous_Close * 100) | Column I ||
| `成交_張數` | int | Total trading volume in lots (1 lot = 1,000 shares) | Column J ||
| `成交_金額_億` | float | Total turnover amount (hundred million NT$) | Column K ||
| `法人買賣超_千張` | float | Institutional net buying total (thousands of lots) | Column L ||
| `外資_淨買超_千張` | float | Foreign institutional investor net buying (thousands of lots) | Column M ||
| `投信_淨買超_千張` | float | Investment trust net buying (thousands of lots) | Column N ||
| `自營_淨買超_千張` | float | Proprietary trading net buying (thousands of lots) | Column O ||
| `法人_合計_千張` | float | Total institutional net buying (thousands of lots) | Column P |
| `外資_持股_pct` | float | Foreign investor ownership percentage | Column Q ||
| `融資_增減_張` | int | Change in margin buying positions (lots) | Column R |
| `融資_餘額_張` | int | Margin buying balance (lots) | Column S ||
| `融券_增減_張` | int | Change in short selling positions (lots) | Column T |
| `融券_餘額_張` | int | Short selling balance (lots) | Column U ||
| `券資比_pct` | float | Short selling to margin buying ratio percentage | Column V ||

### File Structure Notes:
- **Weekly Frequency:** Complete weekly trading data aggregation
- **OHLC Data:** Standard weekly price data (Open, High, Low, Close)
- **Volume Analysis:** Trading volume and turnover amount tracking
- **Institutional Flows:** Detailed breakdown of institutional investor activity
  - **Foreign Investors (外資):** Qualified Foreign Institutional Investors (QFII)
  - **Investment Trusts (投信):** Domestic mutual funds and investment trusts
  - **Proprietary Trading (自營):** Securities dealer proprietary trading
- **Margin Trading:** Comprehensive margin and short selling data
- **Market Microstructure:** Institutional ownership and leveraged position tracking

### Data Quality & Validation:
- **Price Consistency**: High ≥ Open, Close; Low ≤ Open, Close
- **Volume Validation**: Volume and turnover amount consistency
- **Institutional Sum Check**: Foreign + Investment Trust + Proprietary = Total
- **Percentage Validation**: All percentage fields within reasonable ranges
- **Margin Balance Logic**: Balance changes match reported increases/decreases

### Cross-Reference Integration:
- **Type 5 (Monthly Revenue)**: Compare institutional flows with revenue announcements
- **Type 8 (Weekly P/E Flow)**: Validate price data consistency across weekly sources
- **Type 10 (Weekly Equity Distribution)**: Cross-check foreign ownership percentages
- **Type 9 (Quarterly Historical)**: Quarterly aggregation validation

### Market Analysis Applications:
- **Institutional Sentiment**: Track foreign vs domestic institutional positioning
- **Leverage Monitoring**: Margin trading trend analysis for market risk assessment
- **Price Discovery**: Volume-price relationship and institutional flow impact
- **Market Structure**: Foreign ownership concentration and retail vs institutional dynamics

---

## raw_monthly_flow.csv (Monthly Stock Performance and P/E Analysis)**No:**12
**Source:** `ShowMonthlyK_ChartFlow/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/ShowK_ChartFlow.asp?RPT_CAT=PER&STOCK_ID={stock_id}&CHT_CAT=MONTH&SCROLL2Y=439
**Extraction Strategy:** Monthly trading data with P/E ratio analysis across conservative multiple price targets for long-term valuation

### Actual Excel Structure Analysis (Based on Provided Snapshot):
- Column A: 交易月份 (Trading Month) - format "25M09"
- Column B: 收盤價 (Closing Price) - 642
- Column C: 漲跌價 (Price Change NT$) - 153
- Column D: 漲跌幅 (Price Change %) - 31.30%
- Column E: 河流圖EPS(元) (River Chart EPS) - 24.09
- Column F: 目前PER(倍) (Current P/E Ratio) - 26.65
- Columns G-L: 本益比換算價格 (P/E Ratio Target Prices) at conservative multiples for long-term analysis

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `交易_月份` | string | Trading month identifier (YYMxx format, e.g., "25M09") | Column A |Empty rows|
| `收盤價_元` | float | Monthly closing price (NT$) | Column B ||
| `漲跌價_元` | float | Monthly price change (NT$) | Column C ||
| `漲跌幅_pct` | float | Monthly price change percentage | Column D ||
| `河流圖_eps_元` | float | River chart EPS (NT$) | Column E ||
| `目前_per_倍` | float | Current P/E ratio (times) | Column F ||
| `本益比換算價格_9x_元` | float | P/E target price at 9x multiple | Column G ||
| `本益比換算價格_11x_元` | float | P/E target price at 11x multiple | Column H ||
| `本益比換算價格_13x_元` | float | P/E target price at 13x multiple | Column I ||
| `本益比換算價格_15x_元` | float | P/E target price at 15x multiple | Column J ||
| `本益比換算價格_17x_元` | float | P/E target price at 17x multiple | Column K ||
| `本益比換算價格_19x_元` | float | P/E target price at 19x multiple | Column L ||

### File Structure Notes:
- **Monthly Frequency:** Monthly aggregation for long-term trend analysis
- **20-Year Coverage:** Extended historical data for comprehensive backtesting
- **Conservative P/E Multiples:** Lower range (9X-19X) compared to weekly analysis (15X-30X)
- **Long-Term Focus:** Designed for fundamental analysis and portfolio management
- **Cross-Reference Integration:** Complements weekly P/E analysis with monthly perspective

### Key Differentiators from Type 8 (Weekly P/E Flow):
- **Timeframe:** Monthly vs Weekly granularity
- **Historical Coverage:** 20-year vs 5-year data depth
- **P/E Multiple Range:** Conservative 9X-19X vs aggressive 15X-30X
- **Month Identifier Format:** "YYMxx" vs "YYWxx" format
- **Analysis Purpose:** Long-term valuation vs short-term technical analysis

### Data Quality & Validation:
- **P/E Ratio Validation:** Reasonable ranges and trend continuity
- **EPS Consistency:** Alignment with quarterly earnings data from other types
- **Price Consistency:** Monthly aggregation alignment with daily/weekly data
- **Historical Integrity:** No data gaps in 20-year monthly series
- **Cross-Validation:** Compare with other valuation metrics for consistency

### Cross-Reference Integration Opportunities:
- **Type 8 + Type 12:** Multi-timeframe P/E analysis for comprehensive valuation modeling
- **Type 5 + Type 12:** Monthly revenue seasonality vs monthly P/E valuation patterns
- **Type 4 + Type 12:** Annual business performance correlation with long-term P/E trends
- **Type 1 + Type 12:** Dividend policy impact on long-term monthly P/E valuations

### Market Analysis Applications:
- **Long-Term Valuation:** 20-year monthly P/E trends for fundamental analysis
- **Seasonal Pattern Detection:** Monthly granularity reveals annual cyclical valuation patterns
- **Portfolio Management:** Conservative P/E multiples support long-term investment strategies
- **Backtesting Support:** Extended history enables robust valuation strategy testing
- **Macro Correlation:** Monthly frequency aligns with economic indicator and earnings reporting cycles

---

## raw_margin_daily.csv (Daily Margin Balance Details)**No:**13
**Source:** `ShowMarginChart/*.xls*`
**GoodInfo Page:** https://goodinfo.tw/tw/ShowMarginChart.asp?STOCK_ID={stock_id}&CHT_CAT=DATE
**Extraction Strategy:** Daily margin financing and short selling data with multi-header table structure (2-row headers)

### Actual Excel Structure Analysis:
- **Header Row 1:** Main categories - 期別, 收盤, 漲跌, 漲跌(%), 成交(張), 融資(張) [6 sub-columns], 融券(張) [6 sub-columns], 資券互抵(張), 資券當沖(%), 券資比(%), 現股當沖(%)
- **Header Row 2:** Sub-headers - Detail fields for margin and short sections
- **Column A:** 期別 (Date in 'YY/MM/DD format)
- **Columns B-E:** Basic price and volume data
- **Columns F-K:** Margin financing section (買進, 賣出, 現償, 增減, 餘額, 使用率％)
- **Columns L-Q:** Short selling section (買進, 賣出, 現償, 增減, 餘額, 使用率％)
- **Columns R-U:** Additional metrics (互抵, 當沖%, 券資比%, 現股當沖%)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `期別` | string | Trading date (YY/MM/DD format, e.g., '25/12/03) | Column A |Empty rows|
| `收盤_價格_元` | float | Daily closing price (NT$) | Column B ||
| `漲跌_價格_元` | float | Daily price change (NT$) | Column C ||
| `漲跌_pct` | float | Daily price change percentage | Column D ||
| `成交_張數` | int | Daily trading volume (lots, 1 lot = 1,000 shares) | Column E ||
| `融資_買進_張` | int | Margin financing buy (lots) | Column F ||
| `融資_賣出_張` | int | Margin financing sell (lots) | Column G ||
| `融資_現償_張` | int | Margin cash repayment (lots) | Column H ||
| `融資_增減_張` | int | Margin position change (lots) | Column I ||
| `融資_餘額_張` | int | Margin balance (lots) | Column J ||
| `融資_使用率_pct` | float | Margin usage rate percentage | Column K ||
| `融券_買進_張` | int | Short covering buy (lots) | Column L ||
| `融券_賣出_張` | int | Short selling sell (lots) | Column M ||
| `融券_現償_張` | int | Short cash repayment (lots) | Column N ||
| `融券_增減_張` | int | Short position change (lots) | Column O ||
| `融券_餘額_張` | int | Short balance (lots) | Column P ||
| `融券_使用率_pct` | float | Short usage rate percentage | Column Q ||
| `資券互抵_張` | int | Margin-short offset (lots) | Column R ||
| `資券當沖_pct` | float | Margin day trading percentage | Column S ||
| `券資比_pct` | float | Short to margin ratio percentage | Column T ||
| `現股當沖_pct` | float | Cash day trading percentage | Column U ||

### File Structure Notes:
- **Daily Frequency:** Most granular margin data (1-year daily history)
- **Multi-Header Table:** Two-row header structure requires special extraction
- **Margin Financing (融資):** Buy on margin - investor borrows money to buy stocks
- **Short Selling (融券):** Borrow shares to sell - investor borrows stocks to sell
- **Real-time Sentiment:** Daily margin changes indicate retail investor sentiment
- **Risk Indicator:** High margin usage rate signals potential forced liquidation risk
- **Market Timing:** Margin peaks often precede market corrections

### Data Quality & Validation:
- **Balance Logic:** Margin balance change = Buy - Sell - Cash repayment
- **Ratio Validation:** Short/Margin ratio = (Short balance / Margin balance) × 100%
- **Usage Rate Check:** Usage rate = (Balance / Margin limit) × 100%
- **Price Consistency:** Daily close price matches other daily sources
- **Volume Match:** Trading volume consistency with market data

### Cross-Reference Integration:
- **Type 11 (Weekly Trading):** Weekly aggregation validation for margin data
- **Type 14 (Weekly Margin):** Cross-check weekly margin totals
- **Type 15 (Monthly Margin):** Monthly aggregation consistency
- **Type 5 (Revenue):** Margin changes around revenue announcement dates

### Market Analysis Applications:
- **Sentiment Analysis:** Daily margin changes indicate retail investor confidence
- **Liquidity Risk:** High margin usage rates signal potential squeeze risk
- **Technical Trading:** Margin financing peaks as contrarian indicators
- **Day Trading Activity:** Track short-term speculative behavior via day trading %
- **Short Interest:** Monitor short selling pressure and potential short squeezes

---

## raw_margin_weekly.csv (Weekly Margin Balance Details)**No:**14
**Source:** `ShowMarginChartWeek/*.xls*`
**GoodInfo Page:** https://goodinfo.tw/tw/ShowMarginChart.asp?STOCK_ID={stock_id}&PRICE_ADJ=F&CHT_CAT=WEEK&SCROLL2Y=500
**Extraction Strategy:** Weekly margin financing and short selling data with multi-header table structure (identical to Type 13, weekly frequency)

### Actual Excel Structure Analysis:
- **Header Row 1 & 2:** Same structure as Type 13 (Daily Margin Balance)
- **Column A:** 期別 (Week identifier in 'YYWxx' format, e.g., '25W49')
- **Columns B-U:** Same margin/short/price structure as Type 13
- **Historical Coverage:** 5-year weekly history (查5年)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `期別` | string | Trading week identifier (YYWxx format, e.g., '25W49') | Column A |Empty rows|
| `收盤_價格_元` | float | Weekly closing price (NT$) | Column B ||
| `漲跌_價格_元` | float | Weekly price change (NT$) | Column C ||
| `漲跌_pct` | float | Weekly price change percentage | Column D ||
| `成交_張數` | int | Weekly trading volume (lots) | Column E ||
| `融資_買進_張` | int | Margin financing buy (lots) | Column F ||
| `融資_賣出_張` | int | Margin financing sell (lots) | Column G ||
| `融資_現償_張` | int | Margin cash repayment (lots) | Column H ||
| `融資_增減_張` | int | Margin position change (lots) | Column I ||
| `融資_餘額_張` | int | Margin balance (lots) | Column J ||
| `融資_使用率_pct` | float | Margin usage rate percentage | Column K ||
| `融券_買進_張` | int | Short covering buy (lots) | Column L ||
| `融券_賣出_張` | int | Short selling sell (lots) | Column M ||
| `融券_現償_張` | int | Short cash repayment (lots) | Column N ||
| `融券_增減_張` | int | Short position change (lots) | Column O ||
| `融券_餘額_張` | int | Short balance (lots) | Column P ||
| `融券_使用率_pct` | float | Short usage rate percentage | Column Q ||
| `資券互抵_張` | int | Margin-short offset (lots) | Column R ||
| `資券當沖_pct` | float | Margin day trading percentage | Column S ||
| `券資比_pct` | float | Short to margin ratio percentage | Column T ||
| `現股當沖_pct` | float | Cash day trading percentage | Column U ||

### File Structure Notes:
- **Weekly Frequency:** Medium-term margin trend analysis (5-year history)
- **Same Structure as Type 13:** Identical columns, different time granularity
- **Week Identifier Format:** 'YYWxx' (e.g., 25W49 = 2025 Week 49)
- **Smoothed Trends:** Weekly aggregation reduces daily noise
- **Strategic Analysis:** Better for identifying medium-term sentiment shifts

### Data Quality & Validation:
- **Weekly Aggregation:** Sum of daily volumes should approximate weekly total
- **Consistency Check:** Cross-validate with Type 13 daily data
- **Balance Validation:** Weekly balance matches end-of-week daily balance
- **Trend Continuity:** Smooth transitions between weeks

### Cross-Reference Integration:
- **Type 13 (Daily Margin):** Aggregate daily to validate weekly totals
- **Type 11 (Weekly Trading):** Same weekly frequency for price/volume correlation
- **Type 15 (Monthly Margin):** Weekly data aggregates to monthly

### Market Analysis Applications:
- **Trend Identification:** Weekly patterns reveal medium-term sentiment shifts
- **Technical Analysis:** 5-year history supports backtesting trading strategies
- **Swing Trading:** Weekly margin changes for swing position timing
- **Sector Rotation:** Compare weekly margin trends across industry sectors

---

## raw_margin_monthly.csv (Monthly Margin Balance Details)**No:**15
**Source:** `ShowMarginChartMonth/*.xls*`
**GoodInfo Page:** https://goodinfo.tw/tw/ShowMarginChart.asp?STOCK_ID={stock_id}&PRICE_ADJ=F&CHT_CAT=MONTH&SCROLL2Y=400
**Extraction Strategy:** Monthly margin financing and short selling data with multi-header table structure (20-year history, units in thousands)

### Actual Excel Structure Analysis:
- **Header Row 1 & 2:** Same structure as Type 13/14 but with units in 千張 (thousands of lots)
- **Column A:** 期別 (Month identifier in 'YYMxx' format, e.g., '25M12')
- **Columns B-U:** Same structure as Type 13/14 but values in thousands
- **Historical Coverage:** 20-year monthly history (查20年)
- **Unit Difference:** Volume and margin/short values in 千張 (thousands of lots) instead of 張 (lots)

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `期別` | string | Trading month identifier (YYMxx format, e.g., '25M12') | Column A |Empty rows|
| `收盤_價格_元` | float | Monthly closing price (NT$) | Column B ||
| `漲跌_價格_元` | float | Monthly price change (NT$) | Column C ||
| `漲跌_pct` | float | Monthly price change percentage | Column D ||
| `成交_千張` | float | Monthly trading volume (thousands of lots) | Column E ||
| `融資_買進_千張` | float | Margin financing buy (thousands of lots) | Column F ||
| `融資_賣出_千張` | float | Margin financing sell (thousands of lots) | Column G ||
| `融資_現償_千張` | float | Margin cash repayment (thousands of lots) | Column H ||
| `融資_增減_千張` | float | Margin position change (thousands of lots) | Column I ||
| `融資_餘額_千張` | float | Margin balance (thousands of lots) | Column J ||
| `融資_使用率_pct` | float | Margin usage rate percentage | Column K ||
| `融券_買進_千張` | float | Short covering buy (thousands of lots) | Column L ||
| `融券_賣出_千張` | float | Short selling sell (thousands of lots) | Column M ||
| `融券_現償_千張` | float | Short cash repayment (thousands of lots) | Column N ||
| `融券_增減_千張` | float | Short position change (thousands of lots) | Column O ||
| `融券_餘額_千張` | float | Short balance (thousands of lots) | Column P ||
| `融券_使用率_pct` | float | Short usage rate percentage | Column Q ||
| `資券互抵_千張` | float | Margin-short offset (thousands of lots) | Column R ||
| `資券當沖_pct` | float | Margin day trading percentage | Column S ||
| `券資比_pct` | float | Short to margin ratio percentage | Column T ||
| `現股當沖_pct` | float | Cash day trading percentage | Column U ||

### File Structure Notes:
- **Monthly Frequency:** Long-term margin trend analysis (20-year history)
- **Extended Coverage:** 20-year monthly data for comprehensive backtesting
- **Unit Scale:** Values in 千張 (thousands of lots) for readability
- **Month Identifier Format:** 'YYMxx' (e.g., 25M12 = 2025 December)
- **Strategic Perspective:** Best for identifying long-term sentiment cycles

### Key Differentiators from Type 13/14:
- **Timeframe:** Monthly vs Weekly/Daily granularity
- **Historical Coverage:** 20-year vs 5-year (weekly) vs 1-year (daily)
- **Unit Scale:** Thousands of lots vs individual lots
- **Analysis Purpose:** Long-term cycles vs short-term sentiment

### Data Quality & Validation:
- **Monthly Aggregation:** Sum of daily/weekly should approximate monthly totals
- **Unit Conversion:** Verify 千張 values = daily 張 values ÷ 1000
- **Historical Integrity:** 20-year continuous monthly series
- **Seasonal Patterns:** Detect annual cyclical margin patterns

### Cross-Reference Integration:
- **Type 13/14 (Daily/Weekly):** Aggregate shorter timeframes to validate monthly
- **Type 12 (Monthly P/E):** Same monthly frequency for valuation correlation
- **Type 5 (Revenue):** Monthly revenue announcements vs margin sentiment

### Market Analysis Applications:
- **Long-Term Cycles:** 20-year history reveals complete market cycles
- **Macroeconomic Correlation:** Monthly frequency aligns with economic indicators
- **Portfolio Strategy:** Long-term margin trends for investment timing
- **Backtesting:** Extended history enables robust strategy validation
- **Market Structure:** Decades of data show structural margin usage evolution

---

## Multi-Header Table Handling

### For DividendDetail Files:
```python
# Special handling for multi-header tables
def handle_multi_header_table(file_path):
    # Read with multi-level headers
    tables = pd.read_html(file_path, header=[0, 1])
    # Flatten column names intelligently
    # Map to specified column structure
```

### For ShowSaleMonChart Files:
```python
# Extract specific sections from comprehensive table
def extract_revenue_sections(df):
    # Extract stock price columns B-G
    # Extract operating revenue columns H-L  
    # Extract consolidated revenue columns M-Q
    # Apply proper column naming
```

### For StockHisAnaQuar Files:
```python
# Extract quarterly sections from yearly data
def extract_quarterly_sections(df):
    # Extract Q1 columns B-E
    # Extract Q2 columns F-I
    # Extract Q3 columns J-M
    # Extract Q4 columns N-Q
    # Apply quarterly prefixes
```

### For EquityDistributionClassHis Files:
```python
# Extract shareholding distribution by class size
def extract_equity_class_distribution(df):
    # Extract stock price columns C-E
    # Extract TDCC inventory column F
    # Extract shareholding percentages columns G onwards
    # Apply holding size range prefixes
```

### For WeeklyTradingData Files:
```python
# Extract comprehensive weekly trading data
def extract_weekly_trading_data(df):
    # Extract trading week and days columns A-B
    # Extract OHLC data columns C-F
    # Extract price metrics columns G-I
    # Extract volume data columns J-K
    # Extract institutional flows columns L-P
    # Extract margin trading data columns R-V
    # Apply proper column naming and validation
```

### For ShowMonthlyK_ChartFlow Files (NEW for Type 12):
```python
# Extract monthly P/E analysis data with conservative multiples
def extract_monthly_pe_flow_data(df):
    # Extract trading month column A (YYMxx format)
    # Extract basic price data columns B-D (close, change, change%)
    # Extract EPS and current P/E columns E-F
    # Extract conservative P/E target prices columns G-L (9X-19X)
    # Apply monthly P/E prefixes for long-term analysis
    # Validate P/E multiple consistency and EPS alignment
```

### For ShowMarginChart Files (NEW for Type 13 - Daily Margin):
```python
# Extract daily margin balance data with multi-header structure
def extract_daily_margin_data(df):
    # Handle 2-row multi-header table
    # Extract date column A (YY/MM/DD format, e.g., '25/12/03)
    # Extract basic price data columns B-D (close, change, change%)
    # Extract volume column E (成交張數)
    # Extract margin financing columns F-K (買進, 賣出, 現償, 增減, 餘額, 使用率％)
    # Extract short selling columns L-Q (買進, 賣出, 現償, 增減, 餘額, 使用率％)
    # Extract additional metrics columns R-U (互抵, 當沖%, 券資比%, 現股當沖%)
    # Apply proper column naming with 融資/融券 prefixes
    # Validate balance logic: change = buy - sell - cash repayment
```

### For ShowMarginChartWeek Files (NEW for Type 14 - Weekly Margin):
```python
# Extract weekly margin balance data (same structure as Type 13, weekly frequency)
def extract_weekly_margin_data(df):
    # Handle 2-row multi-header table (identical to Type 13)
    # Extract week identifier column A (YYWxx format, e.g., '25W49')
    # Extract columns B-U with same structure as Type 13
    # Apply weekly-specific prefixes
    # Cross-validate with daily margin data aggregation
    # Verify weekly totals match sum of daily data
```

### For ShowMarginChartMonth Files (NEW for Type 15 - Monthly Margin):
```python
# Extract monthly margin balance data (same structure as Type 13/14, monthly frequency, units in thousands)
def extract_monthly_margin_data(df):
    # Handle 2-row multi-header table (same structure as Type 13/14)
    # Extract month identifier column A (YYMxx format, e.g., '25M12')
    # Extract columns B-U with same structure as Type 13/14
    # IMPORTANT: Units are in 千張 (thousands of lots) instead of 張 (lots)
    # Apply monthly-specific prefixes with _千張 suffix for volume columns
    # Cross-validate with weekly/daily margin data aggregation
    # Verify monthly totals match sum of weekly/daily data (accounting for unit conversion)
```

## Column Naming Rules Implementation

### Applied Transformations:
1. **Spaces → Underscores:** `股利 發放 期間` → `股利_發放_期間`
2. **Parentheses Content Preserved:** `現金股利(盈餘)` → `現金股利_盈餘`
3. **Percentage Signs:** `月增(%)` → `月增_pct`
4. **Section Prefixes:** Add section prefixes for complex tables
5. **ROE/ROA/EPS/BPS Lowercase:** Special case for financial ratios
6. **Quarter Prefixes:** `第一季_開盤_元`, `第二季_收盤_元`
7. **Holding Size Ranges:** `持股_小於等於10張_pct`, `持股_大於1千張_pct`
8. **Trading Data Prefixes:** `交易_週別`, `成交_張數`, `法人_合計_千張`
9. **Institutional Types:** `外資_淨買超_千張`, `投信_淨買超_千張`, `自營_淨買超_千張`
10. **Margin Prefixes:** `融資_增減_張`, `融券_餘額_張`, `券資比_pct`
11. **Monthly P/E Prefixes:** `交易_月份`, `本益比換算價格_9x_元`, `河流圖_eps_元` (NEW for Type 12)
12. **Margin Balance Prefixes (NEW for Type 13/14/15):**
    - Daily/Weekly: `融資_買進_張`, `融券_賣出_張`, `資券互抵_張`, `資券當沖_pct`, `現股當沖_pct`
    - Monthly: `融資_買進_千張`, `融券_餘額_千張`, `資券互抵_千張` (units in thousands)

### Multi-Section Naming:
- `營業收入_營收_億` (Operating revenue section)
- `合併營業收入_營收_億` (Consolidated revenue section)
- `現金殖利率_除息前_價格` (Dividend yield section)
- `第一季_開盤_元` (Q1 section)
- `持股_大於200張小於等於400張_pct` (Shareholding class section)
- `外資_淨買超_千張` (Institutional trading section)
- `融資_增減_張` (Margin trading section in Type 11)
- `本益比換算價格_9x_元` (Monthly P/E target section) - NEW for Type 12
- `融資_買進_張` (Margin financing section) - NEW for Type 13/14
- `融券_賣出_張` (Short selling section) - NEW for Type 13/14
- `融資_餘額_千張` (Monthly margin balance section) - NEW for Type 15
- `資券互抵_張`, `資券當沖_pct`, `現股當沖_pct` (Margin metrics section) - NEW for Type 13/14/15

---

## raw_fin_ratio_quarter.csv (Quarterly Financial Ratio Analysis)**No:**16
**Source:** `StockFinDetail/*.xls*`  
**GoodInfo Page:** https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=XX_M_QUAR&STOCK_ID={stock_id}&QRY_TIME={time10q_start}  
**Extraction Strategy:** Download 10-quarter blocks with QRY_TIME, merge full history, then transpose so each row is a quarter.

### Actual Excel Structure Analysis:
- **Source layout:** Multi-section financial ratios table in GoodInfo (10-quarter blocks).
- **Transposed output:** Each row is a `季度` (YYYYQn); columns are ratio metrics/sections.

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `季度` | string | Quarter identifier (YYYYQn) | Transposed row index |Empty rows|
| `獲利能力` | string | Section header (profitability group) | Section header |-
| `營業毛利率` | float | Gross margin (%) | Ratio column ||
| `營業利益率` | float | Operating margin (%) | Ratio column ||
| `稅前淨利率` | float | Pre-tax net margin (%) | Ratio column ||
| `稅後淨利率` | float | After-tax net margin (%) | Ratio column ||
| `稅後淨利率 (母公司)` | float | After-tax margin (parent) (%) | Ratio column ||
| `每股稅前盈餘 (元)` | float | EPS before tax (NT$) | Ratio column ||
| `每股稅後盈餘 (元)` | float | EPS after tax (NT$) | Ratio column ||
| `每股淨值 (元)` | float | Book value per share (NT$) | Ratio column ||
| `股東權益報酬率 (當季)` | float | ROE (quarter) (%) | Ratio column ||
| `股東權益報酬率 (年預估)` | float | ROE (annualized) (%) | Ratio column ||
| `資產報酬率 (當季)` | float | ROA (quarter) (%) | Ratio column ||
| `資產報酬率 (年預估)` | float | ROA (annualized) (%) | Ratio column ||
| `獲利季成長率` | float | Profit QoQ growth (%) | Ratio column ||
| `營收季成長率` | float | Revenue QoQ growth (%) | Ratio column ||
| `毛利季成長率` | float | Gross profit QoQ growth (%) | Ratio column ||
| `營業利益季成長率` | float | Operating profit QoQ growth (%) | Ratio column ||
| `稅前淨利季成長率` | float | Pre-tax net profit QoQ growth (%) | Ratio column ||
| `稅後淨利季成長率` | float | After-tax net profit QoQ growth (%) | Ratio column ||
| `稅後淨利季成長率 (母公司)` | float | After-tax net profit QoQ growth (parent) (%) | Ratio column ||
| `每股稅後盈餘季成長率` | float | EPS QoQ growth (%) | Ratio column ||
| `獲利年成長率` | float | Profit YoY growth (%) | Ratio column ||
| `營收年成長率` | float | Revenue YoY growth (%) | Ratio column ||
| `毛利年成長率` | float | Gross profit YoY growth (%) | Ratio column ||
| `營業利益年成長率` | float | Operating profit YoY growth (%) | Ratio column ||
| `稅前淨利年成長率` | float | Pre-tax net profit YoY growth (%) | Ratio column ||
| `稅後淨利年成長率` | float | After-tax net profit YoY growth (%) | Ratio column ||
| `稅後淨利年成長率 (母公司)` | float | After-tax net profit YoY growth (parent) (%) | Ratio column ||
| `每股稅後盈餘年成長率` | float | EPS YoY growth (%) | Ratio column ||
| `各項資產佔總資產比重` | string | Section header (asset composition) | Section header |-
| `現金 (%)` | float | Cash % of total assets | Ratio column ||
| `應收帳款 (%)` | float | A/R % of total assets | Ratio column ||
| `存貨 (%)` | float | Inventory % of total assets | Ratio column ||
| `速動資產 (%)` | float | Quick assets % of total assets | Ratio column ||
| `流動資產 (%)` | float | Current assets % of total assets | Ratio column ||
| `基金與投資 (%)` | float | Investments % of total assets | Ratio column ||
| `固定資產 (%)` | float | Fixed assets % of total assets | Ratio column ||
| `無形資產 (%)` | float | Intangible assets % of total assets | Ratio column ||
| `其他資產 (%)` | float | Other assets % of total assets | Ratio column ||
| `資產季成長率` | float | Total assets QoQ growth (%) | Ratio column ||
| `現金季成長率` | float | Cash QoQ growth (%) | Ratio column ||
| `應收帳款季成長率` | float | A/R QoQ growth (%) | Ratio column ||
| `存貨季成長率` | float | Inventory QoQ growth (%) | Ratio column ||
| `流動資產季成長率` | float | Current assets QoQ growth (%) | Ratio column ||
| `基金與投資季成長率` | float | Investments QoQ growth (%) | Ratio column ||
| `固定資產季成長率` | float | Fixed assets QoQ growth (%) | Ratio column ||
| `無形資產季成長率` | float | Intangibles QoQ growth (%) | Ratio column ||
| `其他資產季成長率` | float | Other assets QoQ growth (%) | Ratio column ||
| `資產總額季成長率` | float | Total assets QoQ growth (%) | Ratio column ||
| `資產年成長率` | float | Total assets YoY growth (%) | Ratio column ||
| `現金年成長率` | float | Cash YoY growth (%) | Ratio column ||
| `應收帳款年成長率` | float | A/R YoY growth (%) | Ratio column ||
| `存貨年成長率` | float | Inventory YoY growth (%) | Ratio column ||
| `流動資產年成長率` | float | Current assets YoY growth (%) | Ratio column ||
| `基金與投資年成長率` | float | Investments YoY growth (%) | Ratio column ||
| `固定資產年成長率` | float | Fixed assets YoY growth (%) | Ratio column ||
| `無形資產年成長率` | float | Intangibles YoY growth (%) | Ratio column ||
| `其他資產年成長率` | float | Other assets YoY growth (%) | Ratio column ||
| `資產總額年成長率` | float | Total assets YoY growth (%) | Ratio column ||
| `負債&股東權益佔總資產` | string | Section header (liability/equity composition) | Section header |-
| `應付帳款 (%)` | float | A/P % of total assets | Ratio column ||
| `流動負債 (%)` | float | Current liabilities % of total assets | Ratio column ||
| `長期負債 (%)` | float | Long-term liabilities % of total assets | Ratio column ||
| `其他負債 (%)` | float | Other liabilities % of total assets | Ratio column ||
| `負債總額 (%)` | float | Total liabilities % of total assets | Ratio column ||
| `普通股股本 (%)` | float | Common stock % of total assets | Ratio column ||
| `股東權益總額 (%)` | float | Total equity % of total assets | Ratio column ||
| `負債&股東權益季增減率` | float | Liabilities & equity QoQ change (%) | Ratio column ||
| `應付帳款季成長率` | float | A/P QoQ growth (%) | Ratio column ||
| `流動負債季成長率` | float | Current liabilities QoQ growth (%) | Ratio column ||
| `長期負債季成長率` | float | Long-term liabilities QoQ growth (%) | Ratio column ||
| `其他負債季成長率` | float | Other liabilities QoQ growth (%) | Ratio column ||
| `負債總額季成長率` | float | Total liabilities QoQ growth (%) | Ratio column ||
| `普通股股本季成長率` | float | Common stock QoQ growth (%) | Ratio column ||
| `股東權益總額季成長率` | float | Total equity QoQ growth (%) | Ratio column ||
| `負債&股東權益年增減率` | float | Liabilities & equity YoY change (%) | Ratio column ||
| `應付帳款年成長率` | float | A/P YoY growth (%) | Ratio column ||
| `流動負債年成長率` | float | Current liabilities YoY growth (%) | Ratio column ||
| `長期負債年成長率` | float | Long-term liabilities YoY growth (%) | Ratio column ||
| `其他負債年成長率` | float | Other liabilities YoY growth (%) | Ratio column ||
| `負債總額年成長率` | float | Total liabilities YoY growth (%) | Ratio column ||
| `普通股股本年成長率` | float | Common stock YoY growth (%) | Ratio column ||
| `股東權益總額年成長率` | float | Total equity YoY growth (%) | Ratio column ||
| `償債能力` | string | Section header (solvency) | Section header |-
| `現金比` | float | Cash ratio | Ratio column ||
| `速動比` | float | Quick ratio | Ratio column ||
| `流動比` | float | Current ratio | Ratio column ||
| `利息保障倍數` | float | Interest coverage | Ratio column ||
| `現金流量比 (當季)` | float | Cash flow ratio (quarter) | Ratio column ||
| `現金流量比 (年預估)` | float | Cash flow ratio (annualized) | Ratio column ||
| `經營能力` | string | Section header (operating efficiency) | Section header |-
| `營業成本率` | float | Cost of goods ratio (%) | Ratio column ||
| `營業費用率` | float | Operating expense ratio (%) | Ratio column ||
| `應收帳款週轉率 (次/年)` | float | A/R turnover (times/year) | Ratio column ||
| `應收款項收現日數 (日)` | float | Days sales outstanding | Ratio column ||
| `應付帳款週轉率 (次/年)` | float | A/P turnover (times/year) | Ratio column ||
| `應付款項付現日數 (日)` | float | Days payable outstanding | Ratio column ||
| `存貨週轉率 (次/年)` | float | Inventory turnover (times/year) | Ratio column ||
| `平均售貨日數 (日)` | float | Days inventory outstanding | Ratio column ||
| `固定資產週轉率 (次/年)` | float | Fixed asset turnover (times/year) | Ratio column ||
| `總資產週轉率 (次/年)` | float | Total asset turnover (times/year) | Ratio column ||
| `淨值週轉率 (次/年)` | float | Equity turnover (times/year) | Ratio column ||
| `應收帳款佔營收比率 (當季)` | float | A/R to revenue ratio (quarter) | Ratio column ||
| `應收帳款佔營收比率 (年預估)` | float | A/R to revenue ratio (annualized) | Ratio column ||
| `存貨佔營收比率 (當季)` | float | Inventory to revenue ratio (quarter) | Ratio column ||
| `存貨佔營收比率 (年預估)` | float | Inventory to revenue ratio (annualized) | Ratio column ||
| `現金流量狀況` | string | Section header (cash flow) | Section header |-
| `每股營業現金流量 (元)` | float | Operating CF per share (NT$) | Ratio column ||
| `每股投資現金流量 (元)` | float | Investing CF per share (NT$) | Ratio column ||
| `每股融資現金流量 (元)` | float | Financing CF per share (NT$) | Ratio column ||
| `每股淨現金流量 (元)` | float | Net CF per share (NT$) | Ratio column ||
| `每股自由現金流量 (元)` | float | Free CF per share (NT$) | Ratio column ||
| `其他指標` | string | Section header (other metrics) | Section header |-
| `負債對淨值比率` | float | Debt-to-equity ratio | Ratio column ||
| `長期資金適合率` | float | Long-term capital adequacy ratio | Ratio column ||
| `所得稅佔稅前淨利比率` | float | Income tax / pre-tax profit (%) | Ratio column ||
| `業外損益佔營收比率` | float | Non-operating profit / revenue (%) | Ratio column ||
| `業外損益佔稅前淨利比率` | float | Non-operating profit / pre-tax profit (%) | Ratio column ||
| `財報評分 (100為滿分)` | float | Financial report score (0-100) | Ratio column ||

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee-investment/ConceptStocks/refs/heads/main/raw_column_definition.md -->

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
| `gross_profit` | float | Gross profit (USD) | API response/Derived | Revenue - COGS; derived from `total_revenue - cost_of_revenue` if GrossProfit XBRL unavailable |
| `cost_of_revenue` | float | Cost of revenue (USD) | API response | XBRL: CostOfRevenue/CostOfGoodsAndServicesSold; `null` if unavailable (e.g., ORCL after FY2011) |
| `operating_expenses` | float | Total operating expenses (USD) | API response | R&D + SG&A + other opex; `null` if unavailable |
| `research_and_development` | float | R&D expense (USD) | API response | XBRL: ResearchAndDevelopmentExpense; `null` if unavailable |
| `selling_and_marketing` | float | Sales & marketing expense (USD) | API response | XBRL: SellingAndMarketingExpense; `null` if unavailable |
| `general_and_administrative` | float | G&A expense (USD) | API response | XBRL: GeneralAndAdministrativeExpense; `null` if unavailable |
| `amortization` | float | Amortization of intangibles (USD) | API response | XBRL: AmortizationOfIntangibleAssets; `null` if unavailable |
| `operating_income` | float | Operating income (USD) | API response | EBIT |
| `other_income` | float | Non-operating income/expense (USD) | API response | Interest, FX gains/losses, etc.; `null` if unavailable |
| `income_before_tax` | float | Income before tax (USD) | API response | `null` if unavailable |
| `tax` | float | Income tax expense (USD) | Derived/API | `income_before_tax - net_income`; positive = expense |
| `net_income` | float | Net income (USD) | API response | Bottom-line profit |
| `eps` | float | Earnings per share | API response | Diluted EPS |
| `rpo` | float | Remaining Performance Obligations (USD) | API response | XBRL: RevenueRemainingPerformanceObligation; contracted future revenue; `null` if unavailable |
| `gross_margin` | float | Gross margin | Derived | `gross_profit / total_revenue` |
| `operating_margin` | float | Operating margin | Derived | `operating_income / total_revenue` |
| `net_margin` | float | Net margin | Derived | `net_income / total_revenue` |
| `revenue_yoy_pct` | float | Revenue YoY growth rate | Derived | Decimal format (0.25 = 25%); `null` if prior year unavailable |
| `currency` | string | Currency code | API response | Always `USD` |
| `source` | string | Data source | System | `SEC`, `SEC_6K`, `AlphaVantage`, `FMP` |
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
| `revenue` | float | Segment revenue (USD) | Parsed | Raw value in USD; `null` if only % available |
| `pct_of_revenue` | float | Segment as % of total revenue | Parsed/Derived | Decimal format (0.55 = 55%); `null` if unavailable (e.g., TSM platform % from image slides) |
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

---

## raw_conceptstock_company_metadata.csv (Concept Stock Company Metadata)
**No:** 37
**Source:** Concept mapping sync (`--sync-concepts`) and maintained metadata table
**Extraction Strategy:** Store concept-to-company metadata used for ticker resolution, CIK mapping, report tracking, and README concept table generation.

### Columns

| Column | Type | Description | Source Field | Notes |
|--------|------|-------------|--------------|-------|
| `概念欄位` | string | Concept column name | System | e.g., `nVidia概念`, `TSMC概念` |
| `公司名稱` | string | Company display name | Metadata | e.g., `NVIDIA Corporation` |
| `Ticker` | string | Query ticker symbol | Metadata | US ticker or ADR preferred; can be `-` for private companies |
| `CIK` | string | SEC CIK identifier | Metadata | e.g., `0001045810`, or non-SEC marker like `香港上市` |
| `最新財報` | string | Latest released fiscal report | Metadata | e.g., `FY2026 Q3` |
| `即將發布` | string | Next expected fiscal report | Metadata | e.g., `FY2026 Q4` |
| `發布時間` | string | Expected release timing | Metadata | e.g., `2026年4月` |
| `產品區段` | string | Product segment labels | Metadata | Comma-separated labels or `-` |

> Standalone metadata file (no common metadata suffix).

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee-investment/ic.tpex.org.tw/refs/heads/main/raw_column_definition.md -->

## raw_SupplyChain_{code}.csv (Industry Chain Company List)
**No:** 40
**Source:** `https://ic.tpex.org.tw/introduce.php?ic={chain_code}` from [ic.tpex.org.tw](https://github.com/wenchiehlee-investment/ic.tpex.org.tw)
**Extraction Strategy:** Scrape company lists from each industry chain page, including Taiwan stocks and foreign companies.

### Available Chain Codes:
| Code | Name |
|------|------|
| F000 | 電腦及週邊設備 |
| I000 | 通信網路 |
| 5300 | 人工智慧 |
| 5800 | 運動科技 |
| D000 | 半導體 |
| U000 | 金融 |
| T000 | 交通運輸及航運 |
| B000 | 休閒娛樂 |
| R000 | 軟體服務 |
| C100 | 製藥 |
| 5500 | 資通訊安全 |
| V000 | 貿易百貨 |
| R300 | 電子商務 |
| 5200 | 金融科技 |
| L000 | 印刷電路板 |
| C200 | 醫療器材 |
| M000 | 食品 |
| X000 | 其他 |
| 6000 | 自動化 |
| G000 | 平面顯示器 |
| P000 | 電機機械 |

### Column Definitions:

| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `位置` | **Column 1** | string | Supply chain position | `上游`, `中游`, `下游` |
| `子分類` | **Column 2** | string | Subcategory name | `IP設計`, `晶圓代工` |
| `代號` | **Column 3** | string | Stock code (Taiwan or foreign) | `2330`, `ARM`, `` (empty for private) |
| `名稱` | **Column 4** | string | Company name | `台積電`, `安謀` |

### Notes:
- Taiwan stocks have numeric codes (e.g., `2330`)
- Foreign companies use stock symbols from `raw_SupplyChain-non-TWSE-TPEX.csv` (e.g., `ARM`, `NVDA`)
- Private or unlisted companies have empty `代號`

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee-investment/ic.tpex.org.tw/refs/heads/main/raw_column_definition.md -->

## raw_SupplyChainMap.csv (Watchlist Company Supply Chain Map)
**No:** 41
**Source:** Derived from `raw_SupplyChain_{code}.csv` files from [ic.tpex.org.tw](https://github.com/wenchiehlee-investment/ic.tpex.org.tw)
**Extraction Strategy:** Map watchlist companies to their industry chains with upstream/downstream relationships.

### Column Definitions:

| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `代號` | **Column 1** | string | Taiwan stock code | `2330` |
| `名稱` | **Column 2** | string | Company name | `台積電` |
| `產業鏈代碼` | **Column 3** | string | Industry chain code | `D000` |
| `產業鏈名稱` | **Column 4** | string | Industry chain name | `半導體` |
| `位置` | **Column 5** | string | Position(s) in chain | `上游`, `中游/下游` |
| `子分類` | **Column 6** | string | Subcategory(ies) | `晶圓代工;先進封裝` |
| `上游公司` | **Column 7** | string | Upstream companies | `2454\|聯發科;3034\|聯詠` |
| `下游公司` | **Column 8** | string | Downstream companies | `2317\|鴻海;2382\|廣達` |

### Notes:
- Multiple positions separated by `/`
- Multiple subcategories separated by `;`
- Upstream/downstream companies formatted as `代號|名稱` pairs, separated by `;`
- Limited to 20 companies per direction

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee-investment/ic.tpex.org.tw/refs/heads/main/raw_column_definition.md -->

## raw_SupplyChain-non-TWSE-TPEX.csv (Foreign Company Stock Symbol Mapping)
**No:** 42
**Source:** Manual mapping + `KNOWN_MAPPINGS` in `UpdateNonTWSE.py` from [ic.tpex.org.tw](https://github.com/wenchiehlee-investment/ic.tpex.org.tw)
**Extraction Strategy:** Extract foreign company names from supply chain data, map to stock symbols.

### Column Definitions:

| Column | Position | Type | Description | Example |
|--------|----------|------|-------------|---------|
| `名稱` | **Column 1** | string | Company name (Chinese or English) | `安謀`, `NVIDIA` |
| `股票代號` | **Column 2** | string | Stock symbol | `ARM`, `NVDA`, `` (empty if private) |
| `交易所` | **Column 3** | string | Exchange code | `NASDAQ`, `NYSE`, `TSE`, `KRX`, `Private` |

### Exchange Codes:
| Code | Description |
|------|-------------|
| NASDAQ | US NASDAQ |
| NYSE | US New York Stock Exchange |
| OTC | US Over-the-Counter |
| TSE | Tokyo Stock Exchange (Japan) |
| KRX | Korea Exchange |
| HKEX | Hong Kong Stock Exchange |
| SSE | Shanghai Stock Exchange |
| SZSE | Shenzhen Stock Exchange |
| Private | Private company (not publicly traded) |
| Acquired | Company has been acquired |

### Notes:
- Empty `股票代號` indicates private or unlisted company
- Mapping maintained in `KNOWN_MAPPINGS` dictionary in `UpdateNonTWSE.py`

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee-investment/Python-Actions.GoodInfo.CompanyInfo/refs/heads/main/raw_column_definition.md -->

## raw_companyinfo.csv (Company Industry & Market Classification)
**No:** 50
**Source:** `data/stage1_raw/raw_companyinfo.csv` from [Python-Actions.GoodInfo.CompanyInfo](https://github.com/wenchiehlee-investment/Python-Actions.GoodInfo.CompanyInfo)
**Data Sources:**
- **TWSE ISIN System:** https://isin.twse.com.tw/isin/C_public.jsp (Market & Industry Classification)
- **GoodInfo.tw:** Company business details, concepts, and group information (via Selenium scraping)

**Purpose:** Provides official market classification, industry categorization, ETF weightings, and business descriptions for Taiwan stocks across all markets (TWSE, TPEX, Emerging, Public).

### Data Collection Process:
1. **Official Market Data:** Scrapes TWSE ISIN system using Modes 1, 2, 4, and 5
2. **ETF Weightings:** Fetches portfolio weights for ETF 0050, 0056, 00878, and 00919 from MoneyDJ
3. **Business Details:** Uses Selenium with headless Chrome to bypass GoodInfo anti-scraping
4. **Encoding Handling:** Explicitly handles Big5 encoding from TWSE ISIN website

### Column Definitions:

| Column | Description | Source |
| :--- | :--- | :--- |
| `代號` | Taiwan Stock ID (e.g., 2330) | Local Input / TWSE ISIN |
| `名稱` | Company Name | Local Input / TWSE ISIN |
| `市場別` | Market Type (上市, 上櫃, 興櫃, 公開發行) | TWSE ISIN |
| `產業別` | Industry Category | TWSE ISIN |
| `市值` | Market Capitalization (兆/億) | GoodInfo (Summary Table) |
| `市值佔大盤比重` | Weight in TAIEX Index (%) | TAIFEX Futures QA Detail |
| `ETF_0050_權重` | Weight in Yuanta/P-shares Taiwan Top 50 ETF (%) | MoneyDJ constituent data |
| `ETF_0056_權重` | Weight in Yuanta/P-shares Taiwan Dividend Plus ETF (%) | MoneyDJ constituent data |
| `ETF_00878_權重` | Weight in Cathay MSCI Taiwan ESG Sustainability High Dividend Yield ETF (%) | MoneyDJ constituent data |
| `ETF_00919_權重` | Weight in Capital Taiwan High Dividend ETF (%) | MoneyDJ constituent data |
| `主要業務` | Detailed description of the company's main operations | GoodInfo |
| `TSMC概念` | Mark "1" if part of TSMC supply chain/concept | GoodInfo / Gemini AI Analysis |
| `nVidia概念` | Mark "1" if part of Nvidia supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Google概念` | Mark "1" if part of Google supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Amazon概念` | Mark "1" if part of Amazon supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Meta概念` | Mark "1" if part of Meta supply chain/concept | GoodInfo / Gemini AI Analysis |
| `OpenAI概念` | Mark "1" if part of OpenAI supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Microsoft概念` | Mark "1" if part of Microsoft supply chain/concept | GoodInfo / Gemini AI Analysis |
| `AMD概念` | Mark "1" if part of AMD supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Apple概念` | Mark "1" if part of Apple supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Oracle概念` | Mark "1" if part of Oracle supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Micro概念` | Mark "1" if part of Micron Technology supply chain/concept | GoodInfo / Gemini AI Analysis |
| `SanDisk概念` | Mark "1" if part of SanDisk supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Qualcomm概念` | Mark "1" if part of Qualcomm supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Lenovo概念` | Mark "1" if part of Lenovo supply chain/concept | GoodInfo / Gemini AI Analysis |
| `Dell概念` | Mark "1" if part of Dell supply chain/concept | GoodInfo / Gemini AI Analysis |
| `HP概念` | Mark "1" if part of HP supply chain/concept | GoodInfo / Gemini AI Analysis |
| `相關集團` | Name of the business group the company belongs to | GoodInfo (Group List mapping) |

### Market Type Values:
- `上市` - TWSE Listed (Stock Exchange Main Board)
- `上櫃` - TPEX OTC (Over-the-Counter)
- `興櫃` - Emerging Stock Board
- `公開發行` - Public Companies (not yet listed)
- `上市臺灣創新板` - TWSE Taiwan Innovation Board

### Industry Categories (Examples):
Common industry classifications include:
- `半導體業` - Semiconductor Industry
- `電子零組件業` - Electronic Components
- `電腦及週邊設備業` - Computer & Peripherals
- `通信網路業` - Communications & Networking
- `其他電子業` - Other Electronics
- `資訊服務業` - Information Services
- `電子通路業` - Electronic Distribution
- `數位雲端` - Digital Cloud
- `光電業` - Optoelectronics
- `運動休閒` - Sports & Leisure
- `航運業` - Shipping

### Data Quality Notes:
1. **Market & Industry:** 100% reliable (official TWSE ISIN data)
2. **ETF Weightings:** Dynamically fetched from MoneyDJ for ETFs 0050, 0056, 00878, and 00919 (reflects current portfolio holdings)
3. **Business Details:** Best-effort scraping (may be empty if GoodInfo blocks or no data)
4. **Priority:** If stock exists in multiple markets: TWSE > TPEX > Emerging > Public
5. **Performance:** Selenium scraping adds 5-10 seconds per stock
6. **Empty Values:** Some columns may be empty if data unavailable or not applicable

### Usage in Analysis Pipeline:
- **Stage 0 (Pre-filtering):** Used to filter stocks by market or industry
- **Stage 1-2:** Can be merged with other data sources for enrichment
- **Stage 3-6:** Industry classification for peer comparison and sector analysis
- **Reporting:** Display market type and industry in stock dashboards

### File Characteristics:
- **No metadata columns:** Unlike other raw files, this contains only data columns (no file_type, timestamps, etc.)
- **Standalone file:** Not generated by Stage 1 pipeline, maintained separately
- **Update frequency:** Manual/scheduled updates via FetchCompanyInfo.py script
- **Format:** Standard CSV with UTF-8 encoding

---

<!-- source: https://raw.githubusercontent.com/wenchiehlee/GoogleSearch.Factset/refs/heads/main/raw_column_definition.md -->

## factset_detailed_report_latest.csv (FactSet Analyst Consensus Summary)
**No:** 51
**Source:** `data/stage1_raw/factset_detailed_report_latest.csv`
**Data Source:** FactSet via GoogleSearch.Factset pipeline
**Update Frequency:** Daily automated updates
**Extraction Strategy:** Pre-aggregated summary data from FactSet analyst consensus reports

### Data Characteristics:
- **Coverage:** Portfolio stocks with available FactSet analyst coverage
- **Analyst Consensus:** EPS estimates and target prices from multiple analysts
- **Multi-year Projections:** N/N+1/N+2/N+3 year EPS & Revenue forecasts (typically 3-4 years)
- **Quality Scoring:** Automated quality assessment based on data completeness and analyst coverage
- **Markdown Integration:** Links to detailed analyst reports stored in GitHub

- **Dynamic Year Notation:** Column names use actual calendar years extracted from the report header (Dynamic Year Detection)
  - **3-Year Window:** Typically 2025-2027 (for 2025 reports) or 2026-2028 (for 2026 reports).
  - **4-Year Window:** Some reports provide a full 2025-2028 range.
  - **Logic:** The system automatically maps data to the correct calendar year columns (2025, 2026, 2027, 2028) based on report headers.

  - N year always matches the year in MD日期

### Column Definitions:

| Column | Type | Description | Source | Notes |
|--------|------|-------------|--------|-------|
| `代號` | string | 4-digit stock code | FactSet | Primary key |
| `名稱` | string | Company name in Traditional Chinese | FactSet | Display name |
| `股票代號` | string | Full stock code with market suffix | FactSet | Format: `{code}-TW` (e.g., `2357-TW`) |
| `MD最舊日期` | date | Oldest markdown report date | Metadata | Format: `YYYY-MM-DD` |
| `MD最新日期` | date | Most recent markdown report date | Metadata | Format: `YYYY-MM-DD` |
| `MD資料筆數` | int | Total number of markdown reports available | Metadata | Count of historical reports |
| `分析師數量` | int | Number of analysts covering this stock | FactSet | Higher = better coverage |
| `目標價` | float | Analyst consensus target price (NT$) | FactSet | May be empty if no consensus |
| `2025EPS最高值` | float | EPS highest estimate (N) | FactSet | Available if MD日期=2025 |
| `2025EPS最低值` | float | EPS lowest estimate (N) | FactSet | Available if MD日期=2025 |
| `2025EPS平均值` | float | EPS average estimate (N) | FactSet | Available if MD日期=2025 |
| `2026EPS最高值` | float | EPS highest estimate (N+1 or N) | FactSet | N+1 (2025 report) / N (2026 report) |
| `2026EPS最低值` | float | EPS lowest estimate (N+1 or N) | FactSet | Bear case scenario N+1 (2025 report) / N (2026 report)|
| `2026EPS平均值` | float | EPS average estimate (N+1 or N) | FactSet | Consensus estimate N+1 (2025 report) / N (2026 report)|
| `2027EPS最高值` | float | EPS highest estimate (N+2 or N+1) | FactSet | N+2 (2025 report) / N+1 (2026 report) |
| `2027EPS最低值` | float | EPS lowest estimate (N+2 or N+1) | FactSet | Bear case scenario N+2 (2025 report) / N+1 (2026 report)|
| `2027EPS平均值` | float | EPS average estimate (N+2 or N+1) | FactSet | Consensus estimate N+2 (2025 report) / N+1 (2026 report)|
| `2028EPS最高值` | float | EPS highest estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2028EPS最低值` | float | EPS lowest estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2028EPS平均值` | float | EPS average estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2025營收最高值` | float | Revenue highest estimate (N) | FactSet | Available if MD日期=2025 |
| `2025營收最低值` | float | Revenue lowest estimate (N) | FactSet | Available if MD日期=2025 |
| `2025營收平均值` | float | Revenue average estimate (N) | FactSet | Available if MD日期=2025 |
| `2025營收中位數` | float | Revenue median estimate (N) | FactSet | Available if MD日期=2025 |
| `2026營收最高值` | float | Revenue highest estimate (N+1 or N) | FactSet | N+1 (2025 report) / N (2026 report) |
| `2026營收最低值` | float | Revenue lowest estimate (N+1 or N) | FactSet | Bear case scenario |
| `2026營收平均值` | float | Revenue average estimate (N+1 or N) | FactSet | Consensus estimate |
| `2026營收中位數` | float | Revenue median estimate (N+1 or N) | FactSet | Median consensus |
| `2027營收最高值` | float | Revenue highest estimate (N+2 or N+1) | FactSet | N+2 (2025 report) / N+1 (2026 report) |
| `2027營收最低值` | float | Revenue lowest estimate (N+2 or N+1) | FactSet | Bear case scenario |
| `2027營收平均值` | float | Revenue average estimate (N+2 or N+1) | FactSet | Consensus estimate |
| `2027營收中位數` | float | Revenue median estimate (N+2 or N+1) | FactSet | Median consensus |
| `2028營收最高值` | float | Revenue highest estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2028營收最低值` | float | Revenue lowest estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2028營收平均值` | float | Revenue average estimate (N+2) | FactSet | Available if MD日期=2026 |
| `2028營收中位數` | float | Revenue median estimate (N+2) | FactSet | Available if MD日期=2026 |
| `品質評分` | float | Data quality score (0.0-10.0) | Calculated | Based on completeness & coverage |
| `狀態` | string | Quality status with emoji indicator | Calculated | `🟢 優秀`, `🟡 良好`, `🟠 普通`, `🔴 不足` |
| `MD日期` | date | Primary markdown report reference date | Metadata | Format: `YYYY-MM-DD` |
| `MD File` | string | URL to detailed analyst report markdown | GitHub | Full URL to raw markdown file |
| `搜尋日期` | datetime | When data was searched/fetched | Metadata | Format: `YYYY-MM-DD HH:MM:SS` |
| `處理日期` | datetime | When data was processed/aggregated | Metadata | Format: `YYYY-MM-DD HH:MM:SS` |

### Quality Status Interpretation:
- **🟢 優秀 (Excellent):** Score ≥ 9.0 - Comprehensive analyst coverage with complete data
- **🟡 良好 (Good):** Score 7.0-8.9 - Solid coverage with most data available
- **🟠 普通 (Fair):** Score 5.0-6.9 - Limited coverage or partial data
- **🔴 不足 (Insufficient):** Score < 5.0 - Minimal coverage or incomplete data

### Data Completeness Notes:
1. **EPS Estimates:** May be empty if no analyst consensus available
2. **Target Price:** Only present when analysts provide price targets
3. **Analyst Count:** Zero indicates no active analyst coverage
4. **Multi-year Forecasts:** 2026-2028 data may be sparse for some stocks
5. **MD Reports:** Historical reports provide detailed analyst commentary

### Usage in Analysis Pipeline:
- **Dividend Forecasting:** Compare FactSet EPS estimates with TTM-based predictions
- **Valuation Analysis:** Use target prices for forward P/E calculations
- **Analyst Sentiment:** Track changes in consensus estimates over time
- **Coverage Quality:** Filter stocks by analyst coverage depth
- **Report Integration:** Link to detailed markdown reports for qualitative analysis

### Cross-Reference Integration:
- **Type 7 (Quarterly Performance):** Compare actual EPS vs FactSet estimates
- **Dividend Reports:** Validate scenario analysis using analyst consensus
- **PE Forward Return Analysis:** Use forward EPS estimates for valuation metrics

### File Characteristics:
- **No standard metadata columns:** Does not follow stock_code/company_name/file_type pattern
- **Standalone summary:** Pre-aggregated portfolio-level data
- **Daily updates:** Automated refresh from GoogleSearch.Factset pipeline
- **UTF-8 BOM encoding:** Starts with `﻿` BOM character
- **External dependency:** Requires GoogleSearch.Factset repository synchronization

### Example Use Cases:
1. **Earnings Surprise Analysis:** Compare actual Q4 EPS vs FactSet consensus
2. **Scenario Validation:** Verify dividend forecast scenarios align with analyst expectations
3. **Coverage Screening:** Identify stocks with strong analyst following (分析師數量 > 15)
4. **Target Price Monitoring:** Track price appreciation potential vs current market price
5. **Forward Yield Estimation:** Calculate forward dividend yield using consensus EPS

---

## raw_weekly_k_chart_flow.csv (Weekly K-Line Chart Flow)**No:**17
**Source:** `ShowWeeklyK_ChartFlow/*.xls*`
**GoodInfo Page:** https://goodinfo.tw/tw/ShowK_ChartFlow.asp?STOCK_ID={stock_id}&CHT_CAT=WEEK&PRICE_ADJ=F&SCROLL2Y=500
**Extraction Strategy:** Weekly K-Line chart data with capital flow analysis (5-year history). Provides an alternative weekly view focusing on capital flow trends.

### Actual Excel Structure Analysis (Projected):
- **Column A:** 交易週別 (Trading Week)
- **Columns B-E:** OHLC Prices (開盤, 最高, 最低, 收盤)
- **Columns F-H:** Price Change Metrics (漲跌, 漲跌%, 振幅%)
- **Columns I-J:** Volume Metrics (成交張數, 成交金額)
- **Columns K-N:** Capital/Institutional Flow (法人買賣超, 外資, 投信, 自營, etc.) - *Exact columns to be verified against file*

### Column Definitions (Provisional):

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `交易_週別` | string | Trading week identifier (YYWxx format) | Column A |Empty rows|
| `開盤_價格_元` | float | Weekly opening price (NT$) | Column B ||
| `最高_價格_元` | float | Weekly highest price (NT$) | Column C ||
| `最低_價格_元` | float | Weekly lowest price (NT$) | Column D ||
| `收盤_價格_元` | float | Weekly closing price (NT$) | Column E ||
| `漲跌_價格_元` | float | Weekly price change (NT$) | Column F ||
| `漲跌_pct` | float | Weekly price change percentage | Column G ||
| `振幅_pct` | float | Weekly price range percentage | Column H ||
| `成交_張數` | int | Weekly trading volume (lots) | Column I ||
| `成交_金額_億` | float | Weekly turnover amount (hundred million NT$) | Column J ||
| `法人_合計_千張` | float | Total institutional net buying (thousands) | Column K ||
| `外資_淨買超_千張` | float | Foreign investor net buying (thousands) | Column L ||
| `投信_淨買超_千張` | float | Investment trust net buying (thousands) | Column M ||
| `自營_淨買超_千張` | float | Proprietary trading net buying (thousands) | Column N ||

### File Structure Notes:
- **Weekly Frequency:** 5-year history matching Type 8 and Type 14
- **Capital Flow Focus:** Designed to track money flow alongside price action
- **Redundancy Note:** May overlap with Type 11 (Weekly Trading Data); useful for cross-validation or if Type 11 is unavailable.

---

## raw_daily_k_chart_flow.csv (Daily K-Line Chart Flow)
**No:**18
**Source:** `ShowDailyK_ChartFlow/*.xls*`
**GoodInfo Page:** https://goodinfo.tw/tw/ShowK_ChartFlow.asp?STOCK_ID={stock_id}&CHT_CAT=DATE&PRICE_ADJ=F&SCROLL2Y=500
**Extraction Strategy:** Daily K-Line chart data with capital flow analysis (1-year history). **Crucial for daily correlation and volatility analysis.**

### Actual Excel Structure Analysis:
- **Column A:** 交易日期 (source usually in `MM/DD`, no explicit year in table body)
- **Columns B-E:** OHLC Prices (開盤, 最高, 最低, 收盤)
- **Columns F-H:** Price Change Metrics
- **Columns I-J:** Volume Metrics
- **Columns K-N:** Daily Institutional Flow

### Column Definitions:

| Column | Type | Description | Excel Source |Excluded|
|--------|------|-------------|--------------|--|
| `交易_日期` | string | Trading date normalized to `YYYY-MM-DD` | Column A (normalized from source `MM/DD`) |Empty rows|
| `開盤_價格_元` | float | Daily opening price (NT$) | Column B ||
| `最高_價格_元` | float | Daily highest price (NT$) | Column C ||
| `最低_價格_元` | float | Daily lowest price (NT$) | Column D ||
| `收盤_價格_元` | float | Daily closing price (NT$) | Column E ||
| `漲跌_價格_元` | float | Daily price change (NT$) | Column F ||
| `漲跌_pct` | float | Daily price change percentage | Column G ||
| `振幅_pct` | float | Daily price range percentage | Column H ||
| `成交_張數` | int | Daily trading volume (lots) | Column I ||
| `成交_金額_億` | float | Daily turnover amount (hundred million NT$) | Column J ||
| `法人_合計_千張` | float | Total institutional net buying (thousands) | Column K ||
| `外資_淨買超_千張` | float | Foreign investor net buying (thousands) | Column L ||
| `投信_淨買超_千張` | float | Investment trust net buying (thousands) | Column M ||
| `自營_淨買超_千張` | float | Proprietary trading net buying (thousands) | Column N ||

### Date Normalization Rule (`交易_日期`):
- Source table date is typically `MM/DD` (without year).
- Stage 1 uses `download_timestamp` year as anchor year.
- Rows are processed in source order (newest -> oldest).
- If parsed `MM/DD` would become later than previous row date, year is decremented (year rollover handling).
- Final output is standardized to `YYYY-MM-DD`.

### File Structure Notes:
- **Daily Frequency:** 1-year history granularity
- **High Value:** This is the **primary source for Daily OHLC** needed for 30-day correlation matrices and short-term technical analysis.
- **Capital Flow:** Allows correlation of daily price moves with institutional money flow.

### Usage in Analysis Pipeline:
- **Correlation Matrix:** Source for calculating 30-day rolling correlations (Reference: Investopedia Article)
- **Volatility Analysis:** Source for daily ATR and standard deviation calculations
- **Momentum Strategy:** Detection of daily price/volume breakouts



This approach preserves the semantic meaning while handling complex Excel structures and provides comprehensive coverage of all 12 GoodInfo.tw data types with accurate column definitions based on actual file structures.
