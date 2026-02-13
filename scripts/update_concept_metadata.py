#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from typing import Dict, List

import requests


DEFAULT_COMPANYINFO_URL = (
    "https://raw.githubusercontent.com/"
    "wenchiehlee-investment/Python-Actions.GoodInfo.CompanyInfo/"
    "refs/heads/main/raw_companyinfo.csv"
)

OUTPUT_FIELDS = [
    "概念欄位",
    "公司名稱",
    "Ticker",
    "CIK",
    "最新財報",
    "即將發布",
    "發布時間",
    "產品區段",
]

CONCEPT_FALLBACKS: Dict[str, Dict[str, str]] = {
    "TSMC概念": {
        "公司名稱": "Taiwan Semiconductor Manufacturing Company Limited",
        "Ticker": "TSM",
        "CIK": "0001046179",
        "最新財報": "-",
        "即將發布": "-",
        "發布時間": "-",
        "產品區段": "-",
    },
    "台積電概念": {
        "公司名稱": "Taiwan Semiconductor Manufacturing Company Limited",
        "Ticker": "TSM",
        "CIK": "0001046179",
        "最新財報": "-",
        "即將發布": "-",
        "發布時間": "-",
        "產品區段": "-",
    },
}


def load_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, value = s.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate raw_conceptstock_company_metadata.csv from concept columns "
            "in raw_companyinfo.csv using Gemini API."
        )
    )
    parser.add_argument(
        "--out-dir",
        default=os.getcwd(),
        help="Output directory for raw_conceptstock_company_metadata.csv",
    )
    parser.add_argument(
        "--metadata-file",
        default="raw_conceptstock_company_metadata.csv",
        help="Metadata filename under --out-dir",
    )
    parser.add_argument(
        "--companyinfo-url",
        default=DEFAULT_COMPANYINFO_URL,
        help="Company info CSV URL",
    )
    parser.add_argument(
        "--companyinfo-path",
        default="",
        help="Optional local company info CSV path (used first if exists)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model id (e.g., gemini-2.0-flash)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.2,
        help="Seconds between Gemini calls",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Refresh all concepts from Gemini (ignore cache)",
    )
    parser.add_argument(
        "--keep-extra-concepts",
        action="store_true",
        help="Keep existing metadata rows not present in current companyinfo concept columns.",
    )
    parser.add_argument(
        "--skip-readme-update",
        action="store_true",
        help="Do not refresh README concept table after metadata write.",
    )
    return parser.parse_args()


def load_companyinfo_content(path: str, url: str) -> str:
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()

    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read().decode("utf-8-sig")
    except Exception as e:
        print(f"Error fetching company info via urllib: {e}", file=sys.stderr)
        result = subprocess.check_output(["curl", "-sSL", url])
        return result.decode("utf-8-sig")


def load_concept_columns(companyinfo_content: str) -> List[str]:
    lines = companyinfo_content.splitlines()
    reader = csv.DictReader(lines)
    fieldnames = reader.fieldnames or []
    concept_cols = [
        c for c in fieldnames if c.endswith("概念") and c != "相關概念"
    ]
    return concept_cols


def load_existing_metadata(path: str) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(path):
        return {}

    existing: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            concept = (row.get("概念欄位") or "").strip()
            if not concept:
                continue
            existing[concept] = {k: (row.get(k) or "").strip() for k in OUTPUT_FIELDS}
    return existing


def has_anchor_fields(row: Dict[str, str]) -> bool:
    company = (row.get("公司名稱") or "").strip()
    ticker = normalize_ticker(row.get("Ticker") or "")
    cik = normalize_cik(row.get("CIK") or "")

    if not company or company == "-":
        return False
    if not cik or cik == "-":
        return False

    # Public / tradable anchor
    if ticker != "-":
        return True

    # Private / non-listed anchor (ticker intentionally unavailable)
    private_tags = {"私人公司", "私有公司", "未上市", "PRIVATE"}
    if cik.upper() in private_tags:
        return True
    return False


def extract_json_obj(text: str) -> Dict[str, str]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def normalize_ticker(value: str) -> str:
    ticker = (value or "").strip().upper()
    if ticker in {"", "NONE", "N/A", "NA", "NULL"}:
        return "-"
    if re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", ticker):
        return ticker
    return "-"


