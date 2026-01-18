# ConceptStocks

Working space for ConceptStocks.

## What is 「概念股」 in this repo?
This repository uses the GoodInfo company dataset to tag Taiwan-listed companies by **concept themes**. In the CSV (`raw_companyinfo.csv`), a company is considered a **「概念股」** for a theme when the corresponding concept column is marked as `1` (true). The free-text column `相關概念` lists the concepts as a semicolon-separated string and mirrors these binary flags.

### Concept columns (end with 「概念」)
These columns indicate the specific concept themes tracked in the dataset:
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

### How to read the data
- If `nVidia概念 = 1`, the company is a **nVidia 概念股**.
- If `Google概念 = 1`, the company is a **Google 概念股**.
- If `相關概念` includes `Apple`, the `Apple概念` flag should be `1`.

Example (from the CSV):
```
代號: 2308
名稱: 台達電
相關概念: Nvidia;Google;Amazon;Microsoft;AMD;Apple
nVidia概念: 1, Google概念: 1, Amazon概念: 1, Microsoft概念: 1, AMD概念: 1, Apple概念: 1
```

If you add new concept columns, keep the naming pattern `X概念` and update this list.
