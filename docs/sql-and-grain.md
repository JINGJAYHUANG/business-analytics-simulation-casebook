# SQL and grain

## The core accounting trap

Joining these tables at raw grain creates a many-to-many result:

```text
one order
→ many order lines
→ one invoice
→ many payments
→ many return lines
```

A naive query can repeat every line once for each payment. Revenue rises even though no additional sale occurred.

## Safe pattern

```text
aggregate order lines by order
aggregate returns by order
aggregate deduplicated payments by invoice
join the aggregates
```

See:

- [`sql/01_reconciled_order_fact.sql`](../sql/01_reconciled_order_fact.sql)
- [`sql/02_naive_join_anti_pattern.sql`](../sql/02_naive_join_anti_pattern.sql)

## Join checks

Before and after every important join, inspect:

- row count;
- distinct primary entity count;
- uniqueness of the right-hand key;
- unmatched left and right records;
- sum of the highest-impact measure;
- expected one-to-one, one-to-many, or many-to-one relationship.

A successful SQL query is not evidence that the grain is correct.
