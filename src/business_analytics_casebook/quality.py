from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from .canonical import read_csv, stable_float


def analyze_quality(path: Path) -> dict[str, object]:
    raw_rows = read_csv(path)
    duplicate_ids = [event_id for event_id, count in Counter(row["event_id"] for row in raw_rows).items() if count > 1]
    deduped: dict[str, dict[str, str]] = {}
    for row in raw_rows:
        deduped.setdefault(row["event_id"], row)
    rows = list(deduped.values())

    raw_by_week: dict[str, list[dict[str, str]]] = defaultdict(list)
    deduped_by_week: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in raw_rows:
        raw_by_week[row["week"]].append(row)
    for row in rows:
        deduped_by_week[row["week"]].append(row)

    weekly_metrics: list[dict[str, object]] = []
    workflow_details: list[dict[str, object]] = []
    source_reason_counts: Counter[tuple[str, str]] = Counter()
    for week in sorted(deduped_by_week):
        raw_week = raw_by_week[week]
        week_rows = deduped_by_week[week]
        workflows: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in week_rows:
            workflows[row["workflow_id"]].append(row)
            if row["status"] == "failure":
                source_reason_counts[(row["source_system"], row["reason"])] += 1
        first_pass = 0
        final_success = 0
        retried = 0
        customer_impact = 0
        for workflow_id, events in sorted(workflows.items()):
            ordered = sorted(events, key=lambda row: (int(row["attempt"]), row["occurred_at"], row["event_id"]))
            first = ordered[0]
            final = ordered[-1]
            if first["status"] == "success":
                first_pass += 1
            if len(ordered) > 1:
                retried += 1
            if final["status"] == "success":
                final_success += 1
            if final["customer_impact"] == "true":
                customer_impact += 1
            workflow_details.append({
                "workflow_id": workflow_id,
                "week": week,
                "source_system": final["source_system"],
                "attempts": len(ordered),
                "first_attempt_status": first["status"],
                "final_status": final["status"],
                "final_reason": final["reason"],
                "customer_impact": final["customer_impact"],
            })
        workflow_count = len(workflows)
        raw_failure_events = sum(1 for row in raw_week if row["status"] == "failure")
        dedup_failure_events = sum(1 for row in week_rows if row["status"] == "failure")
        weekly_metrics.append({
            "week": week,
            "workflow_count": workflow_count,
            "raw_event_count": len(raw_week),
            "deduped_event_count": len(week_rows),
            "duplicate_event_count": len(raw_week) - len(week_rows),
            "naive_raw_event_failure_rate": stable_float(raw_failure_events / len(raw_week), 8),
            "deduped_event_failure_rate": stable_float(dedup_failure_events / len(week_rows), 8),
            "first_pass_yield": stable_float(first_pass / workflow_count, 8),
            "final_success_rate": stable_float(final_success / workflow_count, 8),
            "final_failure_rate": stable_float((workflow_count - final_success) / workflow_count, 8),
            "retry_rate": stable_float(retried / workflow_count, 8),
            "customer_impact_rate": stable_float(customer_impact / workflow_count, 8),
        })

    first_week, second_week = weekly_metrics
    naive_delta = float(second_week["naive_raw_event_failure_rate"]) - float(first_week["naive_raw_event_failure_rate"])
    corrected_delta = float(second_week["final_failure_rate"]) - float(first_week["final_failure_rate"])
    duplicate_rate = len(raw_rows) - len(rows)
    duplicate_rate = duplicate_rate / len(raw_rows) if raw_rows else 0.0

    root_causes = [
        {
            "source_system": source,
            "reason": reason or "unspecified",
            "failure_event_count": count,
        }
        for (source, reason), count in source_reason_counts.most_common()
    ]
    findings = [
        {
            "finding_id": "QA-001",
            "severity": "critical" if duplicate_ids else "info",
            "rule_id": "DUPLICATE_EVENT_ID",
            "message": f"{len(duplicate_ids)} duplicated event identifier(s) were emitted.",
            "impact": "Event-level failure rates and incident counts are inflated unless event_id is deduplicated.",
            "remediation": "Make event_id idempotent at the producer and deduplicate before metric aggregation.",
        },
        {
            "finding_id": "QA-002",
            "severity": "critical" if abs(naive_delta - corrected_delta) > 0.02 else "info",
            "rule_id": "DENOMINATOR_SHIFT",
            "message": f"Naive event failure-rate change is {naive_delta:+.3%}; workflow-level final failure-rate change is {corrected_delta:+.3%}.",
            "impact": "Retries and duplicate instrumentation make the event denominator incomparable across periods.",
            "remediation": "Use unique workflow as the customer-outcome grain; report retry burden separately.",
        },
    ]
    if root_causes:
        top = root_causes[0]
        findings.append({
            "finding_id": "QA-003",
            "severity": "medium",
            "rule_id": "ROOT_CAUSE_CONCENTRATION",
            "message": f"The largest failure-event concentration is {top['source_system']} / {top['reason']} ({top['failure_event_count']} events).",
            "impact": "A broad business-quality narrative would hide a concentrated source-system reliability issue.",
            "remediation": "Separate first-pass reliability, recovery, and customer-impact metrics by source system.",
        })

    decision = {
        "status": "FIX_METRIC_PIPELINE_AND_SOURCE_RELIABILITY",
        "naive_week_over_week_change": stable_float(naive_delta, 8),
        "corrected_week_over_week_change": stable_float(corrected_delta, 8),
        "duplicate_event_rate": stable_float(duplicate_rate, 8),
        "recommendation": (
            "Do not describe the raw event spike as a customer-facing quality collapse. Repair duplicate logging, preserve workflow-level denominators, and investigate the concentrated timeout source."
        ),
    }
    return {
        "weekly_metrics": weekly_metrics,
        "workflow_details": workflow_details,
        "root_causes": root_causes,
        "decision": decision,
        "findings": findings,
    }
