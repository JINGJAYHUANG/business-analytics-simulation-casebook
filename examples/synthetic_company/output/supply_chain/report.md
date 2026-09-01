# Case 1 — Supply-chain segmentation

## Decision

Choose differentiated operating policies for supplier-lane relationships without treating descriptive clusters as causal proof.

## Method

- Unit of analysis: one supplier-lane relationship.
- Features: landed_cost_per_unit, lead_time_days, service_gap, defect_rate, demand_cv, expedite_rate.
- Candidate cluster counts: 2 through 6.
- Selection rule: highest deterministic silhouette among solutions with at least eight lanes per cluster.
- Selected k: **4**.
- Selected silhouette: **0.759942**.

## K selection

| k | Silhouette | Min size | Max size | Eligible |
|---|---|---|---|---|
| 2 | 0.592899 | 20 | 60 | True |
| 3 | 0.604966 | 20 | 40 | True |
| 4 | 0.759942 | 20 | 20 | True |
| 5 | 0.648438 | 10 | 20 | True |
| 6 | 0.639943 | 5 | 20 | False |

## Segment profiles

| Segment | Lanes | Annual-unit share | Landed cost/unit | Lead days | On-time | Fill | Defect | Demand CV | Expedite |
|---|---|---|---|---|---|---|---|---|---|
| volatile_growth | 20 | 0.279266 | 13.0495 | 13.7675 | 0.870375 | 0.90229 | 0.01904 | 0.684425 | 0.157475 |
| constrained_recovery | 20 | 0.164574 | 16.5895 | 30.8075 | 0.75647 | 0.81592 | 0.04398 | 0.478315 | 0.281525 |
| strategic_reliable | 20 | 0.327601 | 15.413 | 9.578 | 0.973105 | 0.98245 | 0.00556 | 0.18122 | 0.02538 |
| cost_efficient_routine | 20 | 0.228558 | 10.8035 | 17.582 | 0.93137 | 0.939455 | 0.012435 | 0.28195 | 0.05549 |

## Policy actions

| Segment | Policy | Action | Risk |
|---|---|---|---|
| strategic_reliable | protect strategic capacity | Use collaborative forecasting, longer commitments, and quarterly resilience reviews. | Over-dependence can hide concentration risk even when service is strong. |
| cost_efficient_routine | standardize and automate | Use stable reorder parameters, low-touch replenishment, and exception-based management. | Low unit cost should not justify reducing service monitoring below the agreed floor. |
| volatile_growth | add flexibility before volume | Use shorter planning cycles, option capacity, and demand-triggered buffers. | Average demand conceals volatility; fixed commitments can create inventory whiplash. |
| constrained_recovery | contain exposure and improve capability | Set corrective-action milestones, dual-source critical items, and cap expedited spend. | A cost-only sourcing decision can turn service and quality losses into hidden total cost. |

## Findings and boundaries

| ID | Severity | Rule | Finding | Required response |
|---|---|---|---|---|
| SC-001 | info |  |  |  |
| SC-002 | warning |  |  |  |
