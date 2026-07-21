-- queries/revenue_by_segment.sql
-- Monthly revenue metrics joined with customer segment data
-- Returns: order count, total revenue, avg order value, unique customers, revenue per customer
SELECT
    c.customer_type,
    strftime('%Y-%m-01', t.transaction_date)                          AS month,
    COUNT(DISTINCT t.order_id)                                        AS order_count,
    ROUND(SUM(t.amount), 2)                                           AS monthly_revenue,
    ROUND(AVG(t.amount), 2)                                           AS avg_order_value,
    COUNT(DISTINCT t.customer_id)                                     AS unique_customers,
    ROUND(SUM(t.amount) / COUNT(DISTINCT t.customer_id), 2)           AS revenue_per_customer
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.transaction_date >= date('now', '-12 months')
GROUP BY c.customer_type,
         strftime('%Y-%m-01', t.transaction_date)
ORDER BY month DESC, monthly_revenue DESC;
