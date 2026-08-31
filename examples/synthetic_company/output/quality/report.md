# Case 4 — QA metric troubleshooting

## Decision

**FIX_METRIC_PIPELINE_AND_SOURCE_RELIABILITY**

Do not describe the raw event spike as a customer-facing quality collapse. Repair duplicate logging, preserve workflow-level denominators, and investigate the concentrated timeout source.

## Weekly metrics

| Week | Workflows | Raw events | Duplicates | Naive event failure | First-pass yield | Final success | Final failure | Retry rate | Customer impact |
|---|---|---|---|---|---|---|---|---|---|
| 2026-W23 | 200 | 220 | 0 | 0.113636 | 0.9 | 0.975 | 0.025 | 0.1 | 0.025 |
| 2026-W24 | 200 | 234 | 9 | 0.166667 | 0.875 | 0.975 | 0.025 | 0.125 | 0.025 |

## Root-cause concentrations

| Source | Reason | Failure events |
|---|---|---|
| partner | partner_timeout | 16 |
| mobile | transient_timeout | 15 |
| web | transient_timeout | 14 |
| mobile | upstream_unavailable | 4 |
| partner | upstream_unavailable | 4 |
| web | upstream_unavailable | 2 |

## Findings

| ID | Severity | Rule | Finding | Required response |
|---|---|---|---|---|
| QA-001 | critical | DUPLICATE_EVENT_ID | 9 duplicated event identifier(s) were emitted. | Make event_id idempotent at the producer and deduplicate before metric aggregation. |
| QA-002 | critical | DENOMINATOR_SHIFT | Naive event failure-rate change is +5.303%; workflow-level final failure-rate change is +0.000%. | Use unique workflow as the customer-outcome grain; report retry burden separately. |
| QA-003 | medium | ROOT_CAUSE_CONCENTRATION | The largest failure-event concentration is partner / partner_timeout (16 events). | Separate first-pass reliability, recovery, and customer-impact metrics by source system. |
