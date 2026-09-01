from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from .canonical import quantize_money, stable_noise, write_csv, write_json


COMPANY_NAME = "Asterline Supply Co."


def generate_synthetic_company(data_dir: Path) -> dict[str, int]:
    data_dir.mkdir(parents=True, exist_ok=True)
    lanes = _supply_chain_rows()
    accounting = _accounting_rows()
    experiment = _experiment_rows()
    qa_events = _qa_rows()

    write_csv(data_dir / "supply_chain_lanes.csv", lanes)
    for name, rows in accounting.items():
        write_csv(data_dir / f"{name}.csv", rows)
    write_csv(data_dir / "experiment_cells.csv", experiment)
    write_csv(data_dir / "qa_events.csv", qa_events)
    write_json(data_dir / "metric_contracts.json", _metric_contracts())
    write_json(
        data_dir / "casebook_config.json",
        {
            "schema_version": "1.0",
            "company": COMPANY_NAME,
            "quarter": "2026-Q2",
            "currency": "USD",
            "timezone": "UTC",
            "synthetic": True,
            "seed_method": "sha256-derived deterministic fixtures",
            "case_ids": ["supply_chain", "accounting", "experiment", "quality"],
        },
    )
    return {
        "supply_chain_lanes": len(lanes),
        "orders": len(accounting["orders"]),
        "order_lines": len(accounting["order_lines"]),
        "invoices": len(accounting["invoices"]),
        "payments": len(accounting["payments"]),
        "returns": len(accounting["returns"]),
        "experiment_cells": len(experiment),
        "qa_events": len(qa_events),
    }


def _supply_chain_rows() -> list[dict[str, object]]:
    profiles = [
        {
            "base": "A", "region": "North", "annual_units": 5800, "unit_cost": 13.8,
            "freight": 1.6, "lead": 9.5, "on_time": 0.975, "fill": 0.985,
            "defect": 0.006, "cv": 0.19, "expedite": 0.025, "carbon": 1.05,
        },
        {
            "base": "B", "region": "Central", "annual_units": 4200, "unit_cost": 9.8,
            "freight": 1.1, "lead": 17.0, "on_time": 0.925, "fill": 0.947,
            "defect": 0.012, "cv": 0.29, "expedite": 0.055, "carbon": 0.78,
        },
        {
            "base": "C", "region": "West", "annual_units": 5100, "unit_cost": 11.2,
            "freight": 1.8, "lead": 14.0, "on_time": 0.875, "fill": 0.905,
            "defect": 0.019, "cv": 0.68, "expedite": 0.155, "carbon": 1.15,
        },
        {
            "base": "D", "region": "International", "annual_units": 2900, "unit_cost": 12.9,
            "freight": 3.7, "lead": 31.0, "on_time": 0.755, "fill": 0.815,
            "defect": 0.044, "cv": 0.47, "expedite": 0.275, "carbon": 1.92,
        },
    ]
    rows: list[dict[str, object]] = []
    index = 0
    for profile in profiles:
        for item in range(20):
            index += 1
            key = f"lane-{profile['base']}-{item:02d}"
            annual_units = max(800, int(profile["annual_units"] * (1 + stable_noise(key + "units", 0.22))))
            unit_cost = profile["unit_cost"] * (1 + stable_noise(key + "unit", 0.07))
            freight = profile["freight"] * (1 + stable_noise(key + "freight", 0.12))
            lead = max(2.0, profile["lead"] * (1 + stable_noise(key + "lead", 0.14)))
            on_time = min(0.999, max(0.50, profile["on_time"] + stable_noise(key + "ot", 0.028)))
            fill = min(0.999, max(0.50, profile["fill"] + stable_noise(key + "fill", 0.025)))
            defect = min(0.15, max(0.001, profile["defect"] * (1 + stable_noise(key + "defect", 0.25))))
            demand_cv = min(1.2, max(0.05, profile["cv"] * (1 + stable_noise(key + "cv", 0.17))))
            expedite = min(0.60, max(0.0, profile["expedite"] * (1 + stable_noise(key + "exp", 0.25))))
            carbon = max(0.20, profile["carbon"] * (1 + stable_noise(key + "carbon", 0.12)))
            rows.append({
                "lane_id": f"LANE-{index:03d}",
                "supplier_id": f"SUP-{((index - 1) % 28) + 1:03d}",
                "region": profile["region"],
                "annual_units": annual_units,
                "unit_cost_usd": f"{unit_cost:.2f}",
                "inbound_freight_usd": f"{freight:.2f}",
                "lead_time_days": f"{lead:.2f}",
                "on_time_rate": f"{on_time:.4f}",
                "fill_rate": f"{fill:.4f}",
                "defect_rate": f"{defect:.4f}",
                "demand_cv": f"{demand_cv:.4f}",
                "expedite_rate": f"{expedite:.4f}",
                "carbon_kg_per_unit": f"{carbon:.3f}",
            })
    return rows


