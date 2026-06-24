from __future__ import annotations

import csv

from common import EXTRACTED_DIR, PUBLIC_DATA_DIR, PRIORITY_METRICS, REVIEW_FIELDS, read_json


def validate_review_candidates(errors):
    path = EXTRACTED_DIR / "review_candidates.csv"
    if not path.exists():
        errors.append("missing data/extracted/review_candidates.csv")
        return
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REVIEW_FIELDS:
            errors.append("review_candidates.csv has invalid columns")
            return
        ids = set()
        for i, row in enumerate(reader):
            prefix = f"review[{i}] {row.get('candidate_id', '<missing>')}:"
            cid = row.get("candidate_id")
            if not cid:
                errors.append(f"{prefix} missing candidate_id")
            elif cid in ids:
                errors.append(f"{prefix} duplicate candidate_id")
            ids.add(cid)
            promote = (row.get("promote") or "").strip().lower()
            if promote and promote not in {"yes", "no"}:
                errors.append(f"{prefix} promote must be yes, no, or blank")
            if promote == "yes":
                effective = dict(row)
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
                    if row.get(review_field):
                        effective[raw_field] = row[review_field]
                for field in ["source_id", "page", "year", "metric", "value", "unit", "confidence"]:
                    if not effective.get(field):
                        errors.append(f"{prefix} promoted row missing {field}")
                if not row.get("reviewer"):
                    errors.append(f"{prefix} promoted row missing reviewer")
                if effective.get("metric") not in PRIORITY_METRICS:
                    errors.append(f"{prefix} promoted row metric not allowed")
                try:
                    int(effective.get("year", ""))
                except ValueError:
                    errors.append(f"{prefix} promoted row year not integer")
                try:
                    float(effective.get("value", ""))
                except ValueError:
                    errors.append(f"{prefix} promoted row value not numeric")


def main() -> None:
    records = read_json(PUBLIC_DATA_DIR / "energy-demand.json", [])
    sources = read_json(PUBLIC_DATA_DIR / "sources.json", [])
    ids = set()
    source_ids = {s["id"] for s in sources}
    errors = []
    validate_review_candidates(errors)
    for i, record in enumerate(records):
        prefix = f"record[{i}] {record.get('id', '<missing>')}:"
        for field in ["id", "source_id", "year", "metric", "value", "unit", "confidence"]:
            if record.get(field) in (None, ""):
                errors.append(f"{prefix} missing {field}")
        if record.get("id") in ids:
            errors.append(f"{prefix} duplicate id")
        ids.add(record.get("id"))
        if not isinstance(record.get("value"), (int, float)):
            errors.append(f"{prefix} value not numeric")
        if not record.get("derived") and not record.get("source_page"):
            errors.append(f"{prefix} missing source_page")
        if record.get("source_id") not in source_ids:
            errors.append(f"{prefix} source_id not in sources.json")
        metric = record.get("metric", "")
        unit = record.get("unit")
        if metric.endswith("_twh") and unit != "TWh":
            errors.append(f"{prefix} TWh metric has unit {unit}")
        if metric.endswith("_gw") and unit != "GW":
            errors.append(f"{prefix} GW metric has unit {unit}")
        if metric.endswith("_percent") and unit != "percent":
            errors.append(f"{prefix} percent metric has unit {unit}")

    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"Validation OK: {len(records)} records, {len(sources)} sources")


if __name__ == "__main__":
    main()
