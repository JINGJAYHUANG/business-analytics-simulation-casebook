from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from business_analytics_casebook.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(argv)
        return code, output.getvalue()

    def test_inspect_lists_four_cases(self):
        code, output = self.call(["inspect"])
        self.assertEqual(code, 0)
        self.assertIn("supply_chain", output)
        self.assertIn("quality", output)

    def test_inspect_case(self):
        code, output = self.call(["inspect", "experiment"])
        self.assertEqual(code, 0)
        self.assertIn("A/B", output)

    def test_inspect_unknown_case(self):
        code, output = self.call(["inspect", "unknown"])
        self.assertEqual(code, 2)
        self.assertIn("unknown case_id", output)

    def test_generate(self):
        data = self.root / "data"
        code, output = self.call(["generate", "--data-dir", str(data)])
        self.assertEqual(code, 0)
        self.assertTrue((data / "orders.csv").exists())
        self.assertIn("supply_chain_lanes", output)

    def test_generate_refuses_nonempty(self):
        data = self.root / "data"
        data.mkdir()
        (data / "x").write_text("x")
        code, output = self.call(["generate", "--data-dir", str(data)])
        self.assertEqual(code, 2)
        self.assertIn("not empty", output)

    def test_validate(self):
        data = self.root / "data"
        main(["generate", "--data-dir", str(data)])
        code, output = self.call(["validate", "--data-dir", str(data), "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"errors":0', output)

    def test_run_and_verify(self):
        data = self.root / "data"
        run = self.root / "run"
        main(["generate", "--data-dir", str(data)])
        code, _ = self.call(["run", "--data-dir", str(data), "--output-dir", str(run), "--fixed-time", "2026-09-01T00:00:00Z"])
        self.assertEqual(code, 0)
        code, output = self.call(["verify", "--run-dir", str(run)])
        self.assertEqual(code, 0)
        self.assertIn('"status":"verified"', output)

    def test_demo(self):
        code, output = self.call(["demo", "--root", str(self.root / "demo"), "--fixed-time", "2026-09-01T00:00:00Z", "--overwrite"])
        self.assertEqual(code, 0)
        self.assertIn('"verification":"verified"', output)

    def test_naive_time_returns_error(self):
        code, output = self.call(["demo", "--root", str(self.root / "demo"), "--fixed-time", "2026-09-01T00:00:00", "--overwrite"])
        self.assertEqual(code, 2)
        self.assertIn("timezone", output)

    def test_init_preview_does_not_write(self):
        target = self.root / "starter"
        code, output = self.call(["init", "--target", str(target)])
        self.assertEqual(code, 0)
        self.assertFalse(target.exists())
        self.assertIn('"applied":false', output)

    def test_init_apply_writes(self):
        target = self.root / "starter"
        code, output = self.call(["init", "--target", str(target), "--apply"])
        self.assertEqual(code, 0)
        self.assertTrue((target / "metric_contracts.json").exists())
        self.assertIn('"applied":true', output)

    def test_compare(self):
        first = self.root / "a"
        second = self.root / "b"
        main(["demo", "--root", str(first), "--fixed-time", "2026-09-01T00:00:00Z", "--overwrite"])
        main(["demo", "--root", str(second), "--fixed-time", "2026-09-01T00:00:00Z", "--overwrite"])
        code, output = self.call(["compare", "--baseline", str(first / "output"), "--candidate", str(second / "output")])
        self.assertEqual(code, 0)
        self.assertIn('"accounting_net_revenue_delta":0.0', output)


if __name__ == "__main__":
    unittest.main()
