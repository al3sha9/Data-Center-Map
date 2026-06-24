from __future__ import annotations

import re
from collections import defaultdict

import pdfplumber

from common import (
    EXTRACTED_DIR,
    PDF_DIR,
    clean_text,
    ensure_dirs,
    infer_confidence,
    infer_metric,
    infer_region,
    infer_scenario,
    normalize_value,
    read_json,
    snippet_around,
    write_csv,
    write_review_csv,
    write_json,
)

VALUE_RE = re.compile(
    r"(?P<value>\d+(?:(?:,| )\d{3})*(?:\.\d+)?)\s*(?P<unit>TWh|GWh|MWh|GW|MW|%|percent)\b",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(20[12]\d|203[0-5])\b")


def source_lookup(indexes):
    return {doc["source_id"]: doc for doc in indexes}


def nearest_year(quote, value_text):
    value_pos = quote.find(value_text)
    matches = list(YEAR_RE.finditer(quote))
    if not matches:
        return None
    if value_pos < 0:
        return matches[0].group(1)
    return min(matches, key=lambda m: abs(m.start() - value_pos)).group(1)


def row_from_quote(doc, page, quote, value, unit, value_source):
    year = nearest_year(quote, value)
    if not year:
        return None
    metric = infer_metric(quote, unit)
    if not metric:
        return None
    norm_value, norm_unit = normalize_value(float(value.replace(",", "").replace(" ", "")), unit, metric)
    region, country = infer_region(quote)
    scenario = infer_scenario(quote)
    if year >= "2030" and scenario in {"historical"}:
        scenario = "estimate"
    confidence = infer_confidence(doc["source_id"], quote, value_source)
    review_reason = review_reason_for_row(quote, scenario)
    return {
        "source_id": doc["source_id"],
        "source_name": doc.get("title") or doc["filename"],
        "filename": doc["filename"],
        "page": page,
        "year": year,
        "region": region or "global" if country is None else "",
        "country": country or "",
        "metric": metric,
        "value": round(norm_value, 6),
        "unit": norm_unit,
        "scenario": scenario,
        "quote": quote[:500],
        "note": f"Extracted from {value_source}; review source page before publication.",
        "confidence": confidence,
        "needs_review": "yes" if review_reason else "",
        "review_reason": review_reason,
    }


def review_reason_for_row(quote, scenario):
    lower = quote.lower()
    scenario_terms = (
        "base case",
        "lift-off",
        "headwinds",
        "high efficiency",
        "case",
        "scenario",
        "projection",
        "forecast",
        "projected",
        "conservative",
        "optimistic",
        "uncertainty",
        "range",
        "between",
        "over ",
        "around",
    )
    if scenario != "historical" or any(term in lower for term in scenario_terms):
        return "scenario_or_range_value"
    return ""


def extract_text_rows(doc, page_number, text):
    rows = []
    for match in VALUE_RE.finditer(text):
        quote = snippet_around(text, match.start(), match.end(), radius=220)
        row = row_from_quote(doc, page_number, quote, match.group("value"), match.group("unit"), "text")
        if row:
            rows.append(row)
    return rows


def extract_table_rows(doc, page_number, tables):
    rows = []
    for table in tables or []:
        flat = " | ".join(str(cell).strip() for record in table for cell in record if cell)
        flat = clean_text(flat)
        if not flat:
            continue
        for match in VALUE_RE.finditer(flat):
            quote = snippet_around(flat, match.start(), match.end(), radius=220)
            row = row_from_quote(doc, page_number, quote, match.group("value"), match.group("unit"), "table")
            if row:
                rows.append(row)
    return rows


def dedupe(rows):
    seen = set()
    out = []
    for row in rows:
        key = (
            row["source_id"],
            row["page"],
            row["year"],
            row["metric"],
            row["value"],
            row["unit"],
            row["scenario"],
            row["quote"][:120],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def main() -> None:
    ensure_dirs()
    indexes = read_json(EXTRACTED_DIR / "pdf_index.json", [])
    docs = source_lookup(indexes)
    relevant = read_json(EXTRACTED_DIR / "relevant_pages.json", [])
    pages_by_file = defaultdict(list)
    for item in relevant:
        pages_by_file[item["filename"]].append(item["page"])

    rows = []
    review_rows = []
    quotes = []
    for filename, page_numbers in pages_by_file.items():
        doc = next((d for d in docs.values() if d["filename"] == filename), None)
        if not doc:
            continue
        pdf_path = PDF_DIR / filename
        with pdfplumber.open(pdf_path) as pdf:
            for page_number in sorted(set(page_numbers)):
                if page_number < 1 or page_number > len(pdf.pages):
                    continue
                page = pdf.pages[page_number - 1]
                text = clean_text(page.extract_text())
                tables = []
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
                page_rows = extract_text_rows(doc, page_number, text)
                page_rows.extend(extract_table_rows(doc, page_number, tables))
                rows.extend(page_rows)
                review_rows.extend(row for row in page_rows if row.get("needs_review") == "yes")
                if page_rows:
                    quotes.append(
                        {
                            "source_id": doc["source_id"],
                            "filename": filename,
                            "page": page_number,
                            "quotes": [r["quote"] for r in page_rows[:10]],
                        }
                    )

    rows = dedupe(rows)
    review_rows = dedupe(review_rows)
    write_csv(EXTRACTED_DIR / "raw_extractions.csv", rows)
    write_review_csv(EXTRACTED_DIR / "review_candidates.csv", review_rows)
    write_json(EXTRACTED_DIR / "source_quotes.json", quotes)
    print(
        f"Extracted {len(rows)} candidate rows -> data/extracted/raw_extractions.csv; "
        f"{len(review_rows)} review rows -> data/extracted/review_candidates.csv"
    )


if __name__ == "__main__":
    main()
