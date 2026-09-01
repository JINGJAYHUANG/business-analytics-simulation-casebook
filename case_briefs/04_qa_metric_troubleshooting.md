# Case brief 4 — QA metric troubleshooting

## Context

A raw event-failure dashboard spikes in week two. At the same time, the system introduced more retry logging and one source began emitting duplicate failure events.

## Decision

Did customer-facing reliability deteriorate, or did the measurement system change?

## Deliverables

1. Detect duplicate event identifiers.
2. Separate raw event, deduplicated event, first-pass workflow, final workflow, and customer-impact metrics.
3. Compare week-over-week movement at each grain.
4. Identify the largest source/reason concentration.
5. Recommend both a metric repair and an operational response.

## Acceptance criteria

- retries remain visible instead of being discarded;
- final customer outcome uses unique workflows;
- duplicate instrumentation does not inflate the outcome metric;
- the analysis avoids calling the event spike a customer-quality collapse;
- root cause is localized before broad recommendations are made.
