from __future__ import annotations

import html
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable


def _display(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return ""
    return str(value)


def markdown_table(rows: Iterable[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    materialized = list(rows)
    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    body = []
    for row in materialized:
        body.append("| " + " | ".join(_display(row.get(key, "")).replace("|", "\\|") for key, _ in columns) + " |")
    return "\n".join([header, separator, *body])


def _html_table(rows: Iterable[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    materialized = list(rows)
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = []
    for row in materialized:
        cells = "".join(f"<td>{html.escape(_display(row.get(key, '')))}</td>" for key, _ in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def _finding_markdown(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "No material findings."
    return markdown_table(
        findings,
        [
            ("finding_id", "ID"),
            ("severity", "Severity"),
            ("rule_id", "Rule"),
            ("message", "Finding"),
            ("remediation", "Required response"),
        ],
    )


def _finding_html(findings: list[dict[str, Any]]) -> str:
    if not findings:
        return "<p>No material findings.</p>"
    return _html_table(
        findings,
        [
            ("finding_id", "ID"),
            ("severity", "Severity"),
            ("rule_id", "Rule"),
            ("message", "Finding"),
            ("remediation", "Required response"),
        ],
    )


def render_supply_chain(result: dict[str, Any]) -> tuple[str, str]:
    md = f"""# Case 1 — Supply-chain segmentation

## Decision

Choose differentiated operating policies for supplier-lane relationships without treating descriptive clusters as causal proof.

## Method

- Unit of analysis: one supplier-lane relationship.
- Features: {', '.join(result['feature_names'])}.
- Candidate cluster counts: 2 through 6.
- Selection rule: highest deterministic silhouette among solutions with at least eight lanes per cluster.
- Selected k: **{result['selected_k']}**.
- Selected silhouette: **{result['selected_silhouette']}**.

## K selection

{markdown_table(result['k_selection'], [('k','k'),('silhouette_score','Silhouette'),('minimum_cluster_size','Min size'),('maximum_cluster_size','Max size'),('eligible','Eligible')])}

## Segment profiles

{markdown_table(result['profiles'], [('segment','Segment'),('lane_count','Lanes'),('annual_units_share','Annual-unit share'),('landed_cost_per_unit','Landed cost/unit'),('lead_time_days','Lead days'),('on_time_rate','On-time'),('fill_rate','Fill'),('defect_rate','Defect'),('demand_cv','Demand CV'),('expedite_rate','Expedite')])}

## Policy actions

{markdown_table(result['policies'], [('segment','Segment'),('policy','Policy'),('action','Action'),('risk','Risk')])}

## Findings and boundaries

{_finding_markdown(result['findings'])}
"""
    body = f"""
<h1>Case 1 — Supply-chain segmentation</h1>
<p class="lead">Differentiate operating policy without mistaking clusters for causal effects.</p>
<div class="cards"><div><strong>Selected k</strong><span>{result['selected_k']}</span></div><div><strong>Silhouette</strong><span>{result['selected_silhouette']}</span></div><div><strong>Lanes</strong><span>{len(result['assignments'])}</span></div></div>
<h2>K selection</h2>{_html_table(result['k_selection'], [('k','k'),('silhouette_score','Silhouette'),('minimum_cluster_size','Min size'),('maximum_cluster_size','Max size'),('eligible','Eligible')])}
<h2>Segment profiles</h2>{_html_table(result['profiles'], [('segment','Segment'),('lane_count','Lanes'),('annual_units_share','Unit share'),('landed_cost_per_unit','Landed cost'),('lead_time_days','Lead days'),('on_time_rate','On-time'),('fill_rate','Fill'),('defect_rate','Defect'),('demand_cv','Demand CV'),('expedite_rate','Expedite')])}
<h2>Policy actions</h2>{_html_table(result['policies'], [('segment','Segment'),('policy','Policy'),('action','Action'),('risk','Risk')])}
<h2>Findings</h2>{_finding_html(result['findings'])}
"""
    return md, html_document("Supply-chain segmentation", body)


def render_accounting(result: dict[str, Any]) -> tuple[str, str]:
    summary = result["summary"]
    md = f"""# Case 2 — Accounting data integration

## Decision

Publish quarterly revenue and margin only from a reconciled order-grain fact table. Never sum commercial measures after joining multiple one-to-many sources at raw grain.

## Reconciled summary

{markdown_table([summary], [('completed_orders','Completed orders'),('gross_revenue','Gross revenue'),('return_revenue','Returns'),('net_revenue','Net revenue'),('net_cogs','Net COGS'),('gross_profit','Gross profit'),('gross_margin','Gross margin'),('cash_collected','Cash collected'),('accounts_receivable','Accounts receivable'),('dso_proxy_days','DSO proxy')])}

## Join-explosion demonstration

{markdown_table([summary], [('gross_revenue','Correct gross revenue'),('naive_join_gross_revenue','Naive joined revenue'),('join_inflation_amount','Inflation amount'),('join_inflation_rate','Inflation rate')])}

## Channel summary

{markdown_table(result['channel_summary'], [('channel','Channel'),('orders','Orders'),('net_revenue','Net revenue'),('gross_profit','Gross profit'),('gross_margin','Gross margin')])}

## Findings

{_finding_markdown(result['findings'])}
"""
    body = f"""
<h1>Case 2 — Accounting data integration</h1>
<p class="lead">Reconcile revenue, returns, cash, and COGS at the order grain before reporting.</p>
<div class="cards"><div><strong>Net revenue</strong><span>${html.escape(_display(summary['net_revenue']))}</span></div><div><strong>Gross margin</strong><span>{float(summary['gross_margin']):.1%}</span></div><div><strong>Join inflation</strong><span>{float(summary['join_inflation_rate']):.1%}</span></div></div>
<h2>Reconciled summary</h2>{_html_table([summary], [('completed_orders','Orders'),('gross_revenue','Gross revenue'),('return_revenue','Returns'),('net_revenue','Net revenue'),('net_cogs','Net COGS'),('gross_profit','Gross profit'),('cash_collected','Cash collected'),('accounts_receivable','A/R'),('dso_proxy_days','DSO proxy')])}
<h2>Join-explosion demonstration</h2>{_html_table([summary], [('gross_revenue','Correct gross revenue'),('naive_join_gross_revenue','Naive joined revenue'),('join_inflation_amount','Inflation'),('join_inflation_rate','Inflation rate')])}
<h2>Channel summary</h2>{_html_table(result['channel_summary'], [('channel','Channel'),('orders','Orders'),('net_revenue','Net revenue'),('gross_profit','Gross profit'),('gross_margin','Margin')])}
<h2>Findings</h2>{_finding_html(result['findings'])}
"""
    return md, html_document("Accounting data integration", body)


def render_experiment(result: dict[str, Any]) -> tuple[str, str]:
    decision = result["decision"]
    aggregate = result["aggregate"]
    md = f"""# Case 3 — A/B experiment audit

## Decision

**{decision['status']}**

{decision['recommendation']}

## Aggregate result

{markdown_table([aggregate], [('control_rate','Control conversion'),('treatment_rate','Treatment conversion'),('absolute_effect','Absolute effect'),('relative_lift','Relative lift'),('z_score','z'),('p_value','p-value')])}

## Post-stratified result

{markdown_table([decision], [('standardized_control_rate','Standardized control'),('standardized_treatment_rate','Standardized treatment'),('stratified_effect','Stratified effect'),('stratified_p_value','Stratified p-value'),('standardized_unsubscribe_effect','Unsubscribe guardrail effect'),('segment_mix_total_variation_distance','Segment-mix distance'),('srm_p_value','Overall SRM p-value'),('simpsons_paradox','Simpson reversal')])}

## Segment effects

{markdown_table(result['segments'], [('segment','Segment'),('weight_in_target_population','Target weight'),('control_assigned','Control n'),('treatment_assigned','Treatment n'),('control_rate','Control rate'),('treatment_rate','Treatment rate'),('absolute_effect','Effect'),('p_value','p-value')])}

## Findings

{_finding_markdown(result['findings'])}
"""
    body = f"""
<h1>Case 3 — A/B experiment audit</h1>
<p class="lead">Separate treatment effect from traffic-mix composition before making a rollout decision.</p>
<div class="cards"><div><strong>Naive effect</strong><span>{float(aggregate['absolute_effect']):+.1%}</span></div><div><strong>Stratified effect</strong><span>{float(decision['stratified_effect']):+.1%}</span></div><div><strong>Decision</strong><span class="small">{html.escape(decision['status'])}</span></div></div>
<h2>Aggregate result</h2>{_html_table([aggregate], [('control_rate','Control'),('treatment_rate','Treatment'),('absolute_effect','Effect'),('relative_lift','Lift'),('p_value','p-value')])}
<h2>Post-stratified result</h2>{_html_table([decision], [('standardized_control_rate','Std control'),('standardized_treatment_rate','Std treatment'),('stratified_effect','Effect'),('stratified_p_value','p-value'),('standardized_unsubscribe_effect','Unsubscribe effect'),('segment_mix_total_variation_distance','Mix distance'),('simpsons_paradox','Simpson reversal')])}
<h2>Segment effects</h2>{_html_table(result['segments'], [('segment','Segment'),('weight_in_target_population','Weight'),('control_assigned','Control n'),('treatment_assigned','Treatment n'),('control_rate','Control'),('treatment_rate','Treatment'),('absolute_effect','Effect'),('p_value','p-value')])}
<h2>Findings</h2>{_finding_html(result['findings'])}
"""
    return md, html_document("A/B experiment audit", body)


def render_quality(result: dict[str, Any]) -> tuple[str, str]:
    decision = result["decision"]
    md = f"""# Case 4 — QA metric troubleshooting

## Decision

**{decision['status']}**

{decision['recommendation']}

## Weekly metrics

{markdown_table(result['weekly_metrics'], [('week','Week'),('workflow_count','Workflows'),('raw_event_count','Raw events'),('duplicate_event_count','Duplicates'),('naive_raw_event_failure_rate','Naive event failure'),('first_pass_yield','First-pass yield'),('final_success_rate','Final success'),('final_failure_rate','Final failure'),('retry_rate','Retry rate'),('customer_impact_rate','Customer impact')])}

## Root-cause concentrations

{markdown_table(result['root_causes'], [('source_system','Source'),('reason','Reason'),('failure_event_count','Failure events')])}

## Findings

{_finding_markdown(result['findings'])}
"""
    first, second = result["weekly_metrics"]
    body = f"""
<h1>Case 4 — QA metric troubleshooting</h1>
<p class="lead">Keep raw event burden, first-pass reliability, recovery, and customer outcome on separate denominators.</p>
<div class="cards"><div><strong>Naive WoW change</strong><span>{float(decision['naive_week_over_week_change']):+.1%}</span></div><div><strong>Corrected WoW change</strong><span>{float(decision['corrected_week_over_week_change']):+.1%}</span></div><div><strong>Duplicate rate</strong><span>{float(decision['duplicate_event_rate']):.1%}</span></div></div>
<h2>Weekly metrics</h2>{_html_table(result['weekly_metrics'], [('week','Week'),('workflow_count','Workflows'),('raw_event_count','Raw events'),('duplicate_event_count','Duplicates'),('naive_raw_event_failure_rate','Naive failure'),('first_pass_yield','FPY'),('final_success_rate','Final success'),('final_failure_rate','Final failure'),('retry_rate','Retry')])}
<h2>Root causes</h2>{_html_table(result['root_causes'], [('source_system','Source'),('reason','Reason'),('failure_event_count','Failure events')])}
<h2>Findings</h2>{_finding_html(result['findings'])}
"""
    return md, html_document("QA metric troubleshooting", body)


def render_executive(results: dict[str, dict[str, Any]], findings: list[dict[str, Any]]) -> tuple[str, str, list[dict[str, Any]]]:
    supply = results["supply_chain"]
    accounting = results["accounting"]["summary"]
    experiment = results["experiment"]["decision"]
    quality = results["quality"]["decision"]
    decisions = [
        {
            "decision_id": "DEC-001",
            "area": "Supply chain",
            "decision": "Adopt differentiated service policies by operating segment.",
            "evidence": f"Deterministic {supply['selected_k']}-segment solution; silhouette {supply['selected_silhouette']}.",
            "caveat": "Clusters are descriptive and require operational pilots before causal claims.",
            "next_action": "Pilot policy changes with pre-defined service and total-cost measures.",
        },
        {
            "decision_id": "DEC-002",
            "area": "Finance and reporting",
            "decision": "Publish only the reconciled order-grain quarterly fact table.",
            "evidence": f"Naive raw joins inflate gross revenue by {float(accounting['join_inflation_rate']):.1%}.",
            "caveat": "Orphan and duplicate records remain data-governance issues even after quarantine.",
            "next_action": "Add uniqueness and referential-integrity checks upstream of reporting.",
        },
        {
            "decision_id": "DEC-003",
            "area": "Growth experiment",
            "decision": experiment["status"],
            "evidence": f"Naive effect {float(experiment['aggregate_effect']):+.1%}; post-stratified effect {float(experiment['stratified_effect']):+.1%}.",
            "caveat": "Large pre-treatment mix imbalance creates an aggregate sign reversal.",
            "next_action": "Run a segment-blocked confirmatory experiment with a pre-specified estimand.",
        },
        {
            "decision_id": "DEC-004",
            "area": "Quality analytics",
            "decision": quality["status"],
            "evidence": f"Naive failure-rate change {float(quality['naive_week_over_week_change']):+.1%}; workflow-level change {float(quality['corrected_week_over_week_change']):+.1%}.",
            "caveat": "Retry burden is operationally important even when final customer impact is stable.",
            "next_action": "Fix duplicate instrumentation and address the concentrated timeout source.",
        },
    ]
    md = f"""# Asterline Supply Co. — Synthetic quarterly analytics brief

> This report is generated from deterministic synthetic data. It is an educational and portfolio artifact, not a statement about a real company.

## Executive decisions

{markdown_table(decisions, [('decision_id','ID'),('area','Area'),('decision','Decision'),('evidence','Evidence'),('caveat','Caveat'),('next_action','Next action')])}

## Cross-case controls

- Start from the decision and define the unit of analysis before choosing metrics.
- Keep source grain visible; aggregate each one-to-many source before joining.
- Compare treatment groups at comparable pre-treatment composition.
- Preserve multiple denominators when they answer different operational questions.
- Separate descriptive patterns from causal claims.
- Keep unknown, orphaned, duplicated, and unmatched records visible.

## Material findings

{_finding_markdown(findings)}

## Interpretation boundary

The casebook demonstrates reproducible analytical methods on fictional data. It does not reproduce proprietary course material, establish employment, or prove that the same recommendations apply to a real organization.
"""
    body = f"""
<h1>Asterline Supply Co.</h1><p class="lead">Synthetic quarterly analytics brief</p>
<div class="cards"><div><strong>Cases</strong><span>4</span></div><div><strong>Material findings</strong><span>{len(findings)}</span></div><div><strong>Data</strong><span class="small">100% synthetic</span></div></div>
<h2>Executive decisions</h2>{_html_table(decisions, [('decision_id','ID'),('area','Area'),('decision','Decision'),('evidence','Evidence'),('caveat','Caveat'),('next_action','Next action')])}
<h2>Material findings</h2>{_finding_html(findings)}
<h2>Interpretation boundary</h2><p>This casebook demonstrates reproducible analytical methods on fictional data. It does not reproduce proprietary course material, establish employment, or prove that the same recommendations apply to a real organization.</p>
"""
    return md, html_document("Synthetic quarterly analytics brief", body), decisions


def html_document(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--paper:#f7f5ef;--ink:#182026;--muted:#65717a;--line:#cfd6d9;--accent:#244c66;--card:#ffffff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:42px 26px 70px}}h1{{font-size:clamp(30px,5vw,58px);line-height:1.02;margin:0 0 12px;letter-spacing:-.035em}}h2{{margin:42px 0 14px;font-size:24px}}.lead{{font-size:19px;color:var(--muted);max-width:820px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:28px 0}}.cards div{{background:var(--card);border:1px solid var(--line);padding:18px;border-radius:12px}}.cards strong{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em}}.cards span{{display:block;font-size:27px;font-weight:750;margin-top:4px}}.cards span.small{{font-size:15px;line-height:1.3}}
table{{width:100%;border-collapse:collapse;background:var(--card);font-size:13px}}th,td{{padding:10px 9px;border:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#e8edf0;color:#263844;position:sticky;top:0}}tr:nth-child(even) td{{background:#fbfcfc}}code{{background:#e8edf0;padding:2px 5px;border-radius:4px}}@media(max-width:720px){{main{{padding:26px 14px}}table{{display:block;overflow-x:auto}}th,td{{min-width:120px}}}}
</style>
</head>
<body><main>{body}</main></body>
</html>
"""
