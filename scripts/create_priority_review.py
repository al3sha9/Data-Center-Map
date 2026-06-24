from __future__ import annotations

import csv
import re
from pathlib import Path

from common import EXTRACTED_DIR, REVIEW_FIELDS

PRIORITY_FIELDS = ["priority_score"] + REVIEW_FIELDS
TOP_CLAIM_FIELDS = [
    "priority_score",
    "source_id",
    "source_name",
    "filename",
    "year",
    "region",
    "country",
    "metric",
    "value",
    "unit",
    "scenario",
    "confidence",
    "claim_type",
    "all_pages",
    "evidence_count",
    "best_quote",
    "candidate_ids",
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

HIGH_QUALITY_SOURCES = (
    "iea",
    "energyandai",
    "worldenergyoutlook",
    "world_energy_outlook",
    "epri",
    "mckinsey",
    "goldman",
    "uptime",
    "ember",
    "global_electricity_review",
    "globalenergyreview",
)

CONTEXT_TERMS = (
    "data center",
    "data centre",
    "datacenter",
    "ai",
    "artificial intelligence",
    "electricity demand",
    "electricity consumption",
    "energy demand",
    "power demand",
    "2030",
)

DC_DEMAND_TERMS = (
    "data center electricity demand",
    "data centre electricity demand",
    "data center electricity consumption",
    "data centre electricity consumption",
    "electricity demand from data",
    "electricity consumption from data",
    "electricity consumption by data",
    "consumption from data centres",
    "consumption from data centers",
    "to supply data centres",
    "to supply data centers",
)

TARGET_VALUES = (415, 670, 800, 945, 1260)
TARGET_YEARS = {"2024", "2030"}
TARGET_SCOPES = {"global", "north_america", "europe", "asia_pacific", "middle_east", "africa", "latam"}
TARGET_COUNTRIES = {"united states", "us", "u.s.", "usa"}
AXIS_TICK_VALUES = {500, 1000, 1500, 2000}


def read_review_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def high_quality_source(row: dict[str, str]) -> bool:
    haystack = " ".join(
        [
            row.get("source_id", ""),
            row.get("source_name", ""),
            row.get("filename", ""),
        ]
    ).lower()
    return any(source in haystack for source in HIGH_QUALITY_SOURCES)


def has_twh(row: dict[str, str]) -> bool:
    return row.get("unit") == "TWh" or "twh" in context(row)


def context(row: dict[str, str]) -> str:
    return " ".join(
        [
            row.get("metric", ""),
            row.get("quote", ""),
            row.get("note", ""),
        ]
    ).lower()


def has_relevant_context(row: dict[str, str]) -> bool:
    haystack = context(row)
    return any(term in haystack for term in CONTEXT_TERMS)


def include_row(row: dict[str, str]) -> bool:
    return has_twh(row) and has_relevant_context(row) and high_quality_source(row)


def mentions_dc_electricity_claim(row: dict[str, str]) -> bool:
    haystack = context(row)
    has_dc = "data center" in haystack or "data centre" in haystack or "datacenter" in haystack
    has_electricity = "electricity" in haystack
    has_consumption_or_demand = "consumption" in haystack or "demand" in haystack
    return has_dc and has_electricity and has_consumption_or_demand


def value_forms(row: dict[str, str]) -> list[str]:
    try:
        value = float(row.get("value", ""))
    except ValueError:
        return []
    integer = int(value)
    forms = {str(integer), f"{integer:,}", f"{integer:,}".replace(",", " ")}
    if value != integer:
        forms.add(str(value))
    return sorted(forms, key=len, reverse=True)


def sentence_for_value(row: dict[str, str]) -> str:
    quote = row.get("quote", "")
    chunks = re.split(r"(?<=[.!?])\s+|\s+\|\s+", quote)
    forms = value_forms(row)
    for chunk in chunks:
        if any(re.search(rf"(?<!\d){re.escape(form)}(?!\d)", chunk) for form in forms):
            return chunk.strip()
    return quote.strip()


def claim_year(row: dict[str, str]) -> str:
    sentence = sentence_for_value(row)
    forms = value_forms(row)
    value_positions = [
        match.start()
        for form in forms
        for match in re.finditer(rf"(?<!\d){re.escape(form)}(?!\d)", sentence)
    ]
    years = list(re.finditer(r"\b(20[12]\d|203[0-5])\b", sentence))
    if not years:
        return row.get("year", "")
    if not value_positions:
        return years[0].group(1)
    value_pos = min(value_positions)
    following_years = [match for match in years if match.start() >= value_pos]
    if following_years:
        return following_years[0].group(1)
    return min(years, key=lambda match: abs(match.start() - value_pos)).group(1)


def explicit_total_sentence(sentence: str) -> bool:
    lower = sentence.lower()
    has_dc = "data center" in lower or "data centre" in lower or "datacenter" in lower
    has_consumption = "electricity" in lower and ("consumption" in lower or "demand" in lower)
    total_verbs = (
        "reach",
        "reaches",
        "reached",
        "rises to",
        "rise to",
        "rose to",
        "set to",
        "projected to",
        "forecast to",
        "estimated",
        "accounted for",
        "accounts for",
        "was",
        "is ",
    )
    return has_dc and has_consumption and any(verb in lower for verb in total_verbs)


def claim_type(row: dict[str, str]) -> str:
    quote = row.get("quote", "").lower()
    sentence = sentence_for_value(row)
    lower_sentence = sentence.lower()
    if row.get("unit") in {"%", "percent"} or "%" in sentence:
        return "share_percent"
    try:
        value = int(float(row.get("value", "")))
    except ValueError:
        value = None
    if value in AXIS_TICK_VALUES and not explicit_total_sentence(sentence):
        return "chart_axis_noise"
    growth_terms = (
        "increase by",
        "increases by",
        "increased by",
        "increases from",
        "increase from",
        "growth",
        "incremental",
        "additional",
        "more than the",
        "compared to",
        "up ",
        "from today",
        "from the 2024 level",
    )
    if any(term in lower_sentence for term in growth_terms):
        return "growth_increment"
    if explicit_total_sentence(sentence):
        return "total_consumption"
    if (
        row.get("metric") == "data_center_electricity_demand_twh"
        and ("data centre" in quote or "data center" in quote or "datacenter" in quote)
        and (
            "consumption reaches" in lower_sentence
            or "it reaches" in lower_sentence
            or "demand reaches" in lower_sentence
            or "use reaches" in lower_sentence
        )
    ):
        return "total_consumption"
    if mentions_dc_electricity_claim(row) and explicit_total_sentence(quote):
        return "total_consumption"
    return "unrelated"


def scope_for_row(row: dict[str, str]) -> tuple[str, str]:
    sentence = sentence_for_value(row).lower()
    quote = row.get("quote", "").lower()
    row_region = row.get("region", "")
    row_country = row.get("country", "")
    countries = {
        "United States": ("united states", "u.s.", " us ", "usa"),
        "China": ("china",),
        "India": ("india",),
        "Japan": ("japan",),
        "Germany": ("germany",),
        "Ireland": ("ireland",),
    }
    for country, needles in countries.items():
        if any(needle in f" {sentence} " for needle in needles):
            return "", country
    if row_country == "United States" and not any(needle in f" {sentence} " for needle in countries["United States"]):
        if "global" in quote or "global" in sentence or "world" in sentence:
            return "global", ""
        return "", ""
    if row_region == "global" and any(
        term in sentence
        for term in ("united states", "u.s.", " us ", "china", "europe", "india", "japan", "africa")
    ):
        if "europe" in sentence:
            return "europe", ""
        return "", row_country
    return row_region, row_country


def include_top_claim_row(row: dict[str, str]) -> bool:
    region, country = scope_for_row(row)
    year = claim_year(row)
    return (
        row.get("metric") == "data_center_electricity_demand_twh"
        and row.get("unit") == "TWh"
        and row.get("year") in TARGET_YEARS
        and year == row.get("year")
        and high_quality_source(row)
        and mentions_dc_electricity_claim(row)
        and claim_type(row) == "total_consumption"
        and bool(region or country)
    )


def score_row(row: dict[str, str]) -> int:
    haystack = context(row)
    score = 0

    if high_quality_source(row):
        score += 30
    if "iea" in " ".join([row.get("source_id", ""), row.get("source_name", ""), row.get("filename", "")]).lower():
        score += 15
    if any(term in haystack for term in DC_DEMAND_TERMS):
        score += 30
    elif "data center" in haystack or "data centre" in haystack:
        score += 15
    if row.get("year") in TARGET_YEARS:
        score += 15
    if row.get("year") == "2030":
        score += 8
    if row.get("region") in TARGET_SCOPES:
        score += 12
    if (row.get("country") or "").lower() in TARGET_COUNTRIES:
        score += 12

    try:
        value = float(row.get("value", ""))
    except ValueError:
        value = None
    if value is not None:
        nearest = min(abs(value - target) for target in TARGET_VALUES)
        if nearest == 0:
            score += 30
        elif nearest <= 15:
            score += 20
        elif nearest <= 50:
            score += 10

    if row.get("metric") == "data_center_electricity_demand_twh":
        score += 20
    elif row.get("metric") == "ai_data_center_electricity_demand_twh":
        score += 15

    if "scenario_or_range_value" in (row.get("note") or "").lower():
        score += 8
    return score


def priority_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    priority = []
    for row in rows:
        if not include_row(row):
            continue
        out = dict(row)
        out["promote"] = row.get("promote", "")
        out["priority_score"] = str(score_row(row))
        priority.append(out)
    priority.sort(
        key=lambda row: (
            int(row["priority_score"]),
            row.get("source_id", ""),
            row.get("page", ""),
            row.get("candidate_id", ""),
        ),
        reverse=True,
    )
    return priority


def claim_key(row: dict[str, str]) -> tuple[str, str, str, str, str, str, str, str]:
    region, country = scope_for_row(row)
    return (
        row.get("source_id", ""),
        row.get("year", ""),
        region,
        country,
        row.get("metric", ""),
        row.get("value", ""),
        row.get("unit", ""),
        row.get("scenario", ""),
    )


def top_claim_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[tuple[str, str, str, str, str, str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        if not include_top_claim_row(row):
            continue
        groups.setdefault(claim_key(row), []).append(row)

    claims = []
    for key, group in groups.items():
        scored = sorted(
            group,
            key=lambda row: (score_row(row), len(row.get("quote", "")), row.get("candidate_id", "")),
            reverse=True,
        )
        best = scored[0]
        pages = sorted({row.get("page", "") for row in group if row.get("page")}, key=lambda p: int(p) if p.isdigit() else 99999)
        candidate_ids = [row.get("candidate_id", "") for row in group if row.get("candidate_id")]
        region, country = scope_for_row(best)
        claim = {
            "priority_score": str(score_row(best) + min(len(group), 5) * 3),
            "source_id": key[0],
            "source_name": best.get("source_name", ""),
            "filename": best.get("filename", ""),
            "year": key[1],
            "region": region,
            "country": country,
            "metric": key[4],
            "value": key[5],
            "unit": key[6],
            "scenario": key[7],
            "confidence": best.get("confidence", ""),
            "claim_type": "total_consumption",
            "all_pages": ";".join(pages),
            "evidence_count": str(len(group)),
            "best_quote": best.get("quote", ""),
            "candidate_ids": ";".join(candidate_ids),
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
        claims.append(claim)

    claims.sort(
        key=lambda row: (
            int(row["priority_score"]),
            int(row["evidence_count"]),
            row.get("source_id", ""),
            row.get("year", ""),
            row.get("value", ""),
        ),
        reverse=True,
    )
    return claims


def write_priority_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PRIORITY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in PRIORITY_FIELDS})


def write_top_claim_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TOP_CLAIM_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in TOP_CLAIM_FIELDS})


def main() -> None:
    input_path = EXTRACTED_DIR / "review_candidates.csv"
    review_rows = read_review_rows(input_path)
    priority = priority_rows(review_rows)
    top_claims = top_claim_rows(review_rows)
    write_priority_rows(EXTRACTED_DIR / "priority_review_candidates.csv", priority)
    write_top_claim_rows(EXTRACTED_DIR / "top_review_claims.csv", top_claims)
    print(f"Wrote {len(priority)} priority candidates -> data/extracted/priority_review_candidates.csv")
    print(f"Wrote {len(top_claims)} top claims -> data/extracted/top_review_claims.csv")


if __name__ == "__main__":
    main()