def normalize_cik(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return "-"
    digits = re.sub(r"\D", "", v)
    if digits:
        if len(digits) <= 10:
            return digits.zfill(10)
        return digits
    return v


def normalize_generic(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return "-"
    if v.upper() in {"NONE", "N/A", "NA", "NULL"}:
        return "-"
    return v


def post_json_with_curl(url: str, payload: Dict[str, object], timeout: int) -> Dict[str, object]:
    marker = "__HTTP_STATUS__:"
    cmd = [
        "curl",
        "-sS",
        "--max-time",
        str(timeout),
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        url,
        "-d",
        json.dumps(payload, ensure_ascii=False),
        "-w",
        f"\n{marker}%{{http_code}}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Gemini request failed via curl (exit={proc.returncode}).")

    raw = proc.stdout or ""
    if marker not in raw:
        raise RuntimeError("Gemini curl response missing HTTP status marker.")
    body, status_text = raw.rsplit(marker, 1)
    try:
        status_code = int(status_text.strip())
    except Exception:
        raise RuntimeError("Gemini curl response has invalid HTTP status code.")

    if status_code >= 400:
        raise RuntimeError(f"Gemini API error {status_code}: {body[:300]}")

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini curl JSON parse failed: {e}")


def gemini_generate_metadata(
    concept_col: str,
    api_key: str,
    model: str,
    timeout: int = 90,
) -> Dict[str, str]:
    prompt = f"""
你是財務資料整理助手。請只輸出單一 JSON 物件，不要 markdown，不要多餘文字。

任務：針對概念欄位「{concept_col}」提供概念股主公司 metadata。
如果是私人公司或找不到可交易股票，Ticker 用 "-"。

JSON keys（必填）：
- company_name
- ticker
- cik
- latest_report
- upcoming_report
- release_time
- segments

規則：
- ticker 用美股或 ADR 代號（大寫），例如 NVDA、TSM、LNVGY；沒有就 "-"
- cik 優先 SEC CIK（10 碼字串），非 SEC 可放「私人公司」或「香港上市」
- latest_report / upcoming_report 例：FY2026 Q1；未知就 "-"
- release_time 例：2026年4月；未知就 "-"
- segments 用簡短逗號分隔
""".strip()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as e:
        # Fallback path: curl often works when Python DNS resolver has issues.
        data = post_json_with_curl(url=url, payload=payload, timeout=timeout)
    else:
        if resp.status_code >= 400:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini response has no candidates.")

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )
    text = ""
    if parts and isinstance(parts[0], dict):
        text = parts[0].get("text", "")

    obj = extract_json_obj(text)
    if not obj:
        raise RuntimeError(f"Gemini JSON parse failed for {concept_col}: {text[:240]}")

    return {
        "公司名稱": normalize_generic(str(obj.get("company_name", ""))),
        "Ticker": normalize_ticker(str(obj.get("ticker", ""))),
        "CIK": normalize_cik(str(obj.get("cik", ""))),
        "最新財報": normalize_generic(str(obj.get("latest_report", ""))),
        "即將發布": normalize_generic(str(obj.get("upcoming_report", ""))),
        "發布時間": normalize_generic(str(obj.get("release_time", ""))),
        "產品區段": normalize_generic(str(obj.get("segments", ""))),
    }


def write_metadata(path: str, rows: List[Dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "-") for k in OUTPUT_FIELDS})


def refresh_readme_if_needed(out_dir: str, concept_cols: List[str]) -> None:
    try:
        from update_conceptstocks import update_readme_concepts
    except Exception as e:
        print(f"Warning: failed to import update_readme_concepts: {e}", file=sys.stderr)
        return
    update_readme_concepts(out_dir, concept_cols)


