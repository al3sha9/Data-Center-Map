from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "sources" / "pdfs"
EXTRACTED_DIR = ROOT / "data" / "extracted"
PUBLIC_DATA_DIR = ROOT / "public" / "data"

KEYWORDS = [
    "data center",
    "data centre",
    "AI",
    "artificial intelligence",
    "electricity demand",
    "electricity consumption",
    "power demand",
    "energy demand",
    "TWh",
    "GWh",
    "GW",
    "MW",
    "2030",
    "projection",
    "forecast",
    "scenario",
    "hyperscale",
    "cloud",
    "server",
    "load growth",
    "grid",
]

PRIORITY_METRICS = {
    "total_electricity_demand_twh",
    "data_center_electricity_demand_twh",
    "ai_data_center_electricity_demand_twh",
    "data_center_share_percent",
    "electricity_generation_twh",
    "electricity_demand_growth_percent",
    "data_center_power_demand_gw",
    "peak_load_gw",
    "projection_low",
    "projection_base",
    "projection_high",
}

UNITS = {"TWh", "GWh", "MWh", "GW", "MW", "%", "percent"}
YEARS = {str(y) for y in range(2015, 2036)}


def ensure_dirs() -> None:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def stable_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def pdf_files() -> list[Path]:
    return sorted(p for p in PDF_DIR.glob("*.pdf") if p.is_file())


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def snippet_around(text: str, start: int, end: int, radius: int = 180) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    snippet = re.sub(r"\s+", " ", text[left:right]).strip()
    return snippet[:500]


def detect_title(filename: str, first_page_text: str) -> str | None:
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    for line in lines[:15]:
        if 8 <= len(line) <= 160 and not re.fullmatch(r"\d+", line):
            return line
    return Path(filename).stem.replace("-", " ").replace("_", " ").strip() or None


def extract_headings(text: str, page_number: int) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean or len(clean) > 140:
            continue
        looks_numbered = bool(re.match(r"^(\d+(\.\d+)*|[A-Z])[\).:\s-]+[A-Z]", clean))
        looks_title = clean.isupper() and len(clean) > 8
        if looks_numbered or looks_title:
            headings.append({"page": page_number, "text": clean})
    return headings[:20]


def extract_captions(text: str, page_number: int, label: str) -> list[dict[str, Any]]:
    pattern = re.compile(rf"\b{label}\s+\d+[\w.\-: ]*.{{0,220}}", re.IGNORECASE)
    return [
        {"page": page_number, "text": re.sub(r"\s+", " ", m.group(0)).strip()[:300]}
        for m in pattern.finditer(text)
    ][:20]


def keyword_hits_for_text(text: str, page_number: int) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for keyword in KEYWORDS:
        flags = 0 if keyword == "AI" else re.IGNORECASE
        for match in re.finditer(re.escape(keyword), text, flags):
            hits.append(
                {
                    "page": page_number,
                    "keyword": keyword,
                    "snippet": snippet_around(text, match.start(), match.end()),
                }
            )
            break
    return hits


def infer_region(text: str) -> tuple[str | None, str | None]:
    lower = text.lower()
    if "global" in lower or "world" in lower or "worldwide" in lower:
        return "global", None
    if "virginia" in lower or "loudoun" in lower or "prince william" in lower:
        return None, "United States"
    country_map = [
        ("United States", ["united states", "u.s.", " us ", " usa "]),
        ("China", ["china"]),
        ("Ireland", ["ireland"]),
        ("Germany", ["germany"]),
        ("Japan", ["japan"]),
        ("India", ["india"]),
    ]
    for country, needles in country_map:
        if any(n in f" {lower} " for n in needles):
            return None, country
    regions = [
        ("north_america", ["north america", "north american"]),
        ("europe", ["europe", "european"]),
        ("asia_pacific", ["asia pacific", "apac", "asia-pacific"]),
        ("middle_east", ["middle east"]),
        ("africa", ["africa"]),
        ("latam", ["latin america", "latam"]),
    ]
    for region, needles in regions:
        if any(n in lower for n in needles):
            return region, None
    return None, None


