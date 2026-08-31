-- Anti-pattern: line revenue is multiplied when one invoice has multiple payment rows.
-- This query exists for teaching and automated tests; do not use it for reporting.
SELECT
    SUM(CAST(l.quantity AS REAL) * CAST(l.unit_price AS REAL)) AS overstated_gross_revenue
FROM raw_orders o
JOIN raw_order_lines l ON l.order_id = o.order_id
JOIN raw_invoices i ON i.order_id = o.order_id
LEFT JOIN raw_payments p ON p.invoice_id = i.invoice_id
WHERE o.status = 'completed';
