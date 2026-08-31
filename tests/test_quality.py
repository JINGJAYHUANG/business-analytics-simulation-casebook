from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from business_analytics_casebook.quality import analyze_quality
from business_analytics_casebook.synthetic import generate_synthetic_company


class QualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_synthetic_company(cls.data)
        cls.result = analyze_quality(cls.data / "qa_events.csv")
        cls.weeks = cls.result["weekly_metrics"]
        cls.decision = cls.result["decision"]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_two_weeks(self):
        self.assertEqual(len(self.weeks), 2)

    def test_each_week_has_200_workflows(self):
        self.assertTrue(all(row["workflow_count"] == 200 for row in self.weeks))

    def test_duplicate_events_detected_in_week_two(self):
        self.assertEqual(self.weeks[0]["duplicate_event_count"], 0)
        self.assertGreater(self.weeks[1]["duplicate_event_count"], 0)

    def test_naive_failure_rate_increases(self):
        self.assertGreater(float(self.weeks[1]["naive_raw_event_failure_rate"]), float(self.weeks[0]["naive_raw_event_failure_rate"]))

    def test_final_failure_rate_stable(self):
        self.assertAlmostEqual(float(self.weeks[0]["final_failure_rate"]), float(self.weeks[1]["final_failure_rate"]), places=8)

    def test_corrected_delta_zero(self):
        self.assertAlmostEqual(float(self.decision["corrected_week_over_week_change"]), 0.0, places=8)

    def test_naive_delta_material(self):
        self.assertGreater(float(self.decision["naive_week_over_week_change"]), 0.05)

    def test_duplicate_rate_positive(self):
        self.assertGreater(float(self.decision["duplicate_event_rate"]), 0)

    def test_decision_status(self):
        self.assertEqual(self.decision["status"], "FIX_METRIC_PIPELINE_AND_SOURCE_RELIABILITY")

    def test_root_causes_not_empty(self):
        self.assertTrue(self.result["root_causes"])

    def test_workflow_details_400(self):
        self.assertEqual(len(self.result["workflow_details"]), 400)

    def test_workflow_ids_unique(self):
        ids = [row["workflow_id"] for row in self.result["workflow_details"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_first_pass_yield_declines(self):
        self.assertLess(float(self.weeks[1]["first_pass_yield"]), float(self.weeks[0]["first_pass_yield"]))

    def test_final_success_remains_high(self):
        self.assertTrue(all(float(row["final_success_rate"]) >= 0.95 for row in self.weeks))

    def test_customer_impact_rate_matches_final_failure(self):
        for row in self.weeks:
            self.assertAlmostEqual(float(row["customer_impact_rate"]), float(row["final_failure_rate"]), places=8)

    def test_denominator_finding_is_critical(self):
        finding = next(item for item in self.result["findings"] if item["rule_id"] == "DENOMINATOR_SHIFT")
        self.assertEqual(finding["severity"], "critical")


def _make_week_metric_test(metric):
    def test(self):
        for row in self.weeks:
            value = float(row[metric])
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)
    return test


for _metric in (
    "naive_raw_event_failure_rate", "deduped_event_failure_rate", "first_pass_yield",
    "final_success_rate", "final_failure_rate", "retry_rate", "customer_impact_rate",
):
    setattr(QualityTests, f"test_metric_bounds_{_metric}", _make_week_metric_test(_metric))


if __name__ == "__main__":
    unittest.main()