def infer_metric(text: str, unit: str) -> str | None:
    lower = text.lower()
    is_dc = "data center" in lower or "data centre" in lower or "datacenter" in lower
    is_ai = "artificial intelligence" in lower or re.search(r"\bai\b", lower)
    demand_terms = (
        "electricity demand" in lower
        or "electricity consumption" in lower
        or "energy demand" in lower
        or "consumption from data" in lower
        or "consumption reaches" in lower
        or "demand from data" in lower
        or "to supply data" in lower
    )
    if unit in {"%", "percent"}:
        if is_dc and ("electricity" in lower or "power" in lower):
            return "data_center_share_percent"
        if "growth" in lower or "increase" in lower:
            return "electricity_demand_growth_percent"
    if unit in {"GW", "MW"}:
        if is_dc and ("installed capacity" in lower or "designed capacity" in lower):
            return "data_center_power_demand_gw"
        if is_dc and ("peak" in lower or "load" in lower):
            return "peak_load_gw" if unit == "GW" else "peak_load_gw"
        if is_dc and ("power demand" in lower or "capacity" in lower):
            return "data_center_power_demand_gw"
    if unit in {"TWh", "GWh", "MWh"}:
        ai_specific = (
            "ai data centre" in lower
            or "ai data center" in lower
            or "ai-related data" in lower
            or "ai-specific" in lower
        )
        if is_ai and is_dc and ai_specific and demand_terms:
            return "ai_data_center_electricity_demand_twh"
        if is_dc and demand_terms:
            return "data_center_electricity_demand_twh"
        if "generation" in lower:
            return "electricity_generation_twh"
        if "electricity demand" in lower or "electricity consumption" in lower:
            return "total_electricity_demand_twh"
    return None


def infer_scenario(text: str) -> str:
    lower = text.lower()
    if "base" in lower or "central" in lower or "reference" in lower:
        return "base"
    if "high efficiency" in lower or "headwinds" in lower or "low" in lower or "conservative" in lower:
        return "low"
    if "lift-off" in lower or "optimistic" in lower or "high" in lower:
        return "high"
    if "project" in lower or "forecast" in lower or "scenario" in lower or "2030" in lower:
        return "estimate"
    return "historical"


def infer_confidence(source_id: str, quote: str, value_source: str) -> str:
    high_sources = ("iea", "ember", "epri", "weo", "global_energy_review")
    if any(s in source_id for s in high_sources) and value_source == "text":
        return "high"
    if value_source == "table":
        return "medium"
    return "low"


def normalize_value(value: float, unit: str, metric: str | None) -> tuple[float, str]:
    if unit == "%":
        return value, "percent"
    if metric and metric.endswith("_twh"):
        if unit == "GWh":
            return value / 1000, "TWh"
        if unit == "MWh":
            return value / 1_000_000, "TWh"
    if metric and metric.endswith("_gw"):
        if unit == "MW":
            return value / 1000, "GW"
    return value, unit


def today_iso() -> str:
    return date.today().isoformat()


RAW_FIELDS = [
    "source_id",
    "source_name",
    "filename",
    "page",
    "year",
    "region",
    "country",
    "metric",
    "value",
    "unit",
    "scenario",
    "quote",
    "note",
    "confidence",
]

REVIEW_FIELDS = RAW_FIELDS + [
    "candidate_id",
    "promote",
    "reviewer",
    "review_note",
    "corrected_year",
    "corrected_region",
    "corrected_country",
    "corrected_metric",
    "corrected_value",
    "corrected_unit",
    "corrected_scenario",
    "corrected_confidence",
]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in RAW_FIELDS})


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def candidate_id(row: dict[str, Any]) -> str:
    parts = [
        row.get("source_id", ""),
        row.get("page", ""),
        row.get("year", ""),
        row.get("region", ""),
        row.get("country", ""),
        row.get("metric", ""),
        row.get("value", ""),
        row.get("unit", ""),
        row.get("scenario", ""),
        str(row.get("quote", ""))[:160],
    ]
    raw = "_".join(str(part) for part in parts)
    return f"{stable_slug(raw)[:64]}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]}"


def write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {row.get("candidate_id"): row for row in read_csv_rows(path) if row.get("candidate_id")}
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for row in rows:
            cid = candidate_id(row)
            previous = existing.get(cid, {})
            out = {field: row.get(field, "") for field in REVIEW_FIELDS}
            out["candidate_id"] = cid
            for field in REVIEW_FIELDS:
                if field.startswith("corrected_") or field in {"promote", "reviewer", "review_note"}:
                    out[field] = previous.get(field, out.get(field, ""))
            if row.get("review_reason"):
                out["note"] = f"{row.get('note', '')} Review reason: {row['review_reason']}".strip()
            writer.writerow(out)