def _accounting_rows() -> dict[str, list[dict[str, object]]]:
    orders: list[dict[str, object]] = []
    order_lines: list[dict[str, object]] = []
    invoices: list[dict[str, object]] = []
    payments: list[dict[str, object]] = []
    returns: list[dict[str, object]] = []
    start = date(2026, 4, 1)
    line_counter = 0
    payment_counter = 0
    return_counter = 0

    for order_idx in range(1, 65):
        order_id = f"ORD-{order_idx:04d}"
        order_date = start + timedelta(days=(order_idx * 4) % 88)
        status = "cancelled" if order_idx % 19 == 0 else "completed"
        orders.append({
            "order_id": order_id,
            "customer_id": f"CUS-{((order_idx - 1) % 18) + 1:03d}",
            "order_date": order_date.isoformat(),
            "channel": ["direct", "partner", "marketplace"][order_idx % 3],
            "region": ["North", "South", "West", "Central"][order_idx % 4],
            "status": status,
        })
        line_count = 1 + (order_idx % 3)
        line_values: list[tuple[str, int, Decimal, Decimal]] = []
        for local_line in range(line_count):
            line_counter += 1
            line_id = f"LIN-{line_counter:05d}"
            quantity = 4 + ((order_idx * 3 + local_line * 5) % 17)
            unit_price = quantize_money(Decimal("48") + Decimal((order_idx + local_line * 7) % 34) + Decimal("0.50"))
            unit_cost = quantize_money(unit_price * Decimal("0.58") + Decimal((local_line + 1) % 3))
            order_lines.append({
                "line_id": line_id,
                "order_id": order_id,
                "sku": f"SKU-{((order_idx + local_line) % 12) + 1:03d}",
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
            })
            line_values.append((line_id, quantity, unit_price, unit_cost))
            if status == "completed" and (line_counter % 11 == 0 or order_idx % 17 == 0):
                return_counter += 1
                returned = 1 if quantity < 10 else 2
                returns.append({
                    "return_id": f"RET-{return_counter:04d}",
                    "line_id": line_id,
                    "return_date": (order_date + timedelta(days=12 + local_line)).isoformat(),
                    "quantity": returned,
                    "reason": ["damaged", "wrong_item", "customer_change"][return_counter % 3],
                })
        if status != "completed":
            continue
        gross = sum(Decimal(quantity) * price for _, quantity, price, _ in line_values)
        shipping = quantize_money(Decimal("18") + Decimal(order_idx % 5) * Decimal("2.50"))
        tax = quantize_money(gross * Decimal("0.045"))
        invoice_total = quantize_money(gross + shipping + tax)
        invoice_id = f"INV-{order_idx:04d}"
        invoices.append({
            "invoice_id": invoice_id,
            "order_id": order_id,
            "invoice_date": (order_date + timedelta(days=1)).isoformat(),
            "shipping_fee": shipping,
            "tax_amount": tax,
            "invoice_total": invoice_total,
        })
        if order_idx % 10 == 0:
            portions = [Decimal("0.55"), Decimal("0.45")]
        elif order_idx % 8 == 0:
            portions = [Decimal("0.70")]
        else:
            portions = [Decimal("1.00")]
        paid_total = Decimal("0")
        full_payment_schedule = sum(portions, Decimal("0")) == Decimal("1.00")
        for part_idx, fraction in enumerate(portions, start=1):
            payment_counter += 1
            amount = quantize_money(invoice_total * fraction)
            if full_payment_schedule and part_idx == len(portions):
                amount = quantize_money(invoice_total - paid_total)
            paid_total += amount
            row = {
                "payment_id": f"PAY-{payment_counter:05d}",
                "invoice_id": invoice_id,
                "payment_date": (order_date + timedelta(days=10 + part_idx * 7 + order_idx % 6)).isoformat(),
                "amount": amount,
                "payment_status": "posted",
            }
            payments.append(row)
            if order_idx == 20 and part_idx == 1:
                payments.append(dict(row))  # exact duplicate to exercise deduplication
    payments.append({
        "payment_id": "PAY-ORPHAN",
        "invoice_id": "INV-MISSING",
        "payment_date": "2026-06-28",
        "amount": "125.00",
        "payment_status": "posted",
    })
    returns.append({
        "return_id": "RET-ORPHAN",
        "line_id": "LIN-MISSING",
        "return_date": "2026-06-29",
        "quantity": 1,
        "reason": "unknown_reference",
    })
    return {
        "orders": orders,
        "order_lines": order_lines,
        "invoices": invoices,
        "payments": payments,
        "returns": returns,
    }


