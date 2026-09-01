# Case 3 — A/B experiment audit

## Decision

**RE-RANDOMIZE_AND_CONFIRM**

Do not use the naive pooled result. Re-run with segment-blocked assignment and preserve the pre-specified target-population weights.

## Aggregate result

| Control conversion | Treatment conversion | Absolute effect | Relative lift | z | p-value |
|---|---|---|---|---|---|
| 0.264444 | 0.191111 | -0.0733333 | -0.277311 | -5.24561 | 1.6e-07 |

## Post-stratified result

| Standardized control | Standardized treatment | Stratified effect | Stratified p-value | Unsubscribe guardrail effect | Segment-mix distance | Overall SRM p-value | Simpson reversal |
|---|---|---|---|---|---|---|---|
| 0.217778 | 0.237778 | 0.02 | 0.256657 | 0.00761111 | 0.444444 | 1 | True |

## Segment effects

| Segment | Target weight | Control n | Treatment n | Control rate | Treatment rate | Effect | p-value |
|---|---|---|---|---|---|---|---|
| career_fair | 0.194444 | 400 | 300 | 0.25 | 0.27 | 0.02 | 0.549798 |
| organic | 0.25 | 400 | 500 | 0.18 | 0.2 | 0.02 | 0.448276 |
| paid_search | 0.305556 | 200 | 900 | 0.12 | 0.14 | 0.02 | 0.455962 |
| referral | 0.25 | 800 | 100 | 0.35 | 0.37 | 0.02 | 0.693021 |

## Findings

| ID | Severity | Rule | Finding | Required response |
|---|---|---|---|---|
| EX-001 | critical | SIMPSONS_PARADOX | The aggregate treatment effect has the opposite sign from every segment-level effect. | Use blocked randomization or a pre-specified post-stratified estimand and run a confirmatory experiment. |
| EX-002 | high | SEGMENT_IMBALANCE | Variant segment-distribution distance is 0.444. | Balance assignment within segment and monitor allocation at ingestion time. |
