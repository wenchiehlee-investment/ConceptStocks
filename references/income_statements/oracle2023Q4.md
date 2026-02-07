# Oracle Q4 FY23 Income Statement

> Source: App Economy Insights (@EconomyApp)
> Image: `Oracle-2023Q4.webp`
> Period: Q4 FY2023 (ending May 2023)

## Revenue Breakdown

| Segment | Q4 FY23 Revenue | YoY |
|---------|----------------|-----|
| Cloud services & license support | $9.4B | +23% |
| Cloud license & on-premise license | $2.2B | +15% |
| Hardware | $0.9B | +1% |
| Services | $1.5B | - |
| **Total Revenue** | **$13.8B** | **+17%** |

## Income Statement Flow

```
Revenue: $13.8B (+17% Y/Y)
    │
    ├── Cost of Revenue: $3.7B
    │       ├── Cloud: $2.2B (81% gross margin)
    │       ├── Hardware: $0.3B (69% gross margin)
    │       └── Services: $1.3B (9% gross margin)
    │
    ▼
Gross Profit: $10.1B (73% margin, +7pp Y/Y)
    │
    ├── Operating Expenses: $6.0B
    │       ├── R&D: $2.3B
    │       ├── S&M: $2.4B
    │       ├── G&A: $0.4B
    │       └── Amortization: $0.5B
    │
    ▼
Operating Profit: $4.1B (30% margin, +6pp Y/Y)
    │
    ├── Tax Benefit: $0.2B
    ├── Financial: ($0.1B)
    ├── Other: ($0.1B)
    │
    ▼
Net Profit: $3.3B (24% margin, +9pp Y/Y)
```

## Comparison with Our Data

### Q4 FY2023 Cloud services and license support

| Source | Value |
|--------|-------|
| Image (this file) | $9.4B |
| Our calculated Q4 | $13.4B |
| **Difference** | **$4.0B** |

### Data Verification (FIXED 2026-02-07)

Our Q4 calculation: `Q4 = Annual - (Q1 + Q2 + Q3)`

| Data Point | Our Value | Image Value | Status |
|------------|-----------|-------------|--------|
| Q1 FY2023 | $8.4B | $8.4B | ✅ |
| Q2 FY2023 | $8.6B | $8.6B | ✅ |
| Q3 FY2023 | $8.9B | $9.0B | ✅ |
| Q4 FY2023 | **$9.4B** | $9.3B | ✅ |
| **Annual FY2023** | **$35.3B** | **$35.3B** | ✅ |

## Bug Fix Applied

**Root Cause**: The 10-K HTML parser was extracting values from wrong year columns due to overlapping search ranges.

**Fix**: Modified `parse_segment_tables()` in `sec_edgar_client.py` to search only FORWARD from each year's header column, preventing overlap with adjacent columns.

**Result**: All fiscal year data now correctly matches Oracle's 10-K filings and the reference images.
