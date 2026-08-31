# Architecture

## Pipeline

```text
Synthetic source generator
        │
        ▼
Frozen input snapshot + source hashes
        │
        ├── Supply-chain segmentation
        ├── Accounting integration
        ├── Experiment audit
        └── QA metric troubleshooting
        │
        ▼
Cross-case decision register
        │
        ├── Markdown / HTML
        ├── CSV / JSON
        ├── SQLite
        └── Findings ledger
        │
        ▼
Hash-chained events + artifact manifest + run manifest
```

## Module boundaries

| Module | Responsibility |
|---|---|
| `synthetic.py` | deterministic fictional source data |
| `contracts.py` | required files, columns, keys, metric-contract validation |
| `clustering.py` | standardization, deterministic k-means, silhouette and policy profiles |
| `accounting.py` | deduplication, source aggregation, reconciliation and join-explosion demonstration |
| `experiment.py` | aggregate and stratified effects, intervals, SRM and composition diagnostics |
| `quality.py` | event deduplication, workflow outcomes, retry burden and root causes |
| `reporting.py` | decision-oriented Markdown and self-contained HTML |
| `sqlite_export.py` | relational export and semantic content digest |
| `integrity.py` | event-chain and artifact verification |
| `runner.py` | deterministic orchestration and executive integration |
| `cli.py` | public command-line interface |

## Why one integrated fictional company

The four cases use one company context so that analytics feels like an operating system rather than four disconnected notebooks. They remain logically separate:

- segmentation is descriptive;
- accounting is reconciliation and reporting;
- experimentation estimates a defined treatment effect;
- QA analysis diagnoses metric and instrumentation behavior.

No result from one case is allowed to silently become a premise in another. Cross-case recommendations are assembled only in the executive layer.
