from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from business_analytics_casebook.clustering import (
    ARCHETYPE_TARGETS,
    FEATURES,
    POLICIES,
    _standardize,
    analyze_supply_chain,
    kmeans,
    load_lanes,
    silhouette_score,
)
from business_analytics_casebook.synthetic import generate_synthetic_company


class ClusteringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_synthetic_company(cls.data)
        cls.rows = load_lanes(cls.data / "supply_chain_lanes.csv")
        cls.result = analyze_supply_chain(cls.data / "supply_chain_lanes.csv")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_loads_80_lanes(self):
        self.assertEqual(len(self.rows), 80)

    def test_features_are_present(self):
        for feature in FEATURES:
            self.assertIn(feature, self.rows[0])

    def test_standardization_means_approximately_zero(self):
        matrix, _ = _standardize(self.rows)
        for column in range(len(FEATURES)):
            self.assertAlmostEqual(sum(row[column] for row in matrix) / len(matrix), 0.0, places=12)

    def test_selected_k_is_four(self):
        self.assertEqual(self.result["selected_k"], 4)

    def test_silhouette_is_high(self):
        self.assertGreater(self.result["selected_silhouette"], 0.60)

    def test_all_lanes_assigned(self):
        self.assertEqual(len(self.result["assignments"]), 80)

    def test_four_profiles(self):
        self.assertEqual(len(self.result["profiles"]), 4)

    def test_semantic_labels_complete(self):
        self.assertEqual({row["segment"] for row in self.result["profiles"]}, set(ARCHETYPE_TARGETS))

    def test_policy_rows_complete(self):
        self.assertEqual({row["segment"] for row in self.result["policies"]}, set(POLICIES))

    def test_cluster_sizes_sum_to_rows(self):
        self.assertEqual(sum(row["lane_count"] for row in self.result["profiles"]), 80)

    def test_unit_shares_sum_to_one(self):
        self.assertAlmostEqual(sum(float(row["annual_units_share"]) for row in self.result["profiles"]), 1.0, places=12)

    def test_kmeans_is_deterministic(self):
        matrix, _ = _standardize(self.rows)
        first, centroids_a = kmeans(matrix, 4)
        second, centroids_b = kmeans(matrix, 4)
        self.assertEqual(first, second)
        self.assertEqual(centroids_a, centroids_b)

    def test_silhouette_rejects_singletons(self):
        self.assertEqual(silhouette_score([[0.0], [1.0]], [0, 1]), -1.0)

    def test_invalid_k_low(self):
        with self.assertRaises(ValueError):
            kmeans([[0.0], [1.0], [2.0]], 1)

    def test_invalid_k_high(self):
        with self.assertRaises(ValueError):
            kmeans([[0.0], [1.0], [2.0]], 3)

    def test_assignments_have_unique_lane_ids(self):
        ids = [row["lane_id"] for row in self.result["assignments"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_constrained_segment_has_worst_service(self):
        by_segment = {row["segment"]: row for row in self.result["profiles"]}
        constrained = by_segment["constrained_recovery"]
        self.assertEqual(constrained["lead_time_days"], max(row["lead_time_days"] for row in by_segment.values()))

    def test_cost_efficient_has_lowest_cost(self):
        by_segment = {row["segment"]: row for row in self.result["profiles"]}
        efficient = by_segment["cost_efficient_routine"]
        self.assertEqual(efficient["landed_cost_per_unit"], min(row["landed_cost_per_unit"] for row in by_segment.values()))


def _make_k_test(k):
    def test(self):
        matrix, _ = _standardize(self.rows)
        assignments, _ = kmeans(matrix, k)
        self.assertEqual(len(assignments), 80)
        self.assertEqual(len(set(assignments)), k)
    return test


for _k in range(2, 7):
    setattr(ClusteringTests, f"test_kmeans_k_{_k}", _make_k_test(_k))


def _make_profile_test(label):
    def test(self):
        profile = next(row for row in self.result["profiles"] if row["segment"] == label)
        self.assertGreater(profile["lane_count"], 0)
        self.assertGreater(profile["annual_units"], 0)
    return test


for _label in ARCHETYPE_TARGETS:
    setattr(ClusteringTests, f"test_profile_{_label}", _make_profile_test(_label))


if __name__ == "__main__":
    unittest.main()
