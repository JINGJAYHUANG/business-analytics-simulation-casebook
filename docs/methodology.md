# Analytical methodology

## 1. Start from the decision

Each case defines:

- decision owner;
- action under consideration;
- unit of analysis;
- population and exclusions;
- primary metric and guardrails;
- assumptions and interpretation limits.

## 2. Validate source structure

Before analysis:

- required files and columns are checked;
- keys are tested for missing and duplicate values;
- known duplicate-event sources are warnings rather than silently removed;
- metric contracts are required;
- raw inputs are copied into an immutable run snapshot.

## 3. Keep methods appropriate to the claim

### Segmentation

Deterministic k-means creates descriptive groups. Silhouette diagnostics assess geometric separation, not business impact. Policy recommendations remain hypotheses to test.

### Accounting

Each one-to-many source is aggregated to its intended grain before joining. Reconciliation compares billed totals with line revenue, shipping, and tax. Cash is not treated as revenue.

### Experiment

The primary effect is application conversion. Aggregate and segment-specific results are both computed. Post-stratification uses the pooled target-population segment mix. Composition imbalance and sign reversal are reported rather than averaged away.

### Quality

Raw event burden and final customer outcome are intentionally separate. Duplicate events are measured, retries are preserved, and the final event per workflow defines final outcome.

## 4. Preserve negative and unknown records

The pipeline retains:

- duplicate payment IDs;
- orphan payments;
- orphan returns;
- experiment composition imbalance;
- duplicated QA events;
- concentrated failure reasons.

Records may be quarantined from a metric, but they remain in the audit output.

## 5. Validate output integrity

The output bundle includes input and artifact hashes, a hash-chained event log, and a semantic digest of SQLite tables and rows.
