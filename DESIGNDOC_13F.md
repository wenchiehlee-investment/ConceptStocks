# ConceptStocks 13F 機構持倉追蹤功能實作計畫

## 🎯 目標 (Objective)
在 `ConceptStocks` 專案中導入美國證券交易委員會 (SEC) Form 13F-HR 機構持倉報告的自動化抓取與分析功能。這將允許我們觀察「大戶（如巴菲特、各大基金）」在多個季度中對我們所定義之「概念股」的籌碼增減趨勢。

基於您的需求，本計畫採用**高擴充彈性架構**，並支援**多季歷史趨勢**抓取。

## 📂 檔案與結構變更 (Key Files & Context)

1. **核心爬蟲擴充 (`src/external/sec_edgar_client.py`)**:
   - 新增 13F 專用方法：`get_13f_filings_index` (取得 filing 內的 `index.json`)。
   - 新增 XML 解析邏輯：利用 `xml.etree.ElementTree` 解析 `informationtable.xml` (比 HTML 更準確且標準化)。

2. **機構清單設定檔 (`src/manager_config.json` 或 CSV)**:
   - 建立獨立的設定檔來管理要追蹤的機構，方便未來擴充而無需修改程式碼。
   - 包含欄位：`ManagerName`, `CIK`, `Tags` (例如: Value, AI, Tech)。

3. **自動化資料管線 (`scripts/update_13f_holdings.py`)**:
   - 負責讀取機構清單、呼叫 SEC Client 抓取過去 N 季的 13F-HR。
   - 計算 Quarter-over-Quarter (QoQ) 的持股變化（增持、減持、新建倉、清倉）。
   - 將標的（CUSIP / 名稱）與我們的 `ConceptStocks` (NVDA, TSM 等) 進行交叉比對。

4. **輸出資料結構 (Output Data)**:
   - `raw_13f_institutional_holdings.csv`: 記錄每一季、每個機構、每一檔股票的股數 (Shares) 與市值 (Value)。
   - `raw_13f_institutional_changes.csv`: 記錄季度之間的變化量與變化比例。

## 🛠️ 實作步驟 (Implementation Steps)

### 階段一：底層通訊與 XML 解析 (SECEdgarClient)
1. 在 `SECEdgarClient` 中實作尋找 13F XML 資訊表的方法。
   - 流程：呼叫 Submissions API `->` 取得 13F-HR 的 `accessionNumber` `->` 查詢 `/Archives/edgar/data/{cik}/{accession_no_dashes}/index.json` `->` 找出檔名包含 `informationtable` 或 `infotable` 且副檔名為 `.xml` 的檔案 `->` 下載。
2. 實作 `parse_13f_xml` 方法，解析 SEC 13F XML 命名空間 (`http://www.sec.gov/edgar/document/thirteenf/informationtable`)，提取：
   - Name of Issuer (發行公司名稱)
   - Title of Class (股份類別)
   - CUSIP
   - Value (市值)
   - ShrsOrPrnAmt (股數)

### 階段二：建立機構設定檔與資料更新腳本
1. 建立設定檔 `ConceptStocks/configs/institutional_managers.csv`，初步加入數個範例（如 Berkshire Hathaway, BlackRock, Appaloosa, Renaissance Technologies）。
2. 開發 `scripts/update_13f_holdings.py`：
   - 支援 `--quarters` 參數（例如預設 4 季）。
   - 對每一個機構，逐季處理並合併資料。
   - 計算每一季的投資組合佔比 (`% of Portfolio`)。

### 階段三：歷史變化計算與概念股比對 (Trend & Concept Matching)
1. 在更新腳本中加入「歷史趨勢計算」邏輯：
   - 針對同一個機構與同一檔 CUSIP/Ticker，比較當季與前一季的股數。
   - 標記 `Action`: `New` (新建倉), `Add` (增持), `Reduce` (減持), `Sold` (清倉)。
2. 提供輔助映射，將 SEC 的 `Name of Issuer` (如 NVIDIA CORP) 或 `CUSIP` 對應回我們的 Ticker (NVDA)，以利後續與 `ConceptStocks` 儀表板整合。

### 階段四：文件與同步設定更新
1. 更新 `ConceptStocks/README.md`，說明 13F 更新腳本的用法。
2. 更新 `ConceptStocks/raw_column_definition.md` 加入新的 CSV 欄位定義。
3. （視需求）更新 GitHub Actions workflow，讓 13F 資料也能定期抓取。

## 🧪 驗證計畫 (Verification & Testing)
1. 執行單一機構測試：`python scripts/update_13f_holdings.py --manager "Berkshire" --quarters 2`。
2. 比對產出的 CSV 中 AAPL (Apple) 的股數與市值，是否與公開新聞或 SEC 網站上的實際報表一致。
3. 測試概念股標記功能：確認 NVDA, TSM 等科技股是否有被正確映射並標註為概念股。
