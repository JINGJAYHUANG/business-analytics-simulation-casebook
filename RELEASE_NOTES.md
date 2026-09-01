# Business Analytics Simulation Casebook v0.1.0

The first public release turns four original synthetic business problems into one reproducible analytical operating cycle:

1. segment supplier-lane relationships without treating clusters as causes;
2. reconcile order-to-cash data without many-to-many join inflation;
3. audit an A/B test whose pooled result reverses every within-segment result;
4. diagnose a QA spike caused by duplicate telemetry and retry-denominator drift;
5. carry the evidence, conflicts, and decisions into a quarterly executive report.

## Fixed public fixture

- 80 synthetic supplier-lane records;
- 64 orders and 128 order lines;
- 61 invoices, 69 payment rows, and 16 return rows;
- 8 experiment cells;
- 454 raw QA events across 400 workflows;
- 46 declared output artifacts;
- 207 automated tests;
- 6/6 deliberate evidence-bundle tampering attacks detected.

## Interpretation boundary

All entities and observations are fictional. The release validates the software, metric contracts, analytical traps, and evidence-integrity controls. It does not reproduce proprietary coursework and does not establish recommendations for a real company.
