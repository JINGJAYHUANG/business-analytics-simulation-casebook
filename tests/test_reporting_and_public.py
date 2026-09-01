from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from business_analytics_casebook.reporting import html_document, markdown_table


REPO = Path(__file__).resolve().parents[1]


class ReportingAndPublicTests(unittest.TestCase):
    def test_markdown_table_escapes_pipe(self):
        text = markdown_table([{"x": "a|b"}], [("x", "X")])
        self.assertIn("a\\|b", text)

    def test_html_document_escapes_title(self):
        text = html_document("<unsafe>", "<p>ok</p>")
        self.assertIn("&lt;unsafe&gt;", text)
        self.assertIn("<p>ok</p>", text)

    def test_catalog_copies_match(self):
        self.assertEqual((REPO / "catalog" / "cases.json").read_bytes(), (REPO / "src" / "business_analytics_casebook" / "catalog" / "cases.json").read_bytes())

    def test_catalog_has_four_cases(self):
        payload = json.loads((REPO / "catalog" / "cases.json").read_text())
        self.assertEqual(len(payload["cases"]), 4)

    def test_all_cases_mark_synthetic_catalog(self):
        payload = json.loads((REPO / "catalog" / "cases.json").read_text())
        self.assertTrue(payload["synthetic"])

    def test_readme_states_independent(self):
        text = (REPO / "README.md").read_text()
        self.assertIn("independent educational and portfolio project", text)

    def test_readme_rejects_employment_claim(self):
        text = (REPO / "README.md").read_text()
        self.assertIn("claims that a virtual simulation was employment", text)

    def test_chinese_readme_exists(self):
        self.assertTrue((REPO / "docs" / "README.zh-CN.md").exists())

    def test_four_case_briefs(self):
        self.assertEqual(len(list((REPO / "case_briefs").glob("*.md"))), 4)

    def test_three_sql_examples(self):
        self.assertEqual(len(list((REPO / "sql").glob("*.sql"))), 3)

    def test_public_audit_script(self):
        result = subprocess.run([sys.executable, "scripts/public_audit.py", "."], cwd=REPO, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_markdown_links_script(self):
        result = subprocess.run([sys.executable, "scripts/check_markdown_links.py", "."], cwd=REPO, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rebuild_examples_script(self):
        env = {**__import__("os").environ, "PYTHONPATH": str(REPO / "src")}
        result = subprocess.run([sys.executable, "scripts/rebuild_examples.py", "--check"], cwd=REPO, text=True, capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_red_team_script(self):
        env = {**__import__("os").environ, "PYTHONPATH": str(REPO / "src")}
        result = subprocess.run([sys.executable, "scripts/red_team.py", "examples/synthetic_company/output"], cwd=REPO, text=True, capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"detected":6', result.stdout)

    def test_no_proprietary_brand_in_public_text(self):
        forbidden = "Buhi" + " Supply"
        for path in REPO.rglob("*"):
            if path.name == "public_audit.py":
                continue
            if path.is_file() and path.suffix.lower() in {".md", ".py", ".json", ".csv", ".sql", ".toml", ".yml", ".yaml"}:
                self.assertNotIn(forbidden, path.read_text(encoding="utf-8", errors="ignore"))


def _make_output_presence_test(relative):
    def test(self):
        self.assertTrue((REPO / "examples" / "synthetic_company" / "output" / relative).exists())
    return test


for _idx, _relative in enumerate([
    "supply_chain/report.html",
    "supply_chain/lane_assignments.csv",
    "accounting/order_fact.csv",
    "accounting/rejected_rows.json",
    "experiment/decision.json",
    "experiment/segment_effects.csv",
    "quality/weekly_metrics.csv",
    "quality/workflow_details.csv",
    "executive/quarterly_report.html",
    "executive/decision_register.csv",
    "casebook.sqlite",
    "events.jsonl",
    "artifact_manifest.json",
    "run_manifest.json",
], start=1):
    setattr(ReportingAndPublicTests, f"test_committed_output_{_idx:02d}", _make_output_presence_test(_relative))


if __name__ == "__main__":
    unittest.main()
