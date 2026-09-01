from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

from .canonical import read_csv, stable_float


def normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    rate = successes / total
    denominator = 1.0 + z * z / total
    center = (rate + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt((rate * (1.0 - rate) + z * z / (4.0 * total)) / total) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def two_proportion_test(success_a: int, total_a: int, success_b: int, total_b: int) -> dict[str, float]:
    if total_a <= 0 or total_b <= 0:
        raise ValueError("both groups require a positive sample size")
    rate_a = success_a / total_a
    rate_b = success_b / total_b
    pooled = (success_a + success_b) / (total_a + total_b)
    standard_error = math.sqrt(pooled * (1.0 - pooled) * (1.0 / total_a + 1.0 / total_b))
    z_score = (rate_b - rate_a) / standard_error if standard_error else 0.0
    p_value = 2.0 * (1.0 - normal_cdf(abs(z_score)))
    return {
        "control_rate": stable_float(rate_a, 8),
        "treatment_rate": stable_float(rate_b, 8),
        "absolute_effect": stable_float(rate_b - rate_a, 8),
        "relative_lift": stable_float((rate_b / rate_a - 1.0) if rate_a else 0.0, 8),
        "z_score": stable_float(z_score, 8),
        "p_value": stable_float(p_value, 8),
    }


def _chi_square_one_df_p_value(chi_square: float) -> float:
    return 2.0 * (1.0 - normal_cdf(math.sqrt(max(0.0, chi_square))))


def analyze_experiment(path: Path) -> dict[str, object]:
    rows = read_csv(path)
    by_variant: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_segment: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for row in rows:
        payload = {
            "assigned": int(row["assigned"]),
            "opened": int(row["opened"]),
            "applied": int(row["applied"]),
            "unsubscribed": int(row["unsubscribed"]),
        }
        by_segment[row["segment"]][row["variant"]] = payload
        for key, value in payload.items():
            by_variant[row["variant"]][key] += value

    if set(by_variant) != {"control", "treatment"}:
        raise ValueError("experiment requires control and treatment variants")

    aggregate = two_proportion_test(
        by_variant["control"]["applied"],
        by_variant["control"]["assigned"],
        by_variant["treatment"]["applied"],
        by_variant["treatment"]["assigned"],
    )
    control_total = by_variant["control"]["assigned"]
    treatment_total = by_variant["treatment"]["assigned"]
    total_assigned = control_total + treatment_total
    expected_each = total_assigned / 2.0
    chi_square = ((control_total - expected_each) ** 2 + (treatment_total - expected_each) ** 2) / expected_each
    srm_p_value = _chi_square_one_df_p_value(chi_square)

    segment_rows: list[dict[str, object]] = []
    total_by_segment = {
        segment: values["control"]["assigned"] + values["treatment"]["assigned"]
        for segment, values in by_segment.items()
    }
    pooled_total = sum(total_by_segment.values())
    standardized_control = 0.0
    standardized_treatment = 0.0
    standardized_unsub_control = 0.0
    standardized_unsub_treatment = 0.0
    variance_control = 0.0
    variance_treatment = 0.0
    segment_effect_signs: list[int] = []
    control_distribution: dict[str, float] = {}
    treatment_distribution: dict[str, float] = {}

    for segment in sorted(by_segment):
        control = by_segment[segment]["control"]
        treatment = by_segment[segment]["treatment"]
        result = two_proportion_test(
            control["applied"], control["assigned"], treatment["applied"], treatment["assigned"]
        )
        control_rate = control["applied"] / control["assigned"]
        treatment_rate = treatment["applied"] / treatment["assigned"]
        weight = total_by_segment[segment] / pooled_total
        standardized_control += weight * control_rate
        standardized_treatment += weight * treatment_rate
        standardized_unsub_control += weight * (control["unsubscribed"] / control["assigned"])
        standardized_unsub_treatment += weight * (treatment["unsubscribed"] / treatment["assigned"])
        variance_control += weight * weight * control_rate * (1.0 - control_rate) / control["assigned"]
        variance_treatment += weight * weight * treatment_rate * (1.0 - treatment_rate) / treatment["assigned"]
        control_distribution[segment] = control["assigned"] / control_total
        treatment_distribution[segment] = treatment["assigned"] / treatment_total
        effect = treatment_rate - control_rate
        segment_effect_signs.append(1 if effect > 0 else -1 if effect < 0 else 0)
        control_interval = wilson_interval(control["applied"], control["assigned"])
        treatment_interval = wilson_interval(treatment["applied"], treatment["assigned"])
        segment_rows.append({
            "segment": segment,
            "weight_in_target_population": stable_float(weight, 8),
            "control_assigned": control["assigned"],
            "treatment_assigned": treatment["assigned"],
            "control_rate": stable_float(control_rate, 8),
            "treatment_rate": stable_float(treatment_rate, 8),
            "absolute_effect": result["absolute_effect"],
            "relative_lift": result["relative_lift"],
            "p_value": result["p_value"],
            "control_ci_low": stable_float(control_interval[0], 8),
            "control_ci_high": stable_float(control_interval[1], 8),
            "treatment_ci_low": stable_float(treatment_interval[0], 8),
            "treatment_ci_high": stable_float(treatment_interval[1], 8),
        })

    stratified_effect = standardized_treatment - standardized_control
    stratified_se = math.sqrt(variance_control + variance_treatment)
    stratified_z = stratified_effect / stratified_se if stratified_se else 0.0
    stratified_p = 2.0 * (1.0 - normal_cdf(abs(stratified_z)))
    total_variation_distance = 0.5 * sum(
        abs(control_distribution[segment] - treatment_distribution[segment])
        for segment in by_segment
    )
    aggregate_sign = 1 if aggregate["absolute_effect"] > 0 else -1 if aggregate["absolute_effect"] < 0 else 0
    simpsons_paradox = bool(segment_effect_signs) and all(sign > 0 for sign in segment_effect_signs) and aggregate_sign < 0
    guardrail_effect = standardized_unsub_treatment - standardized_unsub_control

    findings = [
        {
            "finding_id": "EX-001",
            "severity": "critical" if simpsons_paradox else "info",
            "rule_id": "SIMPSONS_PARADOX",
            "message": "The aggregate treatment effect has the opposite sign from every segment-level effect." if simpsons_paradox else "No aggregate/segment sign reversal detected.",
            "impact": "A pooled rollout decision would confound treatment performance with a large change in traffic mix.",
            "remediation": "Use blocked randomization or a pre-specified post-stratified estimand and run a confirmatory experiment.",
        },
        {
            "finding_id": "EX-002",
            "severity": "high" if total_variation_distance > 0.10 else "info",
            "rule_id": "SEGMENT_IMBALANCE",
            "message": f"Variant segment-distribution distance is {total_variation_distance:.3f}.",
            "impact": "Treatment and control do not represent the same mix of pre-treatment segments.",
            "remediation": "Balance assignment within segment and monitor allocation at ingestion time.",
        },
    ]
    if srm_p_value < 0.01:
        findings.append({
            "finding_id": "EX-003",
            "severity": "critical",
            "rule_id": "SAMPLE_RATIO_MISMATCH",
            "message": f"Overall sample-ratio mismatch p-value is {srm_p_value:.6f}.",
            "impact": "Assignment or event logging may be broken.",
            "remediation": "Stop interpretation until randomization and exposure logging are repaired.",
        })

    decision = {
        "status": "RE-RANDOMIZE_AND_CONFIRM" if simpsons_paradox or total_variation_distance > 0.10 else "REVIEW_FOR_ROLLOUT",
        "primary_estimand": "post-stratified application conversion effect",
        "aggregate_effect": aggregate["absolute_effect"],
        "stratified_effect": stable_float(stratified_effect, 8),
        "stratified_p_value": stable_float(stratified_p, 8),
        "standardized_control_rate": stable_float(standardized_control, 8),
        "standardized_treatment_rate": stable_float(standardized_treatment, 8),
        "standardized_unsubscribe_effect": stable_float(guardrail_effect, 8),
        "srm_p_value": stable_float(srm_p_value, 8),
        "segment_mix_total_variation_distance": stable_float(total_variation_distance, 8),
        "simpsons_paradox": simpsons_paradox,
        "recommendation": (
            "Do not use the naive pooled result. Re-run with segment-blocked assignment and preserve the pre-specified target-population weights."
            if simpsons_paradox
            else "Review statistical and operational guardrails before rollout."
        ),
    }
    return {
        "aggregate": aggregate,
        "segments": segment_rows,
        "decision": decision,
        "findings": findings,
    }
