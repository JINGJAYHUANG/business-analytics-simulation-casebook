# Business Analytics Simulation Casebook

[![CI](https://github.com/JINGJAYHUANG/business-analytics-simulation-casebook/actions/workflows/ci.yml/badge.svg)](https://github.com/JINGJAYHUANG/business-analytics-simulation-casebook/actions/workflows/ci.yml)

An original, synthetic, and fully reproducible business-analytics casebook covering supply-chain segmentation, order-to-cash data integration, A/B experiment diagnostics, QA metric troubleshooting, and executive reporting.

> This repository is an independent educational and portfolio project. It does not reproduce proprietary course data, instructions, answer keys, screenshots, or company records. Every company, person, transaction, experiment, and operating event is fictional.

## Why this exists

Business analytics is rarely one clean model. The difficult work is usually deciding:

- what decision the analysis should support;
- which unit of analysis matches that decision;
- whether joins, filters, and denominators preserve the intended population;
- whether an experiment compares like with like;
- whether a metric movement reflects the business or the instrumentation;
- and how to communicate a recommendation without hiding uncertainty.

The casebook turns those problems into four connected, executable cases for the fictional **Asterline Supply Co.**

## Four cases

| Case | Decision | Core methods | Deliberate analytical trap |
|---|---|---|---|
| Supply-chain segmentation | Which supplier-lane relationships need different policies? | deterministic k-means, silhouette diagnostics, cluster profiling | treating descriptive clusters as causal |
| Accounting integration | Which quarterly revenue and margin numbers are defensible? | grain contracts, deduplication, reconciliation, SQL | many-to-many join explosion |
| A/B experiment audit | Should a campaign be rolled out? | Wilson intervals, two-proportion tests, post-stratification | Simpson's paradox from segment imbalance |
| QA metric troubleshooting | Did customer quality deteriorate? | event deduplication, workflow-level metrics, root-cause concentration | denominator drift from retries and duplicate logging |

The final executive report integrates all four analyses while preserving conflicting signals and caveats.

## Design principles

1. **Decision first.** Every case names the user, action, population, and unit of analysis.
2. **Grain before joins.** Each source is aggregated to its intended grain before joining.
3. **Denominators are contracts.** Similar-looking rates can answer different questions.
4. **Negative evidence stays visible.** Orphans, duplicates, imbalance, and uncertainty are not silently dropped.
5. **Descriptive is not causal.** Segmentation and observational patterns do not become causal claims.
6. **No synthetic certainty.** Fictional data can validate software behavior, not real-world recommendations.
7. **Reproducibility is part of the deliverable.** Inputs, outputs, hashes, event order, and SQLite content are verifiable.

## Quick start

Requires Python 3.11 or newer. Runtime dependencies: **none**.

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .

basc demo \
  --root demo \
  --fixed-time 2026-09-01T00:00:00Z \
  --overwrite

basc verify --run-dir demo/output
```

Open:

```text
demo/output/executive/quarterly_report.html
```

## CLI

```bash
basc --version
basc inspect
basc inspect experiment
basc generate --data-dir synthetic-data
basc validate --data-dir synthetic-data --json
basc run --data-dir synthetic-data --output-dir run --fixed-time 2026-09-01T00:00:00Z
basc verify --run-dir run
basc compare --baseline run-a --candidate run-b
basc init --target starter-data             # preview only
basc init --target starter-data --apply     # create synthetic starter files
```

## Output bundle

A full run produces:

```text
output/
├── inputs/                       # frozen source snapshot + SHA-256 identities
├── supply_chain/                 # k diagnostics, assignments, profiles, policies
├── accounting/                   # reconciled fact table, channels, rejected rows
├── experiment/                   # aggregate and stratified effects, decision
├── quality/                      # weekly metrics, workflows, root causes
├── executive/                    # decision register, findings, quarterly report
├── casebook.sqlite               # raw and analytical tables
├── events.jsonl                  # hash-chained execution events
├── artifact_manifest.json        # file sizes and SHA-256 digests
└── run_manifest.json             # run identity and SQLite semantic digest
```

## Selected fixed-fixture findings

The committed synthetic fixture is deliberately non-trivial:

- the accounting anti-pattern inflates revenue because raw order lines are joined to multiple payment rows;
- the campaign treatment improves conversion inside every segment but looks worse in the pooled result;
- overall A/B allocation is balanced while segment composition is not;
- raw QA event failure rates rise because retries and duplicate instrumentation changed, while final workflow failure remains stable;
- supply-chain clusters support differentiated policy, but the report explicitly refuses causal interpretation.

These are software fixtures, not findings about a real firm.

## SQL

The repository includes reference SQL for:

- safe source-level aggregation before an order-grain join;
- the naive many-to-many join anti-pattern;
- workflow-level QA metrics after event deduplication.

See [`sql/`](sql/) and [`docs/sql-and-grain.md`](docs/sql-and-grain.md).

## Reproducibility and integrity

Each run:

- snapshots every declared input;
- computes stable SHA-256 identities;
- records a hash-chained event log;
- exports a SQLite database plus a semantic digest of tables and rows;
- rejects missing, modified, or undeclared artifacts;
- supports deterministic re-execution with an explicit timezone-aware timestamp.

A valid evidence bundle can still contain a failed analytical conclusion. Integrity means the evidence was not altered after generation; it does not mean the business recommendation is universally correct.

## Public boundary

This repository does **not** contain:

- proprietary simulation prompts, data, answer keys, or screenshots;
- real employer, customer, employee, supplier, or applicant records;
- private emails, contacts, credentials, or cloud configurations;
- claims that a virtual simulation was employment;
- causal claims unsupported by the analytical design.

See [`docs/provenance-and-boundary.md`](docs/provenance-and-boundary.md).

## Documentation

- [中文说明](docs/README.zh-CN.md)
- [Architecture](docs/architecture.md)
- [Data and metric contracts](docs/data-and-metric-contracts.md)
- [Analytical methodology](docs/methodology.md)
- [SQL and grain](docs/sql-and-grain.md)
- [Experiment interpretation](docs/experiment-interpretation.md)
- [Executive reporting](docs/executive-reporting.md)
- [Provenance and public boundary](docs/provenance-and-boundary.md)
- [Limitations](docs/limitations.md)
- [Skills matrix](docs/skills-matrix.md)
- [Release verification](docs/release-verification.md)

## Maturity

Current maturity: **fixture-method-and-integrity validated**.

Validated:

- deterministic synthetic data generation;
- four analytical workflows;
- metric and grain contracts;
- reporting and SQLite export;
- evidence-bundle verification;
- Python 3.11–3.13 CI;
- reproducible wheel builds.

Not claimed:

- production data connectors;
- real-company recommendations;
- causal validity beyond the experiment design;
- equivalence to any proprietary course or commercial analytics platform.

## License

MIT. Synthetic examples and original instructions are included under the same license.
