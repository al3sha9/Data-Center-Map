from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import create_priority_review  # noqa: E402


def row(**overrides):
    base = {
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
        "quote": "Base Case electricity consumption from data centres rises to around 945 TWh by 2030.",
        "note": "candidate",
        "confidence": "medium",
        "candidate_id": "candidate",
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
    base.update(overrides)
    return base


class PriorityReviewTests(unittest.TestCase):
    def test_filters_to_useful_high_quality_twh_candidates(self):
        rows = [
            row(candidate_id="keep"),
            row(
                candidate_id="drop_unit",
                unit="GW",
                quote="Data centres installed capacity reached 5 GW in 2024.",
                metric="data_center_power_demand_gw",
            ),
            row(
                candidate_id="drop_context",
                metric="electricity_generation_twh",
                year="2025",
                quote="Coal generation reached 945 TWh.",
            ),
            row(
                candidate_id="drop_source",
                source_id="unknown_blog",
                source_name="Unknown Blog",
                filename="unknown.pdf",
            ),
        ]

        priority = create_priority_review.priority_rows(rows)

        self.assertEqual([r["candidate_id"] for r in priority], ["keep"])
        self.assertIn("priority_score", priority[0])
        self.assertEqual(priority[0]["promote"], "")

    def test_sorts_target_global_2030_values_first(self):
        rows = [
            row(candidate_id="low", value="300.0", year="2025", region="latam"),
            row(candidate_id="target", value="945.0", year="2030", region="global"),
            row(candidate_id="target_2024", value="415.0", year="2024", region="global"),
        ]

        priority = create_priority_review.priority_rows(rows)

        self.assertEqual(priority[0]["candidate_id"], "target")
        self.assertGreater(float(priority[0]["priority_score"]), float(priority[-1]["priority_score"]))

    def test_top_claims_group_duplicates_and_keep_best_evidence(self):
        rows = [
            row(
                candidate_id="weaker",
                page="49",
                quote="Data centre electricity consumption reaches 945 TWh by 2030.",
            ),
            row(
                candidate_id="best",
                page="63",
                quote=(
                    "Global electricity consumption by data centres is projected to reach "
                    "around 945 TWh by 2030 in the Base Case."
                ),
            ),
            row(
                candidate_id="other_claim",
                page="77",
                year="2024",
                value="415.0",
                scenario="estimate",
                quote="Estimated 415 TWh of global electricity demand from data centres in 2024.",
            ),
            row(
                candidate_id="drop_wrong_metric",
                metric="electricity_generation_twh",
                quote="Electricity generation from coal was 945 TWh in 2030.",
            ),
            row(
                candidate_id="drop_wrong_year",
                year="2025",
                quote="Data centre electricity consumption reaches 500 TWh in 2025.",
                value="500.0",
            ),
        ]

        claims = create_priority_review.top_claim_rows(rows)

        self.assertEqual(len(claims), 2)
        first = claims[0]
        self.assertEqual(first["value"], "945.0")
        self.assertEqual(first["evidence_count"], "2")
        self.assertEqual(first["all_pages"], "49;63")
        self.assertEqual(first["candidate_ids"], "weaker;best")
        self.assertIn("Global electricity consumption", first["best_quote"])
        self.assertEqual(first["promote"], "")
        self.assertEqual(first["claim_type"], "total_consumption")

    def test_top_claims_reject_chart_ticks_and_growth_increments(self):
        rows = [
            row(
                candidate_id="axis_tick",
                value="1000.0",
                quote="Figure 2.20 Global electricity generation to supply data centres TWh 0 500 1 000 1 500 2 000.",
            ),
            row(
                candidate_id="explicit_total",
                value="1000.0",
                quote="Global electricity consumption by data centres is projected to reach 1 000 TWh in 2030.",
            ),
            row(
                candidate_id="scenario_total",
                value="800.0",
                scenario="low",
                quote=(
                    "The High Efficiency Case is driven by energy savings in software and hardware; "
                    "consumption reaches around 800 TWh by 2030 for data centre buildout."
                ),
            ),
            row(
                candidate_id="growth_increment",
                value="240.0",
                quote="Data centre electricity consumption increases by around 240 TWh in the United States to 2030.",
            ),
            row(
                candidate_id="incremental",
                value="250.0",
                year="2024",
                quote="Data centres accounted for around 250 TWh of incremental electricity consumption between 2014 and 2024.",
            ),
            row(
                candidate_id="from_to",
                value="10.0",
                quote="Annual demand from data centres increases from just over 10 TWh today to 25 TWh by 2030.",
            ),
            row(
                candidate_id="wrong_value_year",
                value="1300.0",
                quote="Global electricity generation to supply data centres grows from 460 TWh in 2024 to over 1 000 TWh in 2030 and 1 300 TWh in 2035.",
            ),
        ]

        claims = create_priority_review.top_claim_rows(rows)

        self.assertEqual({claim["candidate_ids"] for claim in claims}, {"explicit_total", "scenario_total"})
        self.assertEqual(claims[0]["claim_type"], "total_consumption")
        self.assertEqual(create_priority_review.claim_type(rows[0]), "chart_axis_noise")
        self.assertEqual(create_priority_review.claim_type(rows[3]), "growth_increment")
        self.assertEqual(create_priority_review.claim_type(rows[4]), "growth_increment")
        self.assertEqual(create_priority_review.claim_type(rows[5]), "growth_increment")
        self.assertEqual(create_priority_review.claim_year(rows[6]), "2035")

    def test_top_claims_do_not_keep_global_scope_for_region_specific_quote(self):
        rows = [
            row(
                candidate_id="bad_global_scope",
                region="global",
                country="",
                value="180.0",
                year="2024",
                scenario="historical",
                quote=(
                    "Data centres accounted for around 180 TWh of electricity consumption "
                    "in 2024 in the United States."
                ),
            ),
            row(
                candidate_id="bad_us_scope",
                region="",
                country="United States",
                value="945.0",
                quote=(
                    "Data centre electricity consumption is set to more than double to around "
                    "945 TWh by 2030. The United States accounts for by far the largest growth."
                ),
            ),
        ]

        claims = create_priority_review.top_claim_rows(rows)

        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["country"], "United States")
        self.assertEqual(claims[0]["region"], "")
        self.assertEqual(claims[0]["value"], "180.0")


if __name__ == "__main__":
    unittest.main()
