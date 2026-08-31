from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .canonical import read_csv, stable_float

FEATURES = (
    "landed_cost_per_unit",
    "lead_time_days",
    "service_gap",
    "defect_rate",
    "demand_cv",
    "expedite_rate",
)

ARCHETYPE_TARGETS = {
    "strategic_reliable": {
        "landed_cost_per_unit": 15.4,
        "lead_time_days": 9.5,
        "service_gap": 0.02,
        "defect_rate": 0.006,
        "demand_cv": 0.19,
        "expedite_rate": 0.025,
    },
    "cost_efficient_routine": {
        "landed_cost_per_unit": 10.9,
        "lead_time_days": 17.0,
        "service_gap": 0.075,
        "defect_rate": 0.012,
        "demand_cv": 0.29,
        "expedite_rate": 0.055,
    },
    "volatile_growth": {
        "landed_cost_per_unit": 13.0,
        "lead_time_days": 14.0,
        "service_gap": 0.125,
        "defect_rate": 0.019,
        "demand_cv": 0.68,
        "expedite_rate": 0.155,
    },
    "constrained_recovery": {
        "landed_cost_per_unit": 16.6,
        "lead_time_days": 31.0,
        "service_gap": 0.245,
        "defect_rate": 0.044,
        "demand_cv": 0.47,
        "expedite_rate": 0.275,
    },
}

POLICIES = {
    "strategic_reliable": {
        "policy": "protect strategic capacity",
        "action": "Use collaborative forecasting, longer commitments, and quarterly resilience reviews.",
        "risk": "Over-dependence can hide concentration risk even when service is strong.",
    },
    "cost_efficient_routine": {
        "policy": "standardize and automate",
        "action": "Use stable reorder parameters, low-touch replenishment, and exception-based management.",
        "risk": "Low unit cost should not justify reducing service monitoring below the agreed floor.",
    },
    "volatile_growth": {
        "policy": "add flexibility before volume",
        "action": "Use shorter planning cycles, option capacity, and demand-triggered buffers.",
        "risk": "Average demand conceals volatility; fixed commitments can create inventory whiplash.",
    },
    "constrained_recovery": {
        "policy": "contain exposure and improve capability",
        "action": "Set corrective-action milestones, dual-source critical items, and cap expedited spend.",
        "risk": "A cost-only sourcing decision can turn service and quality losses into hidden total cost.",
    },
}


def load_lanes(path: Path) -> list[dict[str, object]]:
    rows = []
    for row in read_csv(path):
        landed = float(row["unit_cost_usd"]) + float(row["inbound_freight_usd"])
        rows.append({
            **row,
            "annual_units": int(row["annual_units"]),
            "unit_cost_usd": float(row["unit_cost_usd"]),
            "inbound_freight_usd": float(row["inbound_freight_usd"]),
            "landed_cost_per_unit": landed,
            "lead_time_days": float(row["lead_time_days"]),
            "on_time_rate": float(row["on_time_rate"]),
            "fill_rate": float(row["fill_rate"]),
            "service_gap": 1.0 - min(float(row["on_time_rate"]), float(row["fill_rate"])),
            "defect_rate": float(row["defect_rate"]),
            "demand_cv": float(row["demand_cv"]),
            "expedite_rate": float(row["expedite_rate"]),
            "carbon_kg_per_unit": float(row["carbon_kg_per_unit"]),
        })
    return rows


def _standardize(rows: list[dict[str, object]]) -> tuple[list[list[float]], dict[str, tuple[float, float]]]:
    stats: dict[str, tuple[float, float]] = {}
    for feature in FEATURES:
        values = [float(row[feature]) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
        std = math.sqrt(variance) or 1.0
        stats[feature] = (mean, std)
    matrix = [
        [(float(row[feature]) - stats[feature][0]) / stats[feature][1] for feature in FEATURES]
        for row in rows
    ]
    return matrix, stats


def _squared_distance(left: list[float], right: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right, strict=True))


def _initial_centroids(matrix: list[list[float]], k: int) -> list[list[float]]:
    first_index = min(range(len(matrix)), key=lambda idx: (sum(value * value for value in matrix[idx]), idx))
    chosen = [first_index]
    while len(chosen) < k:
        next_index = max(
            (idx for idx in range(len(matrix)) if idx not in chosen),
            key=lambda idx: (min(_squared_distance(matrix[idx], matrix[c]) for c in chosen), -idx),
        )
        chosen.append(next_index)
    return [matrix[index][:] for index in chosen]


def kmeans(matrix: list[list[float]], k: int, max_iter: int = 200) -> tuple[list[int], list[list[float]]]:
    if not 1 < k < len(matrix):
        raise ValueError("k must be between 2 and number of rows minus one")
    centroids = _initial_centroids(matrix, k)
    assignments = [-1] * len(matrix)
    for _ in range(max_iter):
        new_assignments = [
            min(range(k), key=lambda cluster: (_squared_distance(point, centroids[cluster]), cluster))
            for point in matrix
        ]
        if new_assignments == assignments:
            break
        assignments = new_assignments
        new_centroids: list[list[float]] = []
        for cluster in range(k):
            members = [matrix[idx] for idx, label in enumerate(assignments) if label == cluster]
            if not members:
                farthest = max(
                    range(len(matrix)),
                    key=lambda idx: min(_squared_distance(matrix[idx], centroid) for centroid in centroids),
                )
                new_centroids.append(matrix[farthest][:])
            else:
                new_centroids.append([
                    sum(member[column] for member in members) / len(members)
                    for column in range(len(matrix[0]))
                ])
        centroids = new_centroids
    return assignments, centroids


