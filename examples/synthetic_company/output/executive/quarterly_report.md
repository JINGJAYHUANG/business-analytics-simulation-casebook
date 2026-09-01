# Asterline Supply Co. — Synthetic quarterly analytics brief

> This report is generated from deterministic synthetic data. It is an educational and portfolio artifact, not a statement about a real company.

## Executive decisions

| ID | Area | Decision | Evidence | Caveat | Next action |
|---|---|---|---|---|---|
| DEC-001 | Supply chain | Adopt differentiated service policies by operating segment. | Deterministic 4-segment solution; silhouette 0.759942. | Clusters are descriptive and require operational pilots before causal claims. | Pilot policy changes with pre-defined service and total-cost measures. |
| DEC-002 | Finance and reporting | Publish only the reconciled order-grain quarterly fact table. | Naive raw joins inflate gross revenue by 12.0%. | Orphan and duplicate records remain data-governance issues even after quarantine. | Add uniqueness and referential-integrity checks upstream of reporting. |
| DEC-003 | Growth experiment | RE-RANDOMIZE_AND_CONFIRM | Naive effect -7.3%; post-stratified effect +2.0%. | Large pre-treatment mix imbalance creates an aggregate sign reversal. | Run a segment-blocked confirmatory experiment with a pre-specified estimand. |
| DEC-004 | Quality analytics | FIX_METRIC_PIPELINE_AND_SOURCE_RELIABILITY | Naive failure-rate change +5.3%; workflow-level change +0.0%. | Retry burden is operationally important even when final customer impact is stable. | Fix duplicate instrumentation and address the concentrated timeout source. |

## Cross-case controls

- Start from the decision and define the unit of analysis before choosing metrics.
- Keep source grain visible; aggregate each one-to-many source before joining.
- Compare treatment groups at comparable pre-treatment composition.
- Preserve multiple denominators when they answer different operational questions.
- Separate descriptive patterns from causal claims.
- Keep unknown, orphaned, duplicated, and unmatched records visible.

## Material findings

| ID | Severity | Rule | Finding | Required response |
|---|---|---|---|---|
| DATA-001 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('PAY-00020',) at CSV row 22 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-002 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000396',) at CSV row 398 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-003 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000402',) at CSV row 405 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-004 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000408',) at CSV row 412 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-005 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000414',) at CSV row 419 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-006 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000420',) at CSV row 426 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-007 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000426',) at CSV row 433 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-008 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000432',) at CSV row 440 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-009 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000438',) at CSV row 447 | Correct the source contract or quarantine the affected row before decision use. |
| DATA-010 | warning | DUPLICATE_PRIMARY_KEY | Duplicate key ('EVT-000444',) at CSV row 454 | Correct the source contract or quarantine the affected row before decision use. |
| SC-001 | info | CASE_FINDING | Segmentation is descriptive, not causal | Preserve the limitation in the decision record. |
| SC-002 | warning | CASE_FINDING | Scale and risk should be reviewed together | Preserve the limitation in the decision record. |
| AC-001 | high | DUPLICATE_PAYMENT_EVENT | Duplicate payment identifiers detected: PAY-00020 | Enforce payment_id uniqueness before aggregation and retain a rejected-row audit table. |
| AC-002 | high | ORPHAN_PAYMENT | 1 payment event(s) do not match a known invoice. | Route unmatched payments to suspense and investigate the source-system key. |
| AC-003 | high | ORPHAN_RETURN | 1 return event(s) do not match a known order line. | Reject or quarantine unmatched returns until line-level identity is restored. |
| AC-004 | critical | JOIN_EXPLOSION | A naive line-to-payment join overstates gross revenue by 11493.50 USD (11.97%). | Aggregate lines, payments, and returns to their intended grain before joining at order_id. |
| EX-001 | critical | SIMPSONS_PARADOX | The aggregate treatment effect has the opposite sign from every segment-level effect. | Use blocked randomization or a pre-specified post-stratified estimand and run a confirmatory experiment. |
| EX-002 | high | SEGMENT_IMBALANCE | Variant segment-distribution distance is 0.444. | Balance assignment within segment and monitor allocation at ingestion time. |
| QA-001 | critical | DUPLICATE_EVENT_ID | 9 duplicated event identifier(s) were emitted. | Make event_id idempotent at the producer and deduplicate before metric aggregation. |
| QA-002 | critical | DENOMINATOR_SHIFT | Naive event failure-rate change is +5.303%; workflow-level final failure-rate change is +0.000%. | Use unique workflow as the customer-outcome grain; report retry burden separately. |
| QA-003 | medium | ROOT_CAUSE_CONCENTRATION | The largest failure-event concentration is partner / partner_timeout (16 events). | Separate first-pass reliability, recovery, and customer-impact metrics by source system. |

## Interpretation boundary

The casebook demonstrates reproducible analytical methods on fictional data. It does not reproduce proprietary course material, establish employment, or prove that the same recommendations apply to a real organization.
