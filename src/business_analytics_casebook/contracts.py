from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .canonical import read_csv, read_json


@dataclass(frozen=True)
class DataContract:
    file_name: str
    grain: str
    primary_key: tuple[str, ...]
    required_columns: tuple[str, ...]


CONTRACTS: tuple[DataContract, ...] = (
    DataContract(
        "supply_chain_lanes.csv",
        "one row per supplier-lane relationship",
        ("lane_id",),
        (
            "lane_id", "supplier_id", "region", "annual_units", "unit_cost_usd",
            "inbound_freight_usd", "lead_time_days", "on_time_rate", "fill_rate",
            "defect_rate", "demand_cv", "expedite_rate", "carbon_kg_per_unit",
        ),
    ),
    DataContract(
        "orders.csv",
        "one row per commercial order",
        ("order_id",),
        ("order_id", "customer_id", "order_date", "channel", "region", "status"),
    ),
    DataContract(
        "order_lines.csv",
        "one row per order line",
        ("line_id",),
        ("line_id", "order_id", "sku", "quantity", "unit_price", "unit_cost"),
    ),
    DataContract(
        "invoices.csv",
        "one row per invoice",
        ("invoice_id",),
        ("invoice_id", "order_id", "invoice_date", "shipping_fee", "tax_amount", "invoice_total"),
    ),
    DataContract(
        "payments.csv",
        "one row per payment event before deduplication",
        ("payment_id",),
        ("payment_id", "invoice_id", "payment_date", "amount", "payment_status"),
    ),
    DataContract(
        "returns.csv",
        "one row per return line",
        ("return_id",),
        ("return_id", "line_id", "return_date", "quantity", "reason"),
    ),
    DataContract(
        "experiment_cells.csv",
        "one row per experiment segment and variant",
        ("segment", "variant"),
        ("segment", "variant", "assigned", "opened", "applied", "unsubscribed"),
    ),
    DataContract(
        "qa_events.csv",
        "one row per emitted QA event before deduplication",
        ("event_id",),
        (
            "event_id", "workflow_id", "week", "occurred_at", "source_system",
            "stage", "attempt", "status", "reason", "customer_impact",
        ),
    ),
)


def validate_data_directory(data_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for contract in CONTRACTS:
        path = data_dir / contract.file_name
        if not path.exists():
            findings.append({
                "severity": "error",
                "rule_id": "MISSING_FILE",
                "file": contract.file_name,
                "message": f"Required data file is missing: {contract.file_name}",
            })
            continue
        rows = read_csv(path)
        if not rows:
            findings.append({
                "severity": "error",
                "rule_id": "EMPTY_FILE",
                "file": contract.file_name,
                "message": f"Required data file has no rows: {contract.file_name}",
            })
            continue
        columns = set(rows[0])
        missing_columns = [column for column in contract.required_columns if column not in columns]
        if missing_columns:
            findings.append({
                "severity": "error",
                "rule_id": "MISSING_COLUMN",
                "file": contract.file_name,
                "message": "Missing columns: " + ", ".join(missing_columns),
            })
        seen: set[tuple[str, ...]] = set()
        for row_number, row in enumerate(rows, start=2):
            key = tuple(row.get(column, "") for column in contract.primary_key)
            if not all(key):
                findings.append({
                    "severity": "error",
                    "rule_id": "NULL_PRIMARY_KEY",
                    "file": contract.file_name,
                    "message": f"Blank primary-key component at CSV row {row_number}",
                })
            if key in seen:
                severity = "warning" if contract.file_name in {"payments.csv", "qa_events.csv"} else "error"
                findings.append({
                    "severity": severity,
                    "rule_id": "DUPLICATE_PRIMARY_KEY",
                    "file": contract.file_name,
                    "message": f"Duplicate key {key!r} at CSV row {row_number}",
                })
            seen.add(key)
    catalog_path = data_dir / "metric_contracts.json"
    if not catalog_path.exists():
        findings.append({
            "severity": "error",
            "rule_id": "MISSING_METRIC_CONTRACTS",
            "file": "metric_contracts.json",
            "message": "Metric contracts are required to define grain, numerator, and denominator.",
        })
    else:
        payload = read_json(catalog_path)
        if payload.get("schema_version") != "1.0":
            findings.append({
                "severity": "error",
                "rule_id": "METRIC_SCHEMA_VERSION",
                "file": "metric_contracts.json",
                "message": "metric_contracts.json must use schema_version 1.0",
            })
        metrics = payload.get("metrics", [])
        ids = [metric.get("metric_id") for metric in metrics]
        if len(ids) != len(set(ids)):
            findings.append({
                "severity": "error",
                "rule_id": "DUPLICATE_METRIC_ID",
                "file": "metric_contracts.json",
                "message": "Metric identifiers must be unique.",
            })
    return findings


def raise_for_errors(findings: Iterable[dict[str, str]]) -> None:
    errors = [finding for finding in findings if finding.get("severity") == "error"]
    if errors:
        messages = "; ".join(f"{item['rule_id']}: {item['message']}" for item in errors)
        raise ValueError(messages)
