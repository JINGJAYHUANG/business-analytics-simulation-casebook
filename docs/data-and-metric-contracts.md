# Data and metric contracts

## Grain is a first-class field

Every source declares its intended unit of analysis and key. Examples:

| File | Grain | Key |
|---|---|---|
| `supply_chain_lanes.csv` | supplier-lane relationship | `lane_id` |
| `orders.csv` | commercial order | `order_id` |
| `order_lines.csv` | order line | `line_id` |
| `invoices.csv` | invoice | `invoice_id` |
| `payments.csv` | emitted payment event | `payment_id` before deduplication |
| `returns.csv` | return line | `return_id` |
| `experiment_cells.csv` | segment × variant cell | `segment, variant` |
| `qa_events.csv` | emitted QA event | `event_id` before deduplication |

## Metric contract fields

A metric contract includes:

```text
metric_id
case_id
grain
numerator
denominator
unit
decision_use
```

This prevents names such as `failure_rate` or `conversion` from carrying multiple incompatible meanings.

## Multiple valid denominators

The quality case deliberately keeps several metrics:

- raw event failure rate;
- deduplicated event failure rate;
- first-pass workflow failure rate;
- final workflow failure rate;
- customer-impact rate.

None is universally correct. Each answers a different operational question. The error is using one while narrating another.
