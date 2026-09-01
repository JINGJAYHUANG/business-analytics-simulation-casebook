from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from .canonical import quantize_money, read_csv, stable_float


def _decimal(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value))


def analyze_accounting(data_dir: Path) -> dict[str, object]:
    orders = read_csv(data_dir / "orders.csv")
    lines = read_csv(data_dir / "order_lines.csv")
    invoices = read_csv(data_dir / "invoices.csv")
    payments_raw = read_csv(data_dir / "payments.csv")
    returns_raw = read_csv(data_dir / "returns.csv")

    order_map = {row["order_id"]: row for row in orders}
    line_map = {row["line_id"]: row for row in lines}
    invoice_map = {row["invoice_id"]: row for row in invoices}
    invoice_by_order = {row["order_id"]: row for row in invoices}

    duplicate_payment_ids = [key for key, count in Counter(row["payment_id"] for row in payments_raw).items() if count > 1]
    deduped_payments: dict[str, dict[str, str]] = {}
    for row in payments_raw:
        deduped_payments.setdefault(row["payment_id"], row)
    orphan_payments = [row for row in deduped_payments.values() if row["invoice_id"] not in invoice_map]
    valid_payments = [row for row in deduped_payments.values() if row["invoice_id"] in invoice_map]

    orphan_returns = [row for row in returns_raw if row["line_id"] not in line_map]
    valid_returns = [row for row in returns_raw if row["line_id"] in line_map]
    returns_by_line: dict[str, int] = defaultdict(int)
    for row in valid_returns:
        returns_by_line[row["line_id"]] += int(row["quantity"])

    payments_by_invoice: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    payment_count_raw: Counter[str] = Counter()
    for row in payments_raw:
        payment_count_raw[row["invoice_id"]] += 1
    for row in valid_payments:
        if row["payment_status"] == "posted":
            payments_by_invoice[row["invoice_id"]] += _decimal(row["amount"])

    order_lines: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in lines:
        order_lines[row["order_id"]].append(row)

    order_fact: list[dict[str, object]] = []
    gross_revenue = Decimal("0")
    return_revenue = Decimal("0")
    net_cogs = Decimal("0")
    invoice_total = Decimal("0")
    cash_collected = Decimal("0")
    reconciliation_residual = Decimal("0")

    for order_id, order in sorted(order_map.items()):
        if order["status"] != "completed":
            continue
        invoice = invoice_by_order[order_id]
        order_gross = Decimal("0")
        order_return_revenue = Decimal("0")
        order_cogs = Decimal("0")
        order_return_cogs = Decimal("0")
        for line in order_lines[order_id]:
            quantity = int(line["quantity"])
            returned_quantity = returns_by_line.get(line["line_id"], 0)
            if returned_quantity > quantity:
                raise ValueError(f"returned quantity exceeds sold quantity for {line['line_id']}")
            price = _decimal(line["unit_price"])
            cost = _decimal(line["unit_cost"])
            order_gross += Decimal(quantity) * price
            order_return_revenue += Decimal(returned_quantity) * price
            order_cogs += Decimal(quantity) * cost
            order_return_cogs += Decimal(returned_quantity) * cost
        order_net_revenue = order_gross - order_return_revenue
        order_net_cogs = order_cogs - order_return_cogs
        invoiced = _decimal(invoice["invoice_total"])
        paid = payments_by_invoice[invoice["invoice_id"]]
        expected_invoice = order_gross + _decimal(invoice["shipping_fee"]) + _decimal(invoice["tax_amount"])
        residual = invoiced - expected_invoice
        order_fact.append({
            "order_id": order_id,
            "customer_id": order["customer_id"],
            "order_date": order["order_date"],
            "channel": order["channel"],
            "region": order["region"],
            "gross_revenue": quantize_money(order_gross),
            "return_revenue": quantize_money(order_return_revenue),
            "net_revenue": quantize_money(order_net_revenue),
            "net_cogs": quantize_money(order_net_cogs),
            "gross_profit": quantize_money(order_net_revenue - order_net_cogs),
            "invoice_total": quantize_money(invoiced),
            "cash_collected": quantize_money(paid),
            "accounts_receivable": quantize_money(invoiced - paid),
            "invoice_reconciliation_residual": quantize_money(residual),
        })
        gross_revenue += order_gross
        return_revenue += order_return_revenue
        net_cogs += order_net_cogs
        invoice_total += invoiced
        cash_collected += paid
        reconciliation_residual += residual

    net_revenue = gross_revenue - return_revenue
    gross_profit = net_revenue - net_cogs
    accounts_receivable = invoice_total - cash_collected
    gross_margin = gross_profit / net_revenue if net_revenue else Decimal("0")
    days_in_quarter = Decimal("91")
    dso = (accounts_receivable / invoice_total * days_in_quarter) if invoice_total else Decimal("0")

    naive_revenue = Decimal("0")
    for line in lines:
        order = order_map[line["order_id"]]
        if order["status"] != "completed":
            continue
        invoice = invoice_by_order[line["order_id"]]
        multiplier = max(1, payment_count_raw[invoice["invoice_id"]])
        naive_revenue += Decimal(int(line["quantity"])) * _decimal(line["unit_price"]) * Decimal(multiplier)
    join_inflation = naive_revenue - gross_revenue
    join_inflation_rate = join_inflation / gross_revenue if gross_revenue else Decimal("0")

    channel_summary: dict[str, dict[str, Decimal | int]] = {}
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in order_fact:
        grouped[str(row["channel"])].append(row)
    for channel, members in sorted(grouped.items()):
        channel_net = sum((_decimal(row["net_revenue"]) for row in members), Decimal("0"))
        channel_gp = sum((_decimal(row["gross_profit"]) for row in members), Decimal("0"))
        channel_summary[channel] = {
            "orders": len(members),
            "net_revenue": quantize_money(channel_net),
            "gross_profit": quantize_money(channel_gp),
            "gross_margin": stable_float(float(channel_gp / channel_net if channel_net else 0), 6),
        }

    findings: list[dict[str, object]] = []
    if duplicate_payment_ids:
        findings.append({
            "finding_id": "AC-001",
            "severity": "high",
            "rule_id": "DUPLICATE_PAYMENT_EVENT",
            "message": f"Duplicate payment identifiers detected: {', '.join(duplicate_payment_ids)}",
            "impact": "Raw payment sums would overstate cash collection unless payment events are deduplicated.",
            "remediation": "Enforce payment_id uniqueness before aggregation and retain a rejected-row audit table.",
        })
    if orphan_payments:
        findings.append({
            "finding_id": "AC-002",
            "severity": "high",
            "rule_id": "ORPHAN_PAYMENT",
            "message": f"{len(orphan_payments)} payment event(s) do not match a known invoice.",
            "impact": "Unmatched cash cannot be safely assigned to revenue or receivables.",
            "remediation": "Route unmatched payments to suspense and investigate the source-system key.",
        })
    if orphan_returns:
        findings.append({
            "finding_id": "AC-003",
            "severity": "high",
            "rule_id": "ORPHAN_RETURN",
            "message": f"{len(orphan_returns)} return event(s) do not match a known order line.",
            "impact": "Return allowances and inventory movement would be incomplete.",
            "remediation": "Reject or quarantine unmatched returns until line-level identity is restored.",
        })
    if join_inflation > 0:
        findings.append({
            "finding_id": "AC-004",
            "severity": "critical",
            "rule_id": "JOIN_EXPLOSION",
            "message": f"A naive line-to-payment join overstates gross revenue by {quantize_money(join_inflation)} USD ({join_inflation_rate:.2%}).",
            "impact": "Many-to-many joins multiply line revenue when an invoice has multiple payments.",
            "remediation": "Aggregate lines, payments, and returns to their intended grain before joining at order_id.",
        })
    if reconciliation_residual != 0:
        findings.append({
            "finding_id": "AC-005",
            "severity": "critical",
            "rule_id": "INVOICE_RECONCILIATION",
            "message": f"Invoice reconciliation residual is {quantize_money(reconciliation_residual)} USD.",
            "impact": "Reported revenue and billed amounts do not reconcile.",
            "remediation": "Trace price, shipping, tax, credit memo, and rounding fields before publication.",
        })

    return {
        "summary": {
            "completed_orders": len(order_fact),
            "gross_revenue": quantize_money(gross_revenue),
            "return_revenue": quantize_money(return_revenue),
            "net_revenue": quantize_money(net_revenue),
            "net_cogs": quantize_money(net_cogs),
            "gross_profit": quantize_money(gross_profit),
            "gross_margin": stable_float(float(gross_margin), 6),
            "invoice_total": quantize_money(invoice_total),
            "cash_collected": quantize_money(cash_collected),
            "accounts_receivable": quantize_money(accounts_receivable),
            "dso_proxy_days": stable_float(float(dso), 4),
            "naive_join_gross_revenue": quantize_money(naive_revenue),
            "join_inflation_amount": quantize_money(join_inflation),
            "join_inflation_rate": stable_float(float(join_inflation_rate), 6),
            "duplicate_payment_ids": len(duplicate_payment_ids),
            "orphan_payments": len(orphan_payments),
            "orphan_returns": len(orphan_returns),
            "invoice_reconciliation_residual": quantize_money(reconciliation_residual),
        },
        "order_fact": order_fact,
        "channel_summary": [
            {"channel": channel, **values} for channel, values in channel_summary.items()
        ],
        "rejected_rows": {
            "duplicate_payment_ids": duplicate_payment_ids,
            "orphan_payments": orphan_payments,
            "orphan_returns": orphan_returns,
        },
        "findings": findings,
    }