def _experiment_rows() -> list[dict[str, object]]:
    cells = {
        "organic": {"control": (400, 210, 72, 4), "treatment": (500, 295, 100, 8)},
        "paid_search": {"control": (200, 88, 24, 3), "treatment": (900, 430, 126, 18)},
        "career_fair": {"control": (400, 250, 100, 5), "treatment": (300, 202, 81, 6)},
        "referral": {"control": (800, 610, 280, 6), "treatment": (100, 80, 37, 2)},
    }
    rows: list[dict[str, object]] = []
    for segment, variants in cells.items():
        for variant, values in variants.items():
            assigned, opened, applied, unsubscribed = values
            rows.append({
                "segment": segment,
                "variant": variant,
                "assigned": assigned,
                "opened": opened,
                "applied": applied,
                "unsubscribed": unsubscribed,
            })
    return rows


def _qa_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    event_counter = 0
    base_date = date(2026, 6, 1)
    for week_number in (1, 2):
        for workflow_index in range(1, 201):
            workflow_id = f"W{week_number}-{workflow_index:04d}"
            source = ["web", "mobile", "partner"][workflow_index % 3]
            if week_number == 1:
                first_pass = workflow_index <= 180
                final_fail = workflow_index > 195
            else:
                first_pass = workflow_index <= 175
                final_fail = workflow_index > 195
            retry_success = not first_pass and not final_fail
            occurred = base_date + timedelta(days=(week_number - 1) * 7 + (workflow_index % 7))

            event_counter += 1
            start_event = {
                "event_id": f"EVT-{event_counter:06d}",
                "workflow_id": workflow_id,
                "week": f"2026-W{22 + week_number}",
                "occurred_at": f"{occurred.isoformat()}T08:{workflow_index % 60:02d}:00Z",
                "source_system": source,
                "stage": "processing",
                "attempt": 1,
                "status": "success" if first_pass else "failure",
                "reason": "" if first_pass else ("partner_timeout" if source == "partner" else "transient_timeout"),
                "customer_impact": "false",
            }
            rows.append(start_event)
            if week_number == 2 and source == "partner" and not first_pass:
                rows.append(dict(start_event))  # instrumentation duplicate with same event_id
            if retry_success or final_fail:
                event_counter += 1
                rows.append({
                    "event_id": f"EVT-{event_counter:06d}",
                    "workflow_id": workflow_id,
                    "week": f"2026-W{22 + week_number}",
                    "occurred_at": f"{occurred.isoformat()}T09:{workflow_index % 60:02d}:00Z",
                    "source_system": source,
                    "stage": "processing",
                    "attempt": 2,
                    "status": "failure" if final_fail else "success",
                    "reason": ("upstream_unavailable" if final_fail else ""),
                    "customer_impact": "true" if final_fail else "false",
                })
    return rows


def _metric_contracts() -> dict[str, object]:
    metrics = [
        {
            "metric_id": "lane_on_time_rate",
            "case_id": "supply_chain",
            "grain": "supplier-lane",
            "numerator": "on-time receipts",
            "denominator": "all due receipts",
            "unit": "ratio",
            "decision_use": "differentiate service and sourcing policy",
        },
        {
            "metric_id": "net_revenue",
            "case_id": "accounting",
            "grain": "commercial order after source aggregation",
            "numerator": "gross line revenue minus accepted return revenue",
            "denominator": "not applicable",
            "unit": "USD",
            "decision_use": "quarterly revenue and margin reporting",
        },
        {
            "metric_id": "application_conversion_rate",
            "case_id": "experiment",
            "grain": "randomized participant within pre-treatment segment",
            "numerator": "participants who submitted an application",
            "denominator": "participants assigned to the variant",
            "unit": "ratio",
            "decision_use": "campaign rollout decision",
        },
        {
            "metric_id": "final_workflow_failure_rate",
            "case_id": "quality",
            "grain": "unique workflow after final attempt",
            "numerator": "workflows whose final observed attempt failed",
            "denominator": "unique workflows started",
            "unit": "ratio",
            "decision_use": "customer-facing reliability assessment",
        },
        {
            "metric_id": "event_failure_rate_naive",
            "case_id": "quality",
            "grain": "raw emitted event",
            "numerator": "raw failure events including duplicates and retries",
            "denominator": "all raw events",
            "unit": "ratio",
            "decision_use": "anti-pattern demonstration only",
        },
    ]
    return {
        "schema_version": "1.0",
        "company": COMPANY_NAME,
        "synthetic": True,
        "metrics": metrics,
    }
