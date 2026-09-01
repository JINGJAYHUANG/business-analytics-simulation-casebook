# Experiment interpretation

## The fixture

The synthetic treatment improves application conversion within every pre-treatment segment. Treatment and control nevertheless receive very different segment mixes. The naive aggregate therefore points in the opposite direction.

## What the case teaches

- Overall 50/50 assignment does not guarantee covariate balance.
- A pooled treatment-control comparison can answer the wrong estimand.
- Post-stratification can recover a target-population comparison only when the strata were defined independently of outcome.
- A corrected analysis does not repair a broken randomization process.
- Guardrails such as unsubscribe rate must remain visible.

## Recommended operational response

Do not choose the result that supports the desired narrative. Use the inconsistency as evidence that assignment and exposure logging require repair, then run a confirmatory experiment with blocked randomization and pre-specified weights.
