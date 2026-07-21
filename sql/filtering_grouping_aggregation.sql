-- Task 1
-- WHERE filters rows BEFORE aggregation.
-- Date filter: Only analyze 2024 transactions.
-- Amount > 0: Excludes refunds or invalid values.
-- Completed status: Includes only successful transactions.

SELECT
    customer_id,
    SUM(amount) AS annual_revenue,
    COUNT(*) AS transaction_count
FROM transactions
WHERE transaction_date >= DATE '2024-01-01'
  AND amount > 0
  AND transaction_status = 'completed'
GROUP BY customer_id
ORDER BY annual_revenue DESC;

-- Task 2
-- WHERE executes before GROUP BY.

SELECT
    c.customer_type,
    DATE_TRUNC('month', t.transaction_date)::DATE AS month,
    COUNT(DISTINCT t.customer_id) AS unique_customers,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS monthly_revenue,
    AVG(t.amount) AS avg_transaction
FROM transactions t
JOIN customers c
ON t.customer_id = c.customer_id
WHERE t.transaction_date >= DATE '2024-01-01'
GROUP BY
    c.customer_type,
    DATE_TRUNC('month', t.transaction_date)
ORDER BY month DESC;

-- Task 3
-- HAVING filters groups AFTER aggregation.

SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS annual_revenue
FROM transactions
WHERE transaction_date >= DATE '2024-01-01'
GROUP BY customer_id
HAVING
    SUM(amount) > 10000
    AND COUNT(*) >= 5
ORDER BY annual_revenue DESC;

-- Task 4
-- WHERE filters valid Enterprise transactions.
-- HAVING filters Enterprise customers whose total annual spending exceeds $10,000.

SELECT
    t.customer_id,
    c.customer_type,
    SUM(t.amount) AS annual_spending,
    COUNT(*) AS purchase_count
FROM transactions t
JOIN customers c
ON t.customer_id = c.customer_id
WHERE
    c.customer_type = 'Enterprise'
    AND t.transaction_date >= DATE '2024-01-01'
    AND t.transaction_status = 'completed'
    AND t.amount > 0
GROUP BY
    t.customer_id,
    c.customer_type
HAVING
    SUM(t.amount) > 10000
ORDER BY annual_spending DESC;

-- Task 5
-- Rank customer segments by revenue.

SELECT
    c.customer_type,
    c.industry,
    COUNT(DISTINCT t.customer_id) AS customers,
    SUM(t.amount) AS total_revenue,
    ROUND(AVG(t.amount),2) AS avg_order,
    RANK() OVER(
        ORDER BY SUM(t.amount) DESC
    ) AS revenue_rank
FROM transactions t
JOIN customers c
ON t.customer_id = c.customer_id
WHERE
    t.transaction_date >= DATE '2024-01-01'
GROUP BY
    c.customer_type,
    c.industry
HAVING
    COUNT(DISTINCT t.customer_id) >= 10
ORDER BY
    total_revenue DESC
LIMIT 20;
