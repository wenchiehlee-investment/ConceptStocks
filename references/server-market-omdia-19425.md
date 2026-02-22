# 2024 Server Market – Omdia

> Source: Omdia (omdia.com)
> Title: "Server market will be even more competitive in 2025"
> Image: `server-market-omdia-19425.jpg`
> Period: 2024 Server Capex

## Total Market

| Metric | Value |
|--------|-------|
| 2024 Server Capex | **$229bn** |
| Top 10 vendors share | >60% of market demand |
| Top 10 users share | ~60% of investment |

---

## Top 10 Compute Vendors (Server Manufacturers / ODMs)

> 圖表標題為 "Top 10"，但底部有並列同分，實際顯示 **11 家**。
> Lenovo 與 ZT Systems 同為 $10B（並列 #8），Wiwynn 與 Inventec 同為 $8B（並列 #10）。

| Rank | Vendor | 2024 Revenue | Tracked? |
|------|--------|-------------|---------|
| 1 | Foxconn | $29bn | ❌ (台股 2317.TW) |
| 2 | Dell | $25bn | ✅ **DELL** |
| 3 | Supermicro | $19bn | ❌ (SMCI, 未追蹤) |
| 4 | IEIT Systems | $16bn | ❌ (浪潮/中國) |
| 5 | QCT (Quanta Cloud Technology) | $15bn | ❌ (廣達子公司, 台股 3006.TW) |
| 6 | Hewlett Packard Enterprise | $13bn | ❌ (HPE ≠ HPQ; 2015年分拆) |
| 7 | xFusion / Huawei | $11bn | ❌ (中國，xFusion 為華為子品牌) |
| 8= | Lenovo | $10bn | ❌ (港股 0992.HK) |
| 8= | ZT Systems | $10bn | ❌ (私人公司，已被 Microsoft 收購 2024) |
| 10= | Wiwynn | $8bn | ❌ (台股 6669.TW，廣達旗下) |
| 10= | Inventec | $8bn | ❌ (台股 2356.TW) |
| – | Other | $86bn | – |

> **注意**: 我們追蹤的是 **HPQ**（HP Inc. — 消費性電腦+印表機），**非 HPE**（Hewlett Packard Enterprise — 伺服器/資料中心硬體）。兩者於 2015 年分拆為獨立公司。
> 在 11 家 Vendor 中，**DELL** 是唯一被我們追蹤的公司。

---

## Top 10 Compute Users (Hyperscalers / Cloud Buyers)

> 圖表標題為 "Top 10"，但底部有三家並列 $3B，實際顯示 **11 家**。
> Apple、CoreWeave、Alibaba 同為 $3B（並列 #9）。

| Rank | User | 2024 Server Capex | Tracked? | Our Symbol |
|------|------|------------------|---------|-----------|
| 1 | Microsoft | $31bn | ✅ | **MSFT** |
| 2 | Amazon | $26bn | ✅ | **AMZN** |
| 3 | Google | $22bn | ✅ | **GOOGL** |
| 4 | Meta | $20bn | ✅ | **META** |
| 5 | ByteDance | $8bn | ❌ (私人公司) |
| 6 | X (Twitter/xAI) | $7bn | ❌ (私人公司) |
| 7 | Tencent | $6bn | ❌ (港股 0700.HK) |
| 8 | Oracle | $5bn | ✅ | **ORCL** |
| 9= | Apple | $3bn | ✅ | **AAPL** |
| 9= | CoreWeave | $3bn | ❌ (NYSE: CRWV，2025年新上市) |
| 9= | Alibaba | $3bn | ❌ (NYSE: BABA，未追蹤) |
| – | Other | $98bn | – |

---

## Cross-Check with Our CSV Data

> **重要說明**: Omdia 圖表的兩側指標不同：
> - **Vendor 側** ($25bn Dell 等) = 伺服器**銷售收入**（Revenue）
> - **User 側** ($31bn Microsoft 等) = 伺服器**資本支出**（Capex/購買支出）
> 我們的 CSV 追蹤 **Revenue**，無直接 Capex 欄位。

---

### DELL（Vendor 側 — 可直接比對 ✅）

| 指標 | Omdia CY2024 | 我們的資料 | 差異 | 說明 |
|------|------------:|----------:|------|------|
| 伺服器銷售額 | $25B | FY2025 "Servers and networking" **$27.1B** | +8% | FY2025 = Feb 2024–Jan 2025，幾乎涵蓋 CY2024；Omdia 為估計值 |

**DELL Servers and networking 歷年趨勢（我們的資料）：**

| FY | Revenue | YoY |
|----|--------:|-----|
| FY2019 | $17.1B | — |
| FY2020 | $16.6B | -3% |
| FY2021 | $16.5B | -1% |
| FY2022 | $17.9B | +8% |
| FY2023 | $20.4B | +14% |
| FY2024 | $17.6B | **-14%** (AI 伺服器轉型前的谷底) |
| **FY2025** | **$27.1B** | **+54%** (AI 伺服器爆發) |

