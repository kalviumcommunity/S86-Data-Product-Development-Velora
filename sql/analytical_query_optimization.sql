-- =========================================================
-- Analytical SQL Query Optimization
-- =========================================================

-- =========================================================
-- Task 1: SELECT * → Explicit Columns
-- =========================================================

-- Original Query
SELECT *
FROM transactions t
JOIN customers c
ON t.customer_id = c.id
WHERE strftime('%Y', t.transaction_date) = '2024'
LIMIT 1000;

-- Optimized Query
SELECT
    -- Identifies the transaction for audit and traceability.
    t.transaction_id,
    -- Answers when the purchase happened.
    t.transaction_date,
    -- Answers how much revenue the transaction generated.
    t.amount,
    -- Keeps the row linked to the customer record for downstream joins.
    t.customer_id,
    -- Answers which customer made the purchase.
    c.customer_name,
    -- Answers where the customer is located.
    c.country,
    -- Answers what account tier generated the transaction.
    c.account_type
FROM transactions t
JOIN customers c
ON t.customer_id = c.id
WHERE strftime('%Y', t.transaction_date) = '2024'
LIMIT 1000;


-- =========================================================
-- Task 2: Filter Before JOIN
-- =========================================================

-- Original Query
SELECT
    t.transaction_id,
    t.amount,
    c.customer_name,
    p.product_name
FROM transactions t
JOIN customers c
ON t.customer_id = c.id
JOIN products p
ON t.product_id = p.id
WHERE t.transaction_date >= '2024-01-01'
  AND t.amount > 100
  AND c.country = 'USA'
LIMIT 5000;

-- Optimized Query
WITH filtered_transactions AS (
    SELECT
        transaction_id,
        customer_id,
        product_id,
        amount,
        transaction_date
    FROM transactions
    WHERE transaction_date >= '2024-01-01'
      AND amount > 100
)
SELECT
    ft.transaction_id,
    ft.amount,
    c.customer_name,
    p.product_name
FROM filtered_transactions ft
JOIN customers c
ON ft.customer_id = c.id
JOIN products p
ON ft.product_id = p.id
WHERE c.country = 'USA'
LIMIT 5000;


-- =========================================================
-- Task 3: Replace Nested Queries with CTEs
-- =========================================================

-- Original Query
SELECT customer_segment,
       AVG(revenue_per_transaction) AS avg_transaction_value
FROM (
    SELECT
        c.customer_segment,
        AVG(t.amount) AS revenue_per_transaction,
        COUNT(DISTINCT t.transaction_id) AS transaction_count
    FROM (
        SELECT
            transaction_id,
            amount,
            customer_id
        FROM transactions
        WHERE transaction_date >= '2024-01-01'
    ) t
    JOIN customers c
    ON t.customer_id = c.id
    GROUP BY c.customer_segment
) grouped
GROUP BY customer_segment
ORDER BY avg_transaction_value DESC;

-- Optimized Query
WITH recent_transactions AS (
    -- Step 1: Filter to the date range needed for the report.
    SELECT
        transaction_id,
        amount,
        customer_id
    FROM transactions
    WHERE transaction_date >= '2024-01-01'
),

customer_segments AS (
    -- Step 2: Attach customer segment information.
    SELECT
        rt.transaction_id,
        rt.amount,
        c.customer_segment
    FROM recent_transactions rt
    JOIN customers c
    ON rt.customer_id = c.id
),

segment_metrics AS (
    -- Step 3: Aggregate the segment-level metrics.
    SELECT
        customer_segment,
        COUNT(DISTINCT transaction_id) AS transaction_count,
        AVG(amount) AS avg_transaction_value,
        SUM(amount) AS total_revenue
    FROM customer_segments
    GROUP BY customer_segment
)

SELECT
    customer_segment,
    avg_transaction_value
FROM segment_metrics
ORDER BY avg_transaction_value DESC;