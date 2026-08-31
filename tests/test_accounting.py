from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from business_analytics_casebook.accounting import analyze_accounting
from business_analytics_casebook.synthetic import generate_synthetic_company


class AccountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.data = Path(cls.temp.name) / "data"
        generate_synthetic_company(cls.data)
        cls.result = analyze_accounting(cls.data)
        cls.summary = cls.result["summary"]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_completed_order_count(self):
        self.assertEqual(self.summary["completed_orders"], 61)

    def test_duplicate_payment_detected(self):
        self.assertEqual(self.summary["duplicate_payment_ids"], 1)

    def test_orphan_payment_detected(self):
        self.assertEqual(self.summary["orphan_payments"], 1)

    def test_orphan_return_detected(self):
        self.assertEqual(self.summary["orphan_returns"], 1)

    def test_join_inflation_positive(self):
        self.assertGreater(Decimal(self.summary["join_inflation_amount"]), 0)

    def test_join_inflation_rate_material(self):
        self.assertGreater(float(self.summary["join_inflation_rate"]), 0.10)

    def test_reconciliation_zero(self):
        self.assertEqual(Decimal(self.summary["invoice_reconciliation_residual"]), Decimal("0.00"))

    def test_net_revenue_formula(self):
        self.assertEqual(
            Decimal(self.summary["gross_revenue"]) - Decimal(self.summary["return_revenue"]),
            Decimal(self.summary["net_revenue"]),
        )

    def test_gross_profit_formula(self):
        self.assertEqual(
            Decimal(self.summary["net_revenue"]) - Decimal(self.summary["net_cogs"]),
            Decimal(self.summary["gross_profit"]),
        )

    def test_accounts_receivable_formula(self):
        self.assertEqual(
            Decimal(self.summary["invoice_total"]) - Decimal(self.summary["cash_collected"]),
            Decimal(self.summary["accounts_receivable"]),
        )

    def test_partial_receivable_exists(self):
        self.assertGreater(Decimal(self.summary["accounts_receivable"]), 0)

    def test_dso_proxy_positive(self):
        self.assertGreater(float(self.summary["dso_proxy_days"]), 0)

    def test_order_fact_count(self):
        self.assertEqual(len(self.result["order_fact"]), self.summary["completed_orders"])

    def test_order_fact_ids_unique(self):
        ids = [row["order_id"] for row in self.result["order_fact"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_channel_orders_reconcile(self):
        self.assertEqual(sum(row["orders"] for row in self.result["channel_summary"]), self.summary["completed_orders"])

    def test_channel_revenue_reconciles(self):
        total = sum(Decimal(row["net_revenue"]) for row in self.result["channel_summary"])
        self.assertEqual(total, Decimal(self.summary["net_revenue"]))

    def test_critical_join_finding_exists(self):
        finding = next(item for item in self.result["findings"] if item["rule_id"] == "JOIN_EXPLOSION")
        self.assertEqual(finding["severity"], "critical")

    def test_rejected_rows_preserved(self):
        self.assertEqual(len(self.result["rejected_rows"]["orphan_payments"]), 1)
        self.assertEqual(len(self.result["rejected_rows"]["orphan_returns"]), 1)


def _make_order_field_test(field):
    def test(self):
        for row in self.result["order_fact"]:
            self.assertIn(field, row)
            self.assertNotEqual(row[field], "")
    return test


for _field in (
    "order_id", "gross_revenue", "return_revenue", "net_revenue", "net_cogs",
    "gross_profit", "invoice_total", "cash_collected", "accounts_receivable",
):
    setattr(AccountingTests, f"test_order_fact_field_{_field}", _make_order_field_test(_field))


if __name__ == "__main__":
    unittest.main()
