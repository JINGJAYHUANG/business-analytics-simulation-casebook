# Case 2 — Accounting data integration

## Decision

Publish quarterly revenue and margin only from a reconciled order-grain fact table. Never sum commercial measures after joining multiple one-to-many sources at raw grain.

## Reconciled summary

| Completed orders | Gross revenue | Returns | Net revenue | Net COGS | Gross profit | Gross margin | Cash collected | Accounts receivable | DSO proxy |
|---|---|---|---|---|---|---|---|---|---|
| 61 | 96006.50 | 1483.50 | 94523.00 | 56502.34 | 38020.66 | 0.402237 | 98065.63 | 3661.71 | 3.2756 |

## Join-explosion demonstration

| Correct gross revenue | Naive joined revenue | Inflation amount | Inflation rate |
|---|---|---|---|
| 96006.50 | 107500.00 | 11493.50 | 0.119716 |

## Channel summary

| Channel | Orders | Net revenue | Gross profit | Gross margin |
|---|---|---|---|---|
| direct | 20 | 15192.00 | 6146.64 | 0.404597 |
| marketplace | 20 | 48224.00 | 19523.08 | 0.404842 |
| partner | 21 | 31107.00 | 12350.94 | 0.397047 |

## Findings

| ID | Severity | Rule | Finding | Required response |
|---|---|---|---|---|
| AC-001 | high | DUPLICATE_PAYMENT_EVENT | Duplicate payment identifiers detected: PAY-00020 | Enforce payment_id uniqueness before aggregation and retain a rejected-row audit table. |
| AC-002 | high | ORPHAN_PAYMENT | 1 payment event(s) do not match a known invoice. | Route unmatched payments to suspense and investigate the source-system key. |
| AC-003 | high | ORPHAN_RETURN | 1 return event(s) do not match a known order line. | Reject or quarantine unmatched returns until line-level identity is restored. |
| AC-004 | critical | JOIN_EXPLOSION | A naive line-to-payment join overstates gross revenue by 11493.50 USD (11.97%). | Aggregate lines, payments, and returns to their intended grain before joining at order_id. |