def main() -> int:
    args = parse_args()

    env_file_values = load_env_file(os.path.join(os.getcwd(), ".env"))
    api_key = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or env_file_values.get("GEMINI_API_KEY")
        or env_file_values.get("GOOGLE_API_KEY")
        or ""
    ).strip()

    try:
        companyinfo_content = load_companyinfo_content(
            path=args.companyinfo_path,
            url=args.companyinfo_url,
        )
    except Exception as e:
        print(f"Failed to load company info: {e}", file=sys.stderr)
        return 1

    concept_cols = load_concept_columns(companyinfo_content)
    if not concept_cols:
        print("No concept columns found in company info.", file=sys.stderr)
        return 1

    metadata_path = os.path.join(args.out_dir, args.metadata_file)
    existing = load_existing_metadata(metadata_path)

    concepts_needing_refresh = []
    for concept in concept_cols:
        current = existing.get(concept, {})
        if args.force_refresh or not has_anchor_fields(current):
            concepts_needing_refresh.append(concept)

    unresolved_without_fallback = [c for c in concepts_needing_refresh if c not in CONCEPT_FALLBACKS]
    if unresolved_without_fallback and not api_key:
        print(
            "Missing GEMINI_API_KEY (or GOOGLE_API_KEY). "
            f"Need API for {len(unresolved_without_fallback)} concepts.",
            file=sys.stderr,
        )
        return 1

    output_rows: List[Dict[str, str]] = []
    refreshed_count = 0
    reused_count = 0
    unresolved_count = 0
    fallback_count = 0

    for i, concept in enumerate(concept_cols):
        current = existing.get(concept, {})
        should_refresh = args.force_refresh or not has_anchor_fields(current)

        if should_refresh:
            if i > 0:
                time.sleep(args.sleep)
            try:
                gem = gemini_generate_metadata(
                    concept_col=concept,
                    api_key=api_key,
                    model=args.model,
                )
                row = {"概念欄位": concept}
                for k in OUTPUT_FIELDS[1:]:
                    # Preserve existing non-empty time-like fields if Gemini is blank.
                    existing_v = (current.get(k) or "").strip()
                    gem_v = (gem.get(k) or "").strip()
                    if existing_v and existing_v != "-" and (not gem_v or gem_v == "-") and k in {"最新財報", "即將發布", "發布時間"}:
                        row[k] = existing_v
                    else:
                        row[k] = gem_v if gem_v else "-"
                output_rows.append(row)
                refreshed_count += 1
                print(f"Refreshed metadata: {concept} -> {row.get('Ticker', '-')}")
            except Exception as e:
                print(f"Gemini refresh failed for {concept}: {e}", file=sys.stderr)
                row = {"概念欄位": concept}
                if has_anchor_fields(current):
                    for k in OUTPUT_FIELDS[1:]:
                        v = (current.get(k) or "").strip()
                        row[k] = v if v else "-"
                    output_rows.append(row)
                    reused_count += 1
                    print(f"Fallback to cached metadata: {concept}")
                else:
                    concept_fallback = CONCEPT_FALLBACKS.get(concept)
                    if concept_fallback:
                        for k in OUTPUT_FIELDS[1:]:
                            v = (concept_fallback.get(k) or "").strip()
                            row[k] = v if v else "-"
                        output_rows.append(row)
                        fallback_count += 1
                        print(f"Applied built-in fallback metadata: {concept} -> {row.get('Ticker', '-')}")
                    else:
                        for k in OUTPUT_FIELDS[1:]:
                            v = (current.get(k) or "").strip()
                            row[k] = v if v else "-"
                        output_rows.append(row)
                        unresolved_count += 1
                        print(f"Unresolved metadata (no cache): {concept}", file=sys.stderr)
        else:
            row = {"概念欄位": concept}
            for k in OUTPUT_FIELDS[1:]:
                v = (current.get(k) or "").strip()
                row[k] = v if v else "-"
            output_rows.append(row)
            reused_count += 1

    if args.keep_extra_concepts:
        source_set = set(concept_cols)
        extras = [c for c in existing.keys() if c not in source_set]
        for concept in sorted(extras):
            row = {"概念欄位": concept}
            for k in OUTPUT_FIELDS[1:]:
                v = (existing[concept].get(k) or "").strip()
                row[k] = v if v else "-"
            output_rows.append(row)
        if extras:
            print(f"Kept {len(extras)} extra concepts not in companyinfo: {', '.join(extras)}")

    write_metadata(metadata_path, output_rows)
    print(
        f"Metadata written: {metadata_path} "
        f"(concepts={len(output_rows)}, reused={reused_count}, refreshed={refreshed_count}, fallback={fallback_count})"
    )

    if not args.skip_readme_update:
        refresh_readme_if_needed(args.out_dir, concept_cols)

    if unresolved_count > 0:
        print(f"Metadata generation completed with {unresolved_count} unresolved concepts.", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
