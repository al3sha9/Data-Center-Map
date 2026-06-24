from __future__ import annotations

import csv

from common import (
    EXTRACTED_DIR,
    PUBLIC_DATA_DIR,
    PRIORITY_METRICS,
    REVIEW_FIELDS,
    UNITS,
    read_json,
    stable_slug,
    today_iso,
    write_json,
)

ALLOWED_SCENARIOS = {"historical", "estimate", "low", "base", "high", "headwinds", "high_efficiency", "lift_off"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def read_raw_rows():
    return read_review_rows_from(EXTRACTED_DIR / "review_candidates.csv") + read_review_rows_from(
        EXTRACTED_DIR / "top_review_claims.csv"
    )


def read_review_rows_from(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def promoted_review_rows(rows):
    promoted = []
    for row in rows:
        if (row.get("promote") or "").strip().lower() != "yes":
            continue
        out = normalize_review_row(row)
        corrections = {
            "corrected_year": "year",
            "corrected_region": "region",
            "corrected_country": "country",
            "corrected_metric": "metric",
            "corrected_value": "value",
            "corrected_unit": "unit",
            "corrected_scenario": "scenario",
            "corrected_confidence": "confidence",
        }
        for review_field, raw_field in corrections.items():
            corrected = (row.get(review_field) or "").strip()
            if not valid_correction(raw_field, corrected):
                continue
            if corrected:
                out[raw_field] = corrected
        promoted.append(out)
    return promoted


def valid_correction(raw_field, value):
    if not value:
        return True
    if raw_field == "year":
        return value.isdigit()
    if raw_field == "value":
        try:
            float(value)
        except ValueError:
            return False
    if raw_field == "unit":
        return value in UNITS
    if raw_field == "metric":
        return value in PRIORITY_METRICS
    if raw_field == "scenario":
        return value in ALLOWED_SCENARIOS
    if raw_field == "confidence":
        return value in ALLOWED_CONFIDENCE
    return True


def normalize_review_row(row):
    out = dict(row)
    if "best_quote" in row and "quote" not in row:
        out["quote"] = row.get("best_quote", "")
    if "all_pages" in row and "page" not in row:
        pages = [page for page in (row.get("all_pages") or "").split(";") if page]
        out["page"] = pages[0] if pages else ""
    if "review_note" in row and "note" not in row:
        note = row.get("review_note") or "Promoted from manual review."
        evidence_count = row.get("evidence_count")
        if evidence_count:
            note = f"{note} Evidence count: {evidence_count}."
        out["note"] = note
    if "candidate_ids" in row and "candidate_id" not in row:
        out["candidate_id"] = row.get("candidate_ids", "")
    return out


def source_records(indexes):
    records = []
    for doc in indexes:
        title = doc.get("title") or doc["filename"]
        lowered = f"{doc['source_id']} {title}".lower()
        publisher = None
        if "iea" in lowered or "energy and ai" in lowered or "world energy outlook" in lowered:
            publisher = "International Energy Agency"
        elif "global electricity review" in lowered:
            publisher = "Ember"
        elif "epri" in lowered:
            publisher = "Electric Power Research Institute"
        elif "goldman" in lowered:
            publisher = "Goldman Sachs"
        records.append(
            {
                "id": doc["source_id"],
                "name": title,
                "publisher": publisher,
                "type": "report",
                "year": None,
                "url": None,
                "filename": doc["filename"],
                "credibility": "high" if publisher else "medium",
                "notes": "Indexed local PDF source.",
            }
        )
    return records


def make_record_id(row):
    parts = [
        row["region"] or "country",
        row["country"] or "",
        row["metric"],
        row["year"],
        row["scenario"],
        row["source_id"],
        row["page"],
        row["value"],
    ]
    return stable_slug("_".join(parts))


BAD_FINAL_CONTEXT = (
    "gas-fired",
    "natural gas",
    "heating demand",
    "reused heat",
    "households",
    "trillion images",
    "hours of videos",
    "netflix",
    "gas plants",
    "how much inference demand",
    "generative ai outputs",
    "loudoun",
    "prince william",
    "northern virginia",
    "largest four hyperscalers",
)


def usable_public_row(row):
    quote = (row.get("quote") or "").lower()
    metric = row.get("metric") or ""
    try:
        value = float(row.get("value") or "nan")
    except ValueError:
        return False
    if value <= 0:
        return False
    if row.get("confidence") == "low":
        return False
    if any(term in quote for term in BAD_FINAL_CONTEXT):
        return False
    if metric.endswith("_twh"):
        direct = (
            "electricity demand from data" in quote
            or "electricity consumption from data" in quote
            or "consumption from data centres" in quote
            or "consumption from data centers" in quote
            or "demand from data centres" in quote
            or "demand from data centers" in quote
            or "to supply data centres" in quote
            or "to supply data centers" in quote
            or "global electricity demand from data centres" in quote
            or "global electricity demand from data centers" in quote
            or "data centre electricity consumption" in quote
            or "data center electricity consumption" in quote
        )
        if not direct:
            return False
    if metric.endswith("_gw"):
        direct = (
            "installed data centre capacity" in quote
            or "installed data center capacity" in quote
            or "designed capacity" in quote
            or "data centre market" in quote
            or "data center market" in quote
        )
        if not direct:
            return False
    return True


def main() -> None:
    indexes = read_json(EXTRACTED_DIR / "pdf_index.json", [])
    sources = source_records(indexes)
    source_labels = {s["id"]: s["name"] for s in sources}
    rows = promoted_review_rows(read_raw_rows())
    records = []
    seen_ids = set()
    for row in rows:
        if row.get("metric") not in PRIORITY_METRICS:
            continue
        if not row.get("source_id") or not row.get("year") or not row.get("value"):
            continue
        record = {
            "id": make_record_id(row),
            "year": int(row["year"]),
            "region": row["region"] or None,
            "country": row["country"] or None,
            "metric": row["metric"],
            "value": float(row["value"]),
            "unit": row["unit"],
            "scenario": row["scenario"],
            "source_id": row["source_id"],
            "source_label": source_labels.get(row["source_id"], row["source_id"]),
            "source_page": int(row["page"]),
            "confidence": row["confidence"],
            "note": row["note"],
        }
        if record["id"] in seen_ids:
            continue
        seen_ids.add(record["id"])
        records.append(record)

    records.sort(key=lambda r: (r["year"], r["metric"], r["source_id"], r["source_page"]))
    write_json(PUBLIC_DATA_DIR / "energy-demand.json", records)
    write_json(PUBLIC_DATA_DIR / "sources.json", sources)

    meta = {
        "version": "1.0",
        "last_updated": today_iso(),
        "total_records": len(records),
        "source_count": len(sources),
        "metrics": sorted({r["metric"] for r in records}),
        "coverage": {
            "years": sorted({r["year"] for r in records}),
            "regions": sorted({r["region"] for r in records if r["region"]}),
            "countries": sorted({r["country"] for r in records if r["country"]}),
        },
        "disclaimer": "This dataset is compiled from public research reports and should be treated as scenario-based educational data, not real-time operational measurement.",
    }
    write_json(PUBLIC_DATA_DIR / "meta.json", meta)
    print(f"Normalized {len(records)} records -> public/data/energy-demand.json")


if __name__ == "__main__":
    main()
