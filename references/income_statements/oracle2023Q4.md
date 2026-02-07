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

### Root Cause Analysis

Our Q4 calculation: `Q4 = Annual - (Q1 + Q2 + Q3)`

| Data Point | Our Value | Image Value |
|------------|-----------|-------------|
| Q1 FY2023 | $8.4B | $8.4B |
| Q2 FY2023 | $8.6B | $8.6B |
| Q3 FY2023 | $8.9B | $9.0B |
| Q4 FY2023 | $13.4B (calculated) | $9.3B |
| **Annual FY2023** | **$39.4B** | **$35.3B** |

**Issue**: Our annual FY2023 data ($39.4B) doesn't match the sum of quarterly data from the image ($35.3B). This causes Q4 to be over-calculated.

**Likely Cause**: 10-K HTML parser may have fiscal year offset - the $39.4B might actually be FY2024 data mislabeled as FY2023.

## Verification Needed

To fix this issue, need to verify:
1. What fiscal year does the $39.4B actually belong to in Oracle's 10-K?
2. Is there a 1-year offset in the 10-K table parsing logic?
