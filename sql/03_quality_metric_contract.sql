-- Customer outcome: one final observation per unique workflow.
WITH dedup AS (
    SELECT DISTINCT event_id, workflow_id, week, attempt, status, customer_impact
    FROM raw_qa_events
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY workflow_id ORDER BY CAST(attempt AS INTEGER) DESC, event_id DESC) AS rn
    FROM dedup
)
SELECT
    week,
    COUNT(*) AS workflows,
    AVG(CASE WHEN status = 'failure' THEN 1.0 ELSE 0.0 END) AS final_failure_rate,
    AVG(CASE WHEN customer_impact = 'true' THEN 1.0 ELSE 0.0 END) AS customer_impact_rate
FROM ranked
WHERE rn = 1
GROUP BY week
ORDER BY week;
