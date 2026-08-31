# Case brief 2 — Order-to-cash integration

## Context

Orders, order lines, invoices, payments, and returns arrive from separate fictional systems. A quarterly report must reconcile sales, gross profit, cash collection, and accounts receivable.

## Decision

Which numbers can be published, and which source issues must remain visible?

## Deliverables

1. Declare the grain and key of every table.
2. Detect duplicate payments and orphan records.
3. Aggregate each one-to-many source before joining.
4. Reconcile invoice totals to line revenue, shipping, and tax.
5. Compare the safe result with a naive raw join.
6. Produce a rejected-row ledger and remediation plan.

## Acceptance criteria

- revenue is not multiplied by payment count;
- cash is not treated as revenue;
- orphan records are quarantined, not silently discarded;
- channel totals reconcile to the order fact;
- the report documents all remaining limitations.
