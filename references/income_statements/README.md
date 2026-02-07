# Income Statement Reference Images

> Last verified: 2026-02-07

This directory contains quarterly earnings reference images for cross-referencing with our annual concept stock data.

## Image Index

| # | File | Company | Period | Data Match | Doc |
|---|------|---------|--------|-----------|-----|
| 1 | `nvidia2026Q1.jpg` | NVIDIA (NVDA) | Q1 FY2026 | CONSISTENT | [nvidia2026Q1.md](nvidia2026Q1.md) |
| 2 | `29032a0a-..._2741x1540.png` | Oracle (ORCL) | Q2 FY2026 | CONSISTENT | [oracle2026Q2.md](oracle2026Q2.md) |
| 3 | `625343054_...n.jpg` | Qualcomm (QCOM) | 1Q FY2026 | N/A | [qualcomm2026Q1.md](qualcomm2026Q1.md) |
| 4 | `MS-2026Q2.jpg` | Microsoft (MSFT) | Q2 FY2026 | CONSISTENT | [microsoft2026Q2.md](microsoft2026Q2.md) |
| 5 | `MS-2026Q2-1.jpg` | Microsoft (MSFT) | Q2 FY2026 | CONSISTENT | [microsoft2026Q2.md](microsoft2026Q2.md) |
| 6 | `apple2026Q1.webp` | Apple (AAPL) | Q1 FY2026 | CONSISTENT | [apple2026Q1.md](apple2026Q1.md) |
| 7 | `Oracle-revenue.webp` | Oracle (ORCL) | FY23-FY26 | Q1-Q3 OK, Q4 ISSUE | [oracle-revenue-breakdown.md](oracle-revenue-breakdown.md) |
| 8 | `Oracle-2023Q4.webp` | Oracle (ORCL) | Q4 FY2023 | Q4 MISMATCH | [oracle2023Q4.md](oracle2023Q4.md) |
| 9 | `Oracle forecast revenue.webp` | Oracle (ORCL) | FY25-FY30 | FORECAST | [oracle-oci-forecast.md](oracle-oci-forecast.md) |

## Summary of Comparison

Our data contains **annual (full fiscal year)** figures, while these reference images show **single quarter** results. Key findings:

### NVDA - NVIDIA Q1 FY26
- Image: Revenue ~$44.1B, Data Center ~$39.2B
- Our FY2025 Q avg: Revenue $32.6B, Data Center $28.8B
- **+35% growth**, driven by AI/Data Center demand

### ORCL - Oracle Q2 FY26
- Image: Revenue $16.1B (Cloud $8.0B + Software $5.9B + HW $0.8B + Services $1.4B)
- Our FY2025 Q avg: $14.4B (Cloud and license $12.3B + HW $0.7B + Services $1.3B)
- **+12% growth**, Oracle Cloud Infrastructure +46% YoY

### QCOM - Qualcomm 1Q FY26
- Image: Revenue $12.25B, EPS $3.50
- **NOT in our 10 concept stock companies** - no comparison available

### MSFT - Microsoft Q2 FY26
- Image: Revenue $81.3B (Server $30.9B, M365 $24.5B, Gaming $6.0B, etc.)
- Our FY2025 Q avg: $70.4B (Server $24.6B, M365 $22.0B, Gaming $5.9B, etc.)
- **+15% growth**, Azure/Server +31% YoY is the growth engine

### AAPL - Apple Q1 FY26 (Holiday Quarter)
- Image: Revenue $143.8B (iPhone $85.3B, Services $30.0B, etc.)
- Our FY2025 Q avg: $104.1B (iPhone $52.4B, Services $27.3B, etc.)
- **Mac quarterly average exactly matches** ($8.4B = $8.4B)
- Q1 is Apple's holiday quarter, iPhone revenue 63% above quarterly average

## Quarterly Data Verification (SEC EDGAR 10-Q)

After implementing quarterly data support (`--period quarterly`), we now have **exact matches** against the reference images:

| Company | Period | Our Revenue | Reference Revenue | Match |
|---------|--------|-------------|-------------------|-------|
| MSFT | FY2026 Q2 | $81.3B | $81.3B | EXACT |
| AAPL | FY2026 Q1 | $143.8B | $143.8B | EXACT |
| NVDA | FY2026 Q1 | $44.1B | ~$44.1B | EXACT |
| ORCL | FY2026 Q2 | $16.1B | $16.1B | EXACT |

Net income also matches: MSFT $38.5B, AAPL $42.1B, ORCL $6.1B (all exact).

## Conclusion

All 4 matched companies (NVDA, ORCL, MSFT, AAPL) show data **consistent** with both annual and quarterly figures:
- Quarterly revenue from SEC EDGAR 10-Q filings match reference images exactly
- Segment structures and proportions align correctly
- Growth trends are reasonable (all trending above FY2025 averages)
- QCOM is not in our concept stock list (no comparison possible)

## Oracle Data Quality Issue (2026-02-07)

### Problem: Q4 Calculation Mismatch

After fixing the 10-Q fiscal quarter determination (Oracle Q1 was being mislabeled as Q2), we discovered a data quality issue:

| Source | FY2023 Cloud services |
|--------|----------------------|
| Our annual data | $39.4B |
| Image quarterly sum | $35.3B |
| **Difference** | **$4.1B** |

This causes our calculated Q4 to be inflated:
- Our calculated Q4 FY2023: $13.4B
- Image shows Q4 FY2023: $9.3B

### Root Cause

The 10-K HTML parser may have a fiscal year offset issue. The $39.4B labeled as FY2023 might actually be FY2024 data.

### Current Status

- **Q1-Q3 quarterly data**: FIXED and CONSISTENT with images
- **Q4 calculated data**: INCORRECT due to annual data mismatch
- **Investigation needed**: Review 10-K HTML parsing for fiscal year determination