def silhouette_score(matrix: list[list[float]], assignments: list[int]) -> float:
    clusters: dict[int, list[int]] = defaultdict(list)
    for index, cluster in enumerate(assignments):
        clusters[cluster].append(index)
    if len(clusters) < 2 or any(len(indices) < 2 for indices in clusters.values()):
        return -1.0
    scores: list[float] = []
    for index, point in enumerate(matrix):
        own = assignments[index]
        own_members = [member for member in clusters[own] if member != index]
        a = sum(math.sqrt(_squared_distance(point, matrix[member])) for member in own_members) / len(own_members)
        b = min(
            sum(math.sqrt(_squared_distance(point, matrix[member])) for member in members) / len(members)
            for cluster, members in clusters.items()
            if cluster != own
        )
        scores.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return sum(scores) / len(scores)


def _cluster_profiles(rows: list[dict[str, object]], assignments: list[int]) -> list[dict[str, object]]:
    groups: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row, cluster in zip(rows, assignments, strict=True):
        groups[cluster].append(row)
    profiles: list[dict[str, object]] = []
    for cluster, members in sorted(groups.items()):
        annual_units = sum(int(row["annual_units"]) for row in members)
        profile: dict[str, object] = {
            "cluster_id": cluster,
            "lane_count": len(members),
            "annual_units": annual_units,
            "annual_units_share": annual_units / sum(int(row["annual_units"]) for row in rows),
        }
        for feature in FEATURES + ("on_time_rate", "fill_rate", "carbon_kg_per_unit"):
            profile[feature] = sum(float(row[feature]) for row in members) / len(members)
        profiles.append(profile)
    return profiles


def _assign_semantic_labels(profiles: list[dict[str, object]]) -> dict[int, str]:
    if len(profiles) != 4:
        return {int(profile["cluster_id"]): f"segment_{index + 1}" for index, profile in enumerate(profiles)}
    feature_ranges: dict[str, float] = {}
    combined = profiles + [{**target, "cluster_id": -1} for target in ARCHETYPE_TARGETS.values()]
    for feature in FEATURES:
        values = [float(item[feature]) for item in combined]
        feature_ranges[feature] = max(values) - min(values) or 1.0
    labels = list(ARCHETYPE_TARGETS)
    best_cost = math.inf
    best_mapping: dict[int, str] = {}
    for permutation in itertools.permutations(labels):
        cost = 0.0
        mapping: dict[int, str] = {}
        for profile, label in zip(profiles, permutation, strict=True):
            mapping[int(profile["cluster_id"])] = label
            target = ARCHETYPE_TARGETS[label]
            cost += sum(
                ((float(profile[feature]) - float(target[feature])) / feature_ranges[feature]) ** 2
                for feature in FEATURES
            )
        if cost < best_cost:
            best_cost = cost
            best_mapping = mapping
    return best_mapping


def analyze_supply_chain(path: Path) -> dict[str, object]:
    rows = load_lanes(path)
    matrix, _ = _standardize(rows)
    k_selection: list[dict[str, object]] = []
    candidates: dict[int, tuple[list[int], list[list[float]]]] = {}
    for k in range(2, 7):
        assignments, centroids = kmeans(matrix, k)
        counts = Counter(assignments)
        score = silhouette_score(matrix, assignments)
        k_selection.append({
            "k": k,
            "silhouette_score": stable_float(score, 6),
            "minimum_cluster_size": min(counts.values()),
            "maximum_cluster_size": max(counts.values()),
            "eligible": min(counts.values()) >= 8,
        })
        candidates[k] = (assignments, centroids)
    eligible = [row for row in k_selection if row["eligible"]]
    selected_row = max(eligible, key=lambda item: (float(item["silhouette_score"]), -int(item["k"])))
    selected_k = int(selected_row["k"])
    assignments, _ = candidates[selected_k]
    profiles = _cluster_profiles(rows, assignments)
    labels = _assign_semantic_labels(profiles)
    for profile in profiles:
        label = labels[int(profile["cluster_id"])]
        profile["segment"] = label
        profile["policy"] = POLICIES.get(label, {}).get("policy", "review segment")
    assignments_rows: list[dict[str, object]] = []
    for row, cluster in zip(rows, assignments, strict=True):
        label = labels[cluster]
        assignments_rows.append({
            "lane_id": row["lane_id"],
            "supplier_id": row["supplier_id"],
            "region": row["region"],
            "segment": label,
            "landed_cost_per_unit": stable_float(float(row["landed_cost_per_unit"]), 4),
            "lead_time_days": stable_float(float(row["lead_time_days"]), 4),
            "on_time_rate": stable_float(float(row["on_time_rate"]), 4),
            "fill_rate": stable_float(float(row["fill_rate"]), 4),
            "defect_rate": stable_float(float(row["defect_rate"]), 4),
            "demand_cv": stable_float(float(row["demand_cv"]), 4),
            "expedite_rate": stable_float(float(row["expedite_rate"]), 4),
            "annual_units": row["annual_units"],
        })
    policy_rows = [
        {"segment": label, **policy}
        for label, policy in POLICIES.items()
        if label in set(labels.values())
    ]
    findings = [
        {
            "finding_id": "SC-001",
            "severity": "info",
            "title": "Segmentation is descriptive, not causal",
            "detail": "Clusters summarize operating patterns. They do not prove that any policy will cause better performance.",
        },
        {
            "finding_id": "SC-002",
            "severity": "warning",
            "title": "Scale and risk should be reviewed together",
            "detail": "High-volume relationships deserve concentration and continuity review even when service metrics are strong.",
        },
    ]
    return {
        "selected_k": selected_k,
        "selected_silhouette": selected_row["silhouette_score"],
        "feature_names": list(FEATURES),
        "k_selection": k_selection,
        "assignments": assignments_rows,
        "profiles": profiles,
        "policies": policy_rows,
        "findings": findings,
    }
