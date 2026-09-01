-- Reference SQL: aggregate each one-to-many source before joining.
WITH line_fact AS (
    SELECT
        order_id,
        SUM(CAST(quantity AS REAL) * CAST(unit_price AS REAL)) AS gross_revenue,
        SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) AS gross_cogs
    FROM raw_order_lines
    GROUP BY order_id
),
return_fact AS (
    SELECT
        l.order_id,
        SUM(CAST(r.quantity AS REAL) * CAST(l.unit_price AS REAL)) AS return_revenue,
        SUM(CAST(r.quantity AS REAL) * CAST(l.unit_cost AS REAL)) AS return_cogs
    FROM raw_returns r
    JOIN raw_order_lines l ON l.line_id = r.line_id
    GROUP BY l.order_id
),
payment_dedup AS (
    SELECT payment_id, invoice_id, MAX(amount) AS amount
    FROM raw_payments
    WHERE payment_status = 'posted'
    GROUP BY payment_id, invoice_id
),
payment_fact AS (
    SELECT invoice_id, SUM(CAST(amount AS REAL)) AS cash_collected
    FROM payment_dedup
    GROUP BY invoice_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    o.channel,
    o.region,
    lf.gross_revenue,
    COALESCE(rf.return_revenue, 0) AS return_revenue,
    lf.gross_revenue - COALESCE(rf.return_revenue, 0) AS net_revenue,
    lf.gross_cogs - COALESCE(rf.return_cogs, 0) AS net_cogs,
    CAST(i.invoice_total AS REAL) AS invoice_total,
    COALESCE(pf.cash_collected, 0) AS cash_collected
FROM raw_orders o
JOIN line_fact lf ON lf.order_id = o.order_id
JOIN raw_invoices i ON i.order_id = o.order_id
LEFT JOIN return_fact rf ON rf.order_id = o.order_id
LEFT JOIN payment_fact pf ON pf.invoice_id = i.invoice_id
WHERE o.status = 'completed';
