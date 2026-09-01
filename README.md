# Business Analytics Simulation Casebook

An original, reproducible and public-safe casebook linking four synthetic business analytics problems for the fictional `Meridian Supply Lab`: supply-chain segmentation, accounting reconciliation, randomized experimentation, and QA metric governance.

> **Simulation disclosure:** all entities, amounts, events and decisions are deterministic software fixtures. This repository does not reproduce proprietary course prompts, answer keys, real company data, or employment work.

## Decision design

The casebook starts from one quarterly management decision and preserves four independent evidence streams. It deliberately has **no overall business score**: a positive experiment point estimate cannot cancel an accounting mismatch or an invalid QA denominator.

## Cases

1. Supply-chain service segmentation across 18 fictional customer profiles.
2. Invoice, payment, return and ledger reconciliation that keeps orphan records visible.
3. A randomized two-arm campaign with 400 fictional participants, an uncertainty interval and a support-demand guardrail.
4. QA metric diagnosis across 120 fictional runs, including denominator and timezone drift.

## Quick start

```bash
python -m pip install --no-deps .
basc build examples/synthetic_company/scenario.json --output-dir demo-run --fixed-time 2026-03-31T00:00:00Z
basc verify demo-run
```

The reference recommendation is **selective proceed with data-governance gates**: pilot service differentiation, repair finance mapping, extend the experiment, and freeze the disputed QA KPI until its semantic definition is corrected.

## Trust boundary

- original code and synthetic fixtures only;
- no course content, private records, credentials or personal profile;
- descriptive clusters are not causal claims;
- a point estimate is not a rollout decision;
- integrity hashes detect post-build changes but are not digital signatures.

## Maturity

`method-fixture-report-and-integrity-validated`

MIT licensed.
