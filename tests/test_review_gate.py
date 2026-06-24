from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import common  # noqa: E402
import extract_relevant_pages  # noqa: E402
import normalize_extractions  # noqa: E402


class ReviewGateTests(unittest.TestCase):
    def test_review_fields_are_declared_after_raw_fields(self):
        self.assertEqual(
            common.REVIEW_FIELDS,
            common.RAW_FIELDS
            + [
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
            ],
        )

    def test_uncertain_scenario_range_rows_go_to_review_candidates(self):
        doc = {
            "source_id": "energyandai",
            "filename": "EnergyandAI.pdf",
            "title": "Energy and AI",
        }
        quote = (
            "In the Base Case, electricity consumption from data centres rises to around "
            "945 TWh by 2030. In the Lift-Off Case, consumption reaches over 1 260 TWh "
            "by 2030. The High Efficiency Case reaches around 800 TWh by 2030. "
            "In the Headwinds Case, it reaches around 670 TWh."
        )
        rows = extract_relevant_pages.extract_text_rows(doc, 49, quote)
        review_rows = [row for row in rows if row["needs_review"] == "yes"]
        public_rows = [row for row in rows if row["needs_review"] != "yes"]

        self.assertEqual(public_rows, [])
        self.assertEqual({row["value"] for row in review_rows}, {945.0, 1260.0, 800.0, 670.0})
        self.assertTrue(all(row["review_reason"] == "scenario_or_range_value" for row in review_rows))

    def test_normalizer_only_promotes_yes_rows_from_review_file(self):
        rows = [
            {
                "source_id": "energyandai",
                "source_name": "Energy and AI",
                "filename": "EnergyandAI.pdf",
                "page": "49",
                "year": "2030",
                "region": "global",
                "country": "",
                "metric": "data_center_electricity_demand_twh",
                "value": "945.0",
                "unit": "TWh",
                "scenario": "base",
                "quote": "electricity consumption from data centres rises to around 945 TWh by 2030",
                "note": "reviewed",
                "confidence": "high",
                "candidate_id": "approved",
                "promote": "yes",
                "reviewer": "tester",
                "review_note": "ok",
                "corrected_year": "",
                "corrected_region": "",
                "corrected_country": "",
                "corrected_metric": "",
                "corrected_value": "",
                "corrected_unit": "",
                "corrected_scenario": "",
                "corrected_confidence": "",
            },
            {
                "source_id": "energyandai",
                "source_name": "Energy and AI",
                "filename": "EnergyandAI.pdf",
                "page": "49",
                "year": "2030",
                "region": "global",
                "country": "",
                "metric": "data_center_electricity_demand_twh",
                "value": "1260.0",
                "unit": "TWh",
                "scenario": "high",
                "quote": "Lift-Off Case consumption reaches over 1 260 TWh by 2030",
                "note": "not reviewed",
                "confidence": "medium",
                "candidate_id": "not_approved",
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
            },
        ]

        promoted = normalize_extractions.promoted_review_rows(rows)

        self.assertEqual(len(promoted), 1)
        self.assertEqual(promoted[0]["value"], "945.0")

    def test_normalizer_promotes_top_claim_rows_with_best_quote_and_all_pages(self):
        rows = [
            {
                "priority_score": "156",
                "source_id": "energyandai",
                "source_name": "Energy and AI",
                "filename": "EnergyandAI.pdf",
                "year": "2030",
                "region": "global",
                "country": "",
                "metric": "data_center_electricity_demand_twh",
                "value": "945.0",
                "unit": "TWh",
                "scenario": "base",
                "confidence": "medium",
                "claim_type": "total_consumption",
                "all_pages": "49;63",
                "evidence_count": "2",
                "best_quote": "electricity consumption from data centres rises to around 945 TWh by 2030",
                "candidate_ids": "a;b",
                "promote": "yes",
                "reviewer": "tester",
                "review_note": "ok",
                "corrected_year": "",
                "corrected_region": "",
                "corrected_country": "",
                "corrected_metric": "",
                "corrected_value": "",
                "corrected_unit": "",
                "corrected_scenario": "",
                "corrected_confidence": "high",
            }
        ]

        promoted = normalize_extractions.promoted_review_rows(rows)

        self.assertEqual(len(promoted), 1)
        self.assertEqual(promoted[0]["quote"], rows[0]["best_quote"])
        self.assertEqual(promoted[0]["page"], "49")
        self.assertEqual(promoted[0]["confidence"], "high")

    def test_invalid_corrected_unit_is_ignored_for_promoted_rows(self):
        rows = [
            {
                "source_id": "energyandai",
                "source_name": "Energy and AI",
                "filename": "EnergyandAI.pdf",
                "page": "49",
                "year": "2030",
                "region": "global",
                "country": "",
                "metric": "data_center_electricity_demand_twh",
                "value": "800.0",
                "unit": "TWh",
                "scenario": "low",
                "quote": "consumption reaches around 800 TWh by 2030 for data centres",
                "note": "reviewed",
                "confidence": "low",
                "candidate_id": "approved",
                "promote": "yes",
                "reviewer": "tester",
                "review_note": "ok",
                "corrected_year": "",
                "corrected_region": "",
                "corrected_country": "",
                "corrected_metric": "",
                "corrected_value": "",
                "corrected_unit": "high_efficiency",
                "corrected_scenario": "",
                "corrected_confidence": "high",
            }
        ]

        promoted = normalize_extractions.promoted_review_rows(rows)

        self.assertEqual(promoted[0]["unit"], "TWh")
        self.assertEqual(promoted[0]["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