> FY2024 下滑是因為客戶暫停採購傳統伺服器等待 AI 伺服器世代；FY2025 的 +54% 反映 NVIDIA GPU 伺服器大量出貨。
> DELL ISG 季度資料（8-K）：FY2025 Q3 $11.4B、Q4 $11.4B、FY2026 Q1 $10.3B、Q2 $16.8B（AI 加速器需求繼續上揚）

---

### User 側（Capex ≠ Revenue，無法直接比對）

我們 CSV 沒有 Capex 欄位。以各公司**雲端/AI 相關 Revenue** 作為間接佐證：

| Symbol | Omdia Server Capex (CY2024) | 我們的 FY2024 雲端段 Revenue | Capex/Revenue 比 | 趨勢 |
|--------|----------------------------:|----------------------------:|-----------------|------|
| MSFT | $31B | Intelligent Cloud **$105B**（4Q FY2024 加總） | ~30% | IC: $24B→$26B→$27B→$29B（逐季成長） |
| AMZN | $26B | AWS **$108B** | ~24% | AWS 持續高成長 |
| GOOGL | $22B | Google Cloud **$43B** | **~51%** | Cloud 仍在重投資期（Capex > 毛利） |
| META | $20B | Family of Apps **$164B** | ~12% | AI 基建占比相對低，但絕對值大 |
| ORCL | $5B | Cloud services ~**$19B** | ~26% | OCI 擴張中；RPO $97B 預示未來 Capex 持續 |
| AAPL | $3B | 總 Revenue $394B | <1% | 主要用於 Apple Intelligence，伺服器非核心 |

**MSFT Intelligent Cloud 季度收入（我們的資料）：**

| 季度 | IC Revenue |
|------|----------:|
| FY2024 Q1 | $24.3B |
| FY2024 Q2 | $25.9B |
| FY2024 Q3 | $26.7B |
| FY2024 Q4 | $28.5B |
| **FY2024 合計** | **$105.4B** |
| FY2025 Q1 | $24.1B |
| FY2025 Q2 | $25.5B |
| FY2025 Q3 | $26.8B |
| FY2025 Q4 | $29.9B |
| **FY2025 合計** | **$106.3B** |
| FY2026 Q1 | $30.9B |
| FY2026 Q2 | $32.9B |

---

### Key Observations

1. **DELL $27.1B ≈ Omdia $25B** ✅ — 大致吻合。FY2025 的 +54% YoY 顯示 AI 伺服器需求爆發，直接受益於超大規模廠商採購
2. **MSFT Intelligent Cloud $105B revenue → $31B server capex** — 約 30% 的 Capex-to-Revenue 比，反映 Azure 重度基建投入
3. **GOOGL ~51% Capex/Revenue 比最高** — Google Cloud 還在快速擴張期，Capex 投入幾乎與整體雲端毛利相當
4. **NVDA 不在此圖** — 屬更上游的 GPU 半導體層；Foxconn/Dell/Supermicro 等將 NVIDIA GPU 整合進伺服器後賣給超大規模廠商
5. **ZT Systems $10B** 已於 2024 年被 Microsoft 收購 — MSFT 的垂直整合動作
6. **ORCL $5B Capex + RPO $97B** — OCI 伺服器採購擴張仍在初期，未來 Capex 壓力大

### Supply Chain Hierarchy（我們追蹤公司的位置）

```
Level 1 – 晶片設計 (Fabless):   NVDA, AMD, QCOM
Level 2 – 晶片製造 (Foundry):   TSM
Level 3 – 記憶體:                MU, WDC
Level 4 – 伺服器組裝 (OEM/ODM): DELL  [HPQ* 屬消費電腦，不在此層]
Level 5 – 雲端服務/採購者:       MSFT, AMZN, GOOGL, META, ORCL, AAPL
```

---

## Data Gap Summary

| 公司 | Omdia 數據 | 我們的對應資料 | 缺口 |
|------|-----------|-------------|------|
| DELL | Server revenue $25B | Servers and networking $27.1B (FY2025) | 小差異，可接受 |
| MSFT | Server capex $31B | IC Revenue $105B | **無 Capex 欄位** |
| AMZN | Server capex $26B | AWS Revenue $108B | **無 Capex 欄位** |
| GOOGL | Server capex $22B | Cloud Revenue $43B | **無 Capex 欄位** |
| META | Server capex $20B | Revenue $165B | **無 Capex 欄位** |
| ORCL | Server capex $5B | Cloud Revenue $19B | **無 Capex 欄位** |
| AAPL | Server capex $3B | Total Revenue $394B | **無 Capex 欄位** |
