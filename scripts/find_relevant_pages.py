from __future__ import annotations

from collections import defaultdict

from common import EXTRACTED_DIR, read_json, write_json

STRONG_TERMS = {
    "data center": 4,
    "data centre": 4,
    "artificial intelligence": 3,
    "electricity demand": 3,
    "electricity consumption": 3,
    "power demand": 3,
    "TWh": 3,
    "GW": 2,
    "2030": 2,
    "projection": 2,
    "forecast": 2,
    "scenario": 2,
    "load growth": 2,
}


def main() -> None:
    indexes = read_json(EXTRACTED_DIR / "pdf_index.json", [])
    relevant = []
    for doc in indexes:
        page_scores = defaultdict(int)
        evidence = defaultdict(list)
        for hit in doc.get("keyword_hits", []):
            weight = STRONG_TERMS.get(hit["keyword"], 1)
            page_scores[hit["page"]] += weight
            evidence[hit["page"]].append(hit)

        selected = set()
        for page, score in page_scores.items():
            if score >= 5:
                selected.update({page - 1, page, page + 1})
        selected = {p for p in selected if 1 <= p <= doc["page_count"]}

        for page in sorted(selected):
            relevant.append(
                {
                    "source_id": doc["source_id"],
                    "filename": doc["filename"],
                    "page": page,
                    "score": page_scores.get(page, 0),
                    "neighbor": page not in evidence,
                    "evidence": evidence.get(page, [])[:8],
                }
            )

    write_json(EXTRACTED_DIR / "relevant_pages.json", relevant)
    print(f"Selected {len(relevant)} relevant pages -> data/extracted/relevant_pages.json")


if __name__ == "__main__":
    main()
