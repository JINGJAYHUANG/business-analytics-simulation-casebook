from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from business_analytics_casebook.contracts import CONTRACTS, raise_for_errors, validate_data_directory
from business_analytics_casebook.synthetic import generate_synthetic_company


class SyntheticAndContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name) / "data"
        self.counts = generate_synthetic_company(self.data_dir)

    def tearDown(self):
        self.temp.cleanup()

    def test_expected_file_count(self):
        self.assertEqual(len(list(self.data_dir.iterdir())), 10)

    def test_expected_lane_count(self):
        self.assertEqual(self.counts["supply_chain_lanes"], 80)

    def test_expected_order_count(self):
        self.assertEqual(self.counts["orders"], 64)

    def test_expected_experiment_cells(self):
        self.assertEqual(self.counts["experiment_cells"], 8)

    def test_expected_qa_events(self):
        self.assertGreater(self.counts["qa_events"], 400)

    def test_generation_is_deterministic(self):
        other = Path(self.temp.name) / "other"
        generate_synthetic_company(other)
        left = {p.name: p.read_bytes() for p in self.data_dir.iterdir()}
        right = {p.name: p.read_bytes() for p in other.iterdir()}
        self.assertEqual(left, right)

    def test_public_config_marks_synthetic(self):
        payload = json.loads((self.data_dir / "casebook_config.json").read_text())
        self.assertTrue(payload["synthetic"])

    def test_metric_contracts_mark_synthetic(self):
        payload = json.loads((self.data_dir / "metric_contracts.json").read_text())
        self.assertTrue(payload["synthetic"])

    def test_validation_has_no_errors(self):
        findings = validate_data_directory(self.data_dir)
        self.assertFalse([item for item in findings if item["severity"] == "error"])

    def test_validation_reports_expected_warnings(self):
        findings = validate_data_directory(self.data_dir)
        self.assertGreaterEqual(sum(1 for item in findings if item["severity"] == "warning"), 2)

    def test_raise_for_errors_accepts_warnings(self):
        raise_for_errors([{"severity": "warning", "rule_id": "X", "message": "x"}])

    def test_raise_for_errors_rejects_errors(self):
        with self.assertRaises(ValueError):
            raise_for_errors([{"severity": "error", "rule_id": "X", "message": "x"}])

    def test_missing_file_is_error(self):
        (self.data_dir / "orders.csv").unlink()
        findings = validate_data_directory(self.data_dir)
        self.assertTrue(any(item["rule_id"] == "MISSING_FILE" for item in findings))

    def test_empty_file_is_error(self):
        (self.data_dir / "orders.csv").write_text("order_id\n", encoding="utf-8")
        findings = validate_data_directory(self.data_dir)
        self.assertTrue(any(item["rule_id"] == "EMPTY_FILE" for item in findings))

    def test_missing_column_is_error(self):
        path = self.data_dir / "orders.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["order_id", "customer_id"])
            writer.writeheader()
            writer.writerows({"order_id": row["order_id"], "customer_id": row["customer_id"]} for row in rows)
        findings = validate_data_directory(self.data_dir)
        self.assertTrue(any(item["rule_id"] == "MISSING_COLUMN" for item in findings))

    def test_bad_metric_schema_version_is_error(self):
        path = self.data_dir / "metric_contracts.json"
        payload = json.loads(path.read_text())
        payload["schema_version"] = "9.9"
        path.write_text(json.dumps(payload), encoding="utf-8")
        findings = validate_data_directory(self.data_dir)
        self.assertTrue(any(item["rule_id"] == "METRIC_SCHEMA_VERSION" for item in findings))

    def test_duplicate_metric_id_is_error(self):
        path = self.data_dir / "metric_contracts.json"
        payload = json.loads(path.read_text())
        payload["metrics"].append(dict(payload["metrics"][0]))
        path.write_text(json.dumps(payload), encoding="utf-8")
        findings = validate_data_directory(self.data_dir)
        self.assertTrue(any(item["rule_id"] == "DUPLICATE_METRIC_ID" for item in findings))

    def test_all_contract_files_exist(self):
        for contract in CONTRACTS:
            with self.subTest(contract=contract.file_name):
                self.assertTrue((self.data_dir / contract.file_name).exists())


def _make_contract_test(contract):
    def test(self):
        with (self.data_dir / contract.file_name).open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(rows)
        self.assertTrue(set(contract.required_columns).issubset(rows[0]))
    return test


for _index, _contract in enumerate(CONTRACTS, start=1):
    setattr(SyntheticAndContractTests, f"test_contract_{_index:02d}_{_contract.file_name.replace('.', '_')}", _make_contract_test(_contract))


if __name__ == "__main__":
    unittest.main()
