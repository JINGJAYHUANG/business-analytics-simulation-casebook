from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from business_analytics_casebook.experiment import analyze_experiment, normal_cdf, two_proportion_test, wilson_interval
from business_analytics_casebook.synthetic import generate_synthetic_company


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_synthetic_company(cls.data)
        cls.result = analyze_experiment(cls.data / "experiment_cells.csv")
        cls.decision = cls.result["decision"]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_normal_cdf_zero(self):
        self.assertAlmostEqual(normal_cdf(0.0), 0.5)

    def test_wilson_bounds(self):
        low, high = wilson_interval(50, 100)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_wilson_empty(self):
        self.assertEqual(wilson_interval(0, 0), (0.0, 0.0))

    def test_two_proportion_requires_samples(self):
        with self.assertRaises(ValueError):
            two_proportion_test(0, 0, 1, 1)

    def test_aggregate_effect_negative(self):
        self.assertLess(float(self.result["aggregate"]["absolute_effect"]), 0)

    def test_stratified_effect_positive(self):
        self.assertGreater(float(self.decision["stratified_effect"]), 0)

    def test_stratified_effect_exact_fixture(self):
        self.assertAlmostEqual(float(self.decision["stratified_effect"]), 0.02, places=8)

    def test_simpsons_paradox_detected(self):
        self.assertTrue(self.decision["simpsons_paradox"])

    def test_overall_srm_passes(self):
        self.assertAlmostEqual(float(self.decision["srm_p_value"]), 1.0, places=8)

    def test_segment_mix_imbalance_material(self):
        self.assertGreater(float(self.decision["segment_mix_total_variation_distance"]), 0.40)

    def test_guardrail_effect_visible(self):
        self.assertGreater(float(self.decision["standardized_unsubscribe_effect"]), 0)

    def test_decision_requires_confirmation(self):
        self.assertEqual(self.decision["status"], "RE-RANDOMIZE_AND_CONFIRM")

    def test_four_segment_rows(self):
        self.assertEqual(len(self.result["segments"]), 4)

    def test_every_segment_effect_positive(self):
        self.assertTrue(all(float(row["absolute_effect"]) > 0 for row in self.result["segments"]))

    def test_segment_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(float(row["weight_in_target_population"]) for row in self.result["segments"]), 1.0, places=8)

    def test_finding_for_simpson_exists(self):
        finding = next(item for item in self.result["findings"] if item["rule_id"] == "SIMPSONS_PARADOX")
        self.assertEqual(finding["severity"], "critical")

    def test_finding_for_mix_exists(self):
        finding = next(item for item in self.result["findings"] if item["rule_id"] == "SEGMENT_IMBALANCE")
        self.assertEqual(finding["severity"], "high")


def _make_segment_test(segment):
    def test(self):
        row = next(item for item in self.result["segments"] if item["segment"] == segment)
        self.assertGreater(row["control_assigned"], 0)
        self.assertGreater(row["treatment_assigned"], 0)
        self.assertGreater(float(row["treatment_rate"]), float(row["control_rate"]))
        self.assertGreaterEqual(float(row["control_ci_low"]), 0.0)
        self.assertLessEqual(float(row["treatment_ci_high"]), 1.0)
    return test


for _segment in ("organic", "paid_search", "career_fair", "referral"):
    setattr(ExperimentTests, f"test_segment_{_segment}", _make_segment_test(_segment))


def _make_proportion_test(success_a, total_a, success_b, total_b, expected_sign):
    def test(self):
        result = two_proportion_test(success_a, total_a, success_b, total_b)
        effect = result["absolute_effect"]
        self.assertEqual(0 if effect == 0 else (1 if effect > 0 else -1), expected_sign)
        self.assertGreaterEqual(result["p_value"], 0.0)
        self.assertLessEqual(result["p_value"], 1.0)
    return test


for _idx, _values in enumerate([
    (10, 100, 12, 100, 1),
    (20, 100, 15, 100, -1),
    (5, 50, 5, 50, 0),
    (1, 10, 9, 10, 1),
    (9, 10, 1, 10, -1),
], start=1):
    setattr(ExperimentTests, f"test_two_proportion_matrix_{_idx}", _make_proportion_test(*_values))


if __name__ == "__main__":
    unittest.main()
