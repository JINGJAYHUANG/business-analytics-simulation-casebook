# Case brief 3 — A/B experiment audit

## Context

A fictional campaign was assigned 50/50 overall, but treatment and control have very different mixes of pre-treatment acquisition segments. Treatment conversion is higher inside every segment while the pooled result is lower.

## Decision

Should the treatment be rolled out?

## Deliverables

1. Calculate pooled conversion and uncertainty.
2. Check the overall assignment ratio.
3. Compare pre-treatment segment composition.
4. Calculate segment effects.
5. Estimate a post-stratified target-population effect.
6. Check an unsubscribe guardrail.
7. Explain whether the current run supports causal rollout.

## Acceptance criteria

- the pooled and stratified estimands are not conflated;
- Simpson's paradox is detected;
- composition imbalance remains a blocker;
- guardrails are visible;
- the recommendation calls for a confirmatory design rather than selective reporting.
