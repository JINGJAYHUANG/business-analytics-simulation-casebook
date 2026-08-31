from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from business_analytics_casebook.canonical import read_json
from business_analytics_casebook.integrity import verify_event_chain, verify_run
from business_analytics_casebook.runner import build_demo, compare_runs, run_casebook
from business_analytics_casebook.synthetic import generate_synthetic_company


class RunnerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.demo = self.root / "demo"
        self.result = build_demo(self.demo, "2026-09-01T00:00:00Z", overwrite=True)
        self.run = self.demo / "output"

    def tearDown(self):
        self.temp.cleanup()

    def test_build_demo_verified(self):
        self.assertEqual(self.result["verification"], "verified")

    def test_verify_run(self):
        result = verify_run(self.run)
        self.assertEqual(result["status"], "verified")

    def test_artifact_count_matches_manifest(self):
        manifest = read_json(self.run / "artifact_manifest.json")
        self.assertEqual(manifest["artifact_count"], self.result["artifact_count"])

    def test_event_chain_final_hash(self):
        run_manifest = read_json(self.run / "run_manifest.json")
        self.assertEqual(verify_event_chain(self.run / "events.jsonl"), run_manifest["final_event_hash"])

    def test_sqlite_exists(self):
        self.assertTrue((self.run / "casebook.sqlite").exists())

    def test_sqlite_contains_expected_tables(self):
        connection = sqlite3.connect(self.run / "casebook.sqlite")
        try:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            connection.close()
        for table in {"raw_orders", "accounting_order_fact", "experiment_segments", "quality_weekly_metrics", "findings"}:
            self.assertIn(table, tables)

    def test_same_inputs_and_time_are_byte_deterministic(self):
        second = self.root / "second"
        build_demo(second, "2026-09-01T00:00:00Z", overwrite=True)
        left = {p.relative_to(self.demo).as_posix(): p.read_bytes() for p in self.demo.rglob("*") if p.is_file()}
        right = {p.relative_to(second).as_posix(): p.read_bytes() for p in second.rglob("*") if p.is_file()}
        self.assertEqual(left, right)

    def test_different_time_changes_run_identity(self):
        second_data = self.root / "data2"
        generate_synthetic_company(second_data)
        second_run = self.root / "run2"
        result = run_casebook(second_data, second_run, "2026-09-02T00:00:00Z")
        self.assertNotEqual(result["run_id"], self.result["run_id"])

    def test_compare_identical_runs_has_zero_deltas(self):
        result = compare_runs(self.run, self.run)
        self.assertEqual(result["accounting_net_revenue_delta"], 0)
        self.assertEqual(result["experiment_stratified_effect_delta"], 0)
        self.assertEqual(result["quality_corrected_failure_change_delta"], 0)

    def test_output_refuses_nonempty_directory(self):
        data = self.root / "source"
        generate_synthetic_company(data)
        output = self.root / "occupied"
        output.mkdir()
        (output / "x.txt").write_text("x")
        with self.assertRaises(FileExistsError):
            run_casebook(data, output, "2026-09-01T00:00:00Z")

    def test_naive_timestamp_rejected(self):
        data = self.root / "source2"
        generate_synthetic_company(data)
        with self.assertRaises(ValueError):
            run_casebook(data, self.root / "bad", "2026-09-01T00:00:00")

    def test_alter_input_detected(self):
        target = self._copy("alter-input")
        (target / "inputs" / "orders.csv").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_alter_summary_detected(self):
        target = self._copy("alter-summary")
        (target / "executive" / "summary.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_delete_artifact_detected(self):
        target = self._copy("delete-artifact")
        (target / "experiment" / "decision.json").unlink()
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_inject_artifact_detected(self):
        target = self._copy("inject-artifact")
        (target / "extra.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_delete_event_detected(self):
        target = self._copy("delete-event")
        path = target / "events.jsonl"
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[1:]) + "\n")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_reorder_events_detected(self):
        target = self._copy("reorder-events")
        path = target / "events.jsonl"
        lines = path.read_text().splitlines()
        lines[1], lines[2] = lines[2], lines[1]
        path.write_text("\n".join(lines) + "\n")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_alter_sqlite_detected(self):
        target = self._copy("alter-sqlite")
        connection = sqlite3.connect(target / "casebook.sqlite")
        try:
            connection.execute("UPDATE metadata SET value='false' WHERE key='synthetic'")
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_alter_artifact_manifest_detected(self):
        target = self._copy("alter-manifest")
        path = target / "artifact_manifest.json"
        payload = json.loads(path.read_text())
        payload["artifact_count"] += 1
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_run(target)

    def test_executive_reports_exist(self):
        self.assertTrue((self.run / "executive" / "quarterly_report.md").exists())
        self.assertTrue((self.run / "executive" / "quarterly_report.html").exists())

    def test_all_case_reports_exist(self):
        for case in ("supply_chain", "accounting", "experiment", "quality"):
            with self.subTest(case=case):
                self.assertTrue((self.run / case / "report.md").exists())
                self.assertTrue((self.run / case / "report.html").exists())

    def _copy(self, name: str) -> Path:
        target = self.root / name
        shutil.copytree(self.run, target)
        return target


if __name__ == "__main__":
    unittest.main()
