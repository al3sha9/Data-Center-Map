"""
extract_supporting_claims.py
────────────────────────────
Targeted extractor: EnergyandAI.pdf, pages 49-64 only.

Metrics targeted:
  data_center_share_percent
  total_electricity_demand_twh
  regional_data_center_demand_twh
  data_center_growth_increment_twh

Rules:
  - Reject chart axis labels (short isolated numbers on a line).
  - Keep regional growth increments separate from total consumption.
  - "increases by X TWh" → data_center_growth_increment_twh
  - "accounts for X%"   → data_center_share_percent
  - Total world electricity → total_electricity_demand_twh
  - Regional DC consumption → regional_data_center_demand_twh
  - Do NOT promote automatically (promote field left blank).
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

# ── resolve repo root so we can import common.py ────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pdfplumber

from common import (
    EXTRACTED_DIR,
    PDF_DIR,
    candidate_id,
    clean_text,
    infer_region,
    snippet_around,
    REVIEW_FIELDS,
)

# ── constants ────────────────────────────────────────────────
SOURCE_ID = "energyandai"
SOURCE_NAME = "Energy and AI"
FILENAME = "EnergyandAI.pdf"
PAGE_START = 49
PAGE_END = 64

TARGET_METRICS = {
    "data_center_share_percent",
    "total_electricity_demand_twh",
    "regional_data_center_demand_twh",
    "data_center_growth_increment_twh",
}

OUTPUT_PATH = EXTRACTED_DIR / "supporting_review_claims.csv"

# ── regex patterns ───────────────────────────────────────────
# Numeric values with units
VALUE_RE = re.compile(
    r"(?P<value>\d+(?:[,.]\d+)?)\s*(?P<unit>TWh|GWh|MWh|GW|MW|%|percent)\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(20[12]\d|203[0-5])\b")

# Growth / increment signals — must be close to the numeric value
# Only match explicit "increases by X", "grew by X", "rise of X", "additional X TWh"
GROWTH_SIGNALS = re.compile(
    r"\b(increases?\s+by|increase\s+of\s+(?:around|about|roughly|nearly|over)?\s*\d|"  # increases by / increase of ~N
    r"grew\s+by|growth\s+of\s+(?:around|about|roughly|nearly|over)?\s*\d|"  # grew by / growth of ~N
    r"rise\s+of|rises?\s+by|"  # rise of / rises by
    r"adds?\s+(?:around|about|roughly|nearly|over)?\s*\d|"  # adds ~N TWh
    r"additional\s+\d|additional\s+electricity\s+demand|"  # additional N TWh
    r"increment\s+of)\b",
    re.IGNORECASE,
)

# Share / percent signals
SHARE_SIGNALS = re.compile(
    r"\b(accounts?\s+for|represent(?:s)?|share\s+of|proportion\s+of|"
    r"fraction\s+of|amount(?:s)?\s+to|equivalent\s+to)\b",
    re.IGNORECASE,
)

# Total world electricity signals
TOTAL_DEMAND_SIGNALS = re.compile(
    r"\b(total\s+(global\s+)?electricity\s+demand|global\s+electricity\s+(?:demand|consumption)|"
    r"world(?:wide)?\s+electricity\s+(?:demand|consumption)|"
    r"total\s+electricity\s+(?:demand|consumption))\b",
    re.IGNORECASE,
)

# Regional DC demand signals
REGIONAL_SIGNALS = re.compile(
    r"\b(united\s+states|u\.s\.|europe|china|japan|india|"
    r"north\s+america|asia.pacific|middle\s+east|southeast\s+asia|"
    r"virginia|ireland|singapore)\b",
    re.IGNORECASE,
)

DC_SIGNALS = re.compile(
    r"\b(data\s+cent(?:er|re)s?|datacenters?|hyperscale|server\s+farm)\b",
    re.IGNORECASE,
)

SCENARIO_MAP = {
    "base case": "base",
    "base-case": "base",
    "lift-off": "lift_off",
    "lift off": "lift_off",
    "headwinds": "headwinds",
    "high efficiency": "high_efficiency",
    "high-efficiency": "high_efficiency",
    "conservative": "headwinds",
    "low scenario": "headwinds",
    "high scenario": "lift_off",
    "optimistic": "lift_off",
    "central": "base",
    "reference": "base",
}

CONFIDENCE_MAP = {
    "high": ["exactly", "confirmed", "reported", "accounts for", "totalled", "was"],
    "medium": ["approximately", "around", "about", "roughly", "nearly"],
    "low": ["could", "might", "may", "potentially", "up to", "as much as"],
}


# ── helpers ───────────────────────────────────────────────────

def nearest_year(text: str, pos: int) -> str | None:
    matches = list(YEAR_RE.finditer(text))
    if not matches:
        return None
    return min(matches, key=lambda m: abs(m.start() - pos)).group(1)


def infer_scenario(text: str) -> str:
    lower = text.lower()
    for phrase, scenario in SCENARIO_MAP.items():
        if phrase in lower:
            return scenario
    if "2030" in text and re.search(r"\bproject|forecast|scenario\b", lower):
        return "estimate"
    return "estimate"


def infer_confidence(text: str) -> str:
    lower = text.lower()
    for conf, signals in CONFIDENCE_MAP.items():
        if any(s in lower for s in signals):
            return conf
    return "medium"


def is_axis_label(quote: str) -> bool:
    """Reject short, isolated numeric snippets that look like chart axis labels."""
    stripped = quote.strip()
    # If the surrounding context is very short and almost entirely numeric → axis label
    words = stripped.split()
    if len(words) <= 4:
        nums = sum(1 for w in words if re.fullmatch(r"[\d,.]+", w))
        if nums >= len(words) - 1:
            return True
    return False


def classify_metric(text: str, unit: str, value: float, match_pos: int = 0) -> str | None:
    """
    Apply strict metric classification rules:
      1. Growth increment ("increases by X TWh", "grew by X TWh") → data_center_growth_increment_twh
      2. Share percent ("accounts for X%")                        → data_center_share_percent
      3. Total world demand (TWh, global, no specific region)     → total_electricity_demand_twh
      4. Regional DC demand (region present, not growth)          → regional_data_center_demand_twh

    Key discipline: "consumption reaches X TWh" is NOT a growth increment.
    """
    norm_unit = unit.upper().replace("PERCENT", "%")

    # Rule 1: growth increment — the growth signal must appear WITHIN 120 chars of the value
    if norm_unit in {"TWH", "GWH", "MWH"} and DC_SIGNALS.search(text):
        # Extract a tight window around the value match position
        window_start = max(0, match_pos - 120)
        window_end = min(len(text), match_pos + 120)
        window = text[window_start:window_end]
        if GROWTH_SIGNALS.search(window):
            return "data_center_growth_increment_twh"

    # Rule 2: share percent
    if norm_unit in {"%", "PERCENT"}:
        if DC_SIGNALS.search(text) and (SHARE_SIGNALS.search(text) or "electricity" in text.lower()):
            return "data_center_share_percent"
        return None  # % without DC context — skip

    if norm_unit not in {"TWH", "GWH"}:
        return None

    # Rule 3: total world demand (global language, no specific country/region)
    if TOTAL_DEMAND_SIGNALS.search(text) and not REGIONAL_SIGNALS.search(text):
        return "total_electricity_demand_twh"

    # Rule 4: regional DC demand
    if DC_SIGNALS.search(text) and REGIONAL_SIGNALS.search(text):
        return "regional_data_center_demand_twh"

    return None


def normalize_twh(value: float, unit: str) -> tuple[float, str]:
    u = unit.upper()
    if u == "GWH":
        return round(value / 1000, 4), "TWh"
    return value, "TWh" if u == "TWH" else unit


def build_row(page: int, text: str, match: re.Match) -> dict | None:
    raw_value = match.group("value").replace(",", "")
    raw_unit = match.group("unit")

    try:
        value = float(raw_value)
    except ValueError:
        return None

    quote = snippet_around(text, match.start(), match.end(), radius=250)

    if is_axis_label(quote):
        return None

    metric = classify_metric(quote, raw_unit, value, match_pos=match.start())
    if metric not in TARGET_METRICS:
        return None

    year = nearest_year(quote, match.start())
    if not year:
        return None

    norm_value, norm_unit = normalize_twh(value, raw_unit) if "wh" in raw_unit.lower() else (value, raw_unit)
    region, country = infer_region(quote)
    scenario = infer_scenario(quote)
    confidence = infer_confidence(quote)

    # For regional metric, region or country must be present
    if metric == "regional_data_center_demand_twh" and not region and not country:
        return None

    # For total demand, ensure it's actually global
    if metric == "total_electricity_demand_twh" and country:
        # country-specific total → reclassify or skip
        return None

    return {
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "filename": FILENAME,
        "page": page,
        "year": year,
        "region": region or ("global" if not country else ""),
        "country": country or "",
        "metric": metric,
        "value": norm_value,
        "unit": norm_unit,
        "scenario": scenario,
        "quote": quote[:500],
        "note": f"Extracted from pages {PAGE_START}–{PAGE_END}. Requires manual review before promotion.",
        "confidence": confidence,
        # review fields (leave blank — do NOT promote automatically)
        "candidate_id": "",
        "promote": "",
        "reviewer": "",
        "review_note": "",
        "corrected_year": "",
        "corrected_region": "",
        "corrected_country": "",
        "corrected_metric": "",
        "corrected_value": "",
        "corrected_unit": "",
        "corrected_scenario": "",
        "corrected_confidence": "",
    }


def dedupe(rows: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out = []
    for row in rows:
        key = (row["page"], row["metric"], str(row["value"]), row["unit"], row["year"], row["quote"][:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


# ── main ─────────────────────────────────────────────────────

def main() -> None:
    pdf_path = PDF_DIR / FILENAME
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found", file=sys.stderr)
        sys.exit(1)

    rows: list[dict] = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"PDF has {total_pages} pages. Extracting pages {PAGE_START}–{PAGE_END}.")

        for pn in range(PAGE_START, min(PAGE_END + 1, total_pages + 1)):
            page = pdf.pages[pn - 1]
            text = clean_text(page.extract_text() or "")

            if not text:
                print(f"  p{pn}: no text")
                continue

            page_rows: list[dict] = []

            # Text extraction
            for match in VALUE_RE.finditer(text):
                row = build_row(pn, text, match)
                if row:
                    page_rows.append(row)

            # Table extraction (for figures cited in tables)
            try:
                tables = page.extract_tables() or []
                for table in tables:
                    flat = clean_text(
                        " | ".join(str(c).strip() for record in table for c in record if c)
                    )
                    for match in VALUE_RE.finditer(flat):
                        row = build_row(pn, flat, match)
                        if row:
                            page_rows.append(row)
            except Exception:
                pass

            # Share-percent pass — separate regex for "X% of ... data centre" patterns
            # VALUE_RE misses bare "2%" without TWh/GW unit; handle it here explicitly
            SHARE_PCT_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*%")
            CHART_AXIS_RE = re.compile(
                # Reject sequences of consecutive axis numbers like "5% 4% 3% 2% 1%"
                r"(?:\d+(?:\.\d+)?\s*%\s*){4,}"
            )
            for match in SHARE_PCT_RE.finditer(text):
                val = float(match.group("value"))
                if val <= 0 or val > 100:
                    continue
                window_start = max(0, match.start() - 200)
                window_end = min(len(text), match.end() + 200)
                ctx = text[window_start:window_end]
                # Reject chart axis label sequences
                if CHART_AXIS_RE.search(ctx):
                    continue
                # Reject quotes that are figure captions / chart axis dumps
                if re.match(r"^\s*Figure\s+\d+", ctx.strip(), re.IGNORECASE):
                    continue
                if re.search(r"(?:500\s+5%|400\s+4%|300\s+3%|200\s+2%|100\s+1%)", ctx):
                    continue
                if is_axis_label(ctx):
                    continue
                if not DC_SIGNALS.search(ctx):
                    continue
                if not SHARE_SIGNALS.search(ctx):
                    continue
                year = nearest_year(ctx, match.start() - window_start)
                if not year:
                    continue
                region, country = infer_region(ctx)
                scenario = infer_scenario(ctx)
                confidence = infer_confidence(ctx)
                quote = ctx.strip()[:500]
                page_rows.append({
                    "source_id": SOURCE_ID,
                    "source_name": SOURCE_NAME,
                    "filename": FILENAME,
                    "page": pn,
                    "year": year,
                    "region": region or ("global" if not country else ""),
                    "country": country or "",
                    "metric": "data_center_share_percent",
                    "value": val,
                    "unit": "%",
                    "scenario": scenario,
                    "quote": quote,
                    "note": f"Extracted from pages {PAGE_START}–{PAGE_END}. Requires manual review before promotion.",
                    "confidence": confidence,
                    "candidate_id": "",
                    "promote": "",
                    "reviewer": "",
                    "review_note": "",
                    "corrected_year": "",
                    "corrected_region": "",
                    "corrected_country": "",
                    "corrected_metric": "",
                    "corrected_value": "",
                    "corrected_unit": "",
                    "corrected_scenario": "",
                    "corrected_confidence": "",
                })

            print(f"  p{pn}: {len(text)} chars, {len(page_rows)} candidate rows")
            rows.extend(page_rows)


    rows = dedupe(rows)

    # Assign candidate_ids
    for row in rows:
        row["candidate_id"] = candidate_id(row)

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in REVIEW_FIELDS})

    # ── report ───────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total rows: {len(rows)}")
    print()

    metric_counts: dict[str, int] = {}
    for row in rows:
        m = row["metric"]
        metric_counts[m] = metric_counts.get(m, 0) + 1

    print("Rows per metric:")
    for metric in TARGET_METRICS:
        print(f"  {metric}: {metric_counts.get(metric, 0)}")

    # Flag risky rows
    risky = []
    for row in rows:
        reasons = []
        if row["confidence"] == "low":
            reasons.append("low confidence")
        if row["year"] < "2020":
            reasons.append(f"unusual year ({row['year']})")
        if row["scenario"] == "estimate" and row["year"] >= "2030":
            reasons.append("future estimate without named scenario")
        if float(str(row["value"]).replace(",", "") or 0) == 0:
            reasons.append("zero value")
        if reasons:
            risky.append((row["page"], row["metric"], row["value"], row["unit"], reasons))

    print()
    if risky:
        print(f"Rows flagged for manual review ({len(risky)}):")
        for page, metric, value, unit, reasons in risky:
            print(f"  p{page} | {metric} | {value} {unit} → {', '.join(reasons)}")
    else:
        print("No rows flagged as risky.")

    print(f"\nAll rows have promote='' — nothing promoted automatically.")


if __name__ == "__main__":
    main()
