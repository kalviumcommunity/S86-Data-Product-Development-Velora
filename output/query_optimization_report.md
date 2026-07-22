# Analytical SQL Query Optimization Report

## Summary

| Metric | Original | Optimized |
| --- | --- | --- |
| Columns Selected | 10 columns (SELECT *) | 7 explicit columns |
| Intermediate Rows | 75,000 rows | 31,977 rows |
| Filters Applied Before Join | No | Yes |
| Nesting Depth | 3 levels | 1 level (CTEs) |
| Readability Score | Hard to follow | Clear steps |

## Task 1 - SELECT * to Explicit Columns

### Original Query

```sql
SELECT *
	FROM transactions t
	JOIN customers c ON t.customer_id = c.id
	WHERE strftime('%Y', t.transaction_date) = '2024'
	LIMIT 1000;
```

### Optimized Query

```sql
SELECT
		-- transaction_id answers: which transaction is being analyzed?
		t.transaction_id,
		-- transaction_date answers: when did the purchase happen?
		t.transaction_date,
		-- amount answers: how much revenue did the transaction generate?
		t.amount,
		-- customer_id keeps the transaction linked to the customer record.
		t.customer_id,
		-- customer_name answers: who made the purchase?
		c.customer_name,
		-- country answers: where are these transactions coming from?
		c.country,
		-- account_type answers: what subscription/account tier is the customer on?
		c.account_type
	FROM transactions t
	JOIN customers c ON t.customer_id = c.id
	WHERE strftime('%Y', t.transaction_date) = '2024'
	LIMIT 1000;
```

### Results

- Original columns: 10
- Optimized columns: 7
- Original time: 43.78 ms
- Optimized time: 34.24 ms
- Original DataFrame memory: 0.31 MB
- Optimized DataFrame memory: 0.24 MB
- Approximate time improvement: 9.55 ms
- Approximate memory improvement: 0.07 MB
- Core data identical after projecting the same columns: True

### Why the columns were selected

- transaction_id: uniquely identifies the transaction for audit and deduplication.
- transaction_date: answers when the transaction happened.
- amount: answers how much revenue the transaction generated.
- customer_id: preserves the relationship back to the customer dimension.
- customer_name: answers which customer made the purchase.
- country: answers where the customer is located.
- account_type: answers what type of account generated the transaction.

### Performance note

Removing SELECT * reduces payload size, lowers client-side memory usage, and avoids transferring columns that the analysis does not use.

## Task 2 - Filter Before JOINs

### Original Query

```sql
SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
	FROM transactions t
	JOIN customers c ON t.customer_id = c.id
	JOIN products p ON t.product_id = p.id
	WHERE t.transaction_date >= '2024-01-01'
	  AND t.amount > 100
	  AND c.country = 'USA'
	LIMIT 5000;
```

### Optimized Query

```sql
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
	JOIN customers c ON ft.customer_id = c.id
	JOIN products p ON ft.product_id = p.id
	WHERE c.country = 'USA'
	LIMIT 5000;
```

### Results

- Full transactions table: 75,000 rows
- Filtered transactions before join: 31,977 rows
- Reduction factor before join: 2.35x smaller dataset
- Original final result rows: 5,000
- Optimized final result rows: 5,000
- Final results identical: True

### Why this helps

Filtering first reduces the number of rows that must be carried into join operations, which lowers CPU, memory, and sort/hash work in the join stage.

## Task 3 - CTEs for Readability

### Original Query

```sql
SELECT customer_segment, AVG(revenue_per_transaction) AS avg_transaction_value
	FROM (
		SELECT
			c.customer_segment,
			AVG(t.amount) AS revenue_per_transaction,
			COUNT(DISTINCT t.transaction_id) AS transaction_count
		FROM (
			SELECT t.transaction_id, t.amount, t.customer_id
			FROM transactions t
			WHERE t.transaction_date >= '2024-01-01'
		) t
		JOIN customers c ON t.customer_id = c.id
		GROUP BY c.customer_segment
	) grouped
	GROUP BY customer_segment
	ORDER BY avg_transaction_value DESC;
```

### Refactored Query

```sql
WITH recent_transactions AS (
		-- Step 1: keep only recent transactions so downstream steps process less data.
		SELECT transaction_id, amount, customer_id
		FROM transactions
		WHERE transaction_date >= '2024-01-01'
	),
	customer_with_segment AS (
		-- Step 2: attach customer segment information to each recent transaction.
		SELECT
			rt.transaction_id,
			rt.amount,
			c.customer_segment
		FROM recent_transactions rt
		JOIN customers c ON rt.customer_id = c.id
	),
	segment_metrics AS (
		-- Step 3: compute the metrics used by the dashboard at segment level.
		SELECT
			customer_segment,
			COUNT(DISTINCT transaction_id) AS transaction_count,
			AVG(amount) AS avg_transaction_value,
			SUM(amount) AS total_revenue
		FROM customer_with_segment
		GROUP BY customer_segment
	)
	SELECT
		customer_segment,
		avg_transaction_value
	FROM segment_metrics
	ORDER BY avg_transaction_value DESC;
```

### Results

- Original result rows: 3
- Refactored result rows: 3
- Identical results: True

### CTE breakdown

- recent_transactions: filters the fact table to the time window the dashboard needs.
- customer_with_segment: joins customer dimension data to each filtered transaction.
- segment_metrics: computes the final metrics used for reporting.

## Best Practices Applied

- Query 1 used explicit column selection to avoid SELECT * and reduce unnecessary data transfer.
- Query 2 used a CTE to filter the largest table before joining to dimensions.
- Query 3 used CTEs to replace nested subqueries and make each step independently testable.

## Specific Improvements

- Query 1: original inefficiency was fetching every column; the fix selected only the business-relevant fields.
- Query 2: original inefficiency was joining a larger dataset than needed; the fix shrank the transaction set first.
- Query 3: original inefficiency was hard-to-read nesting; the fix split the logic into named, testable CTEs.

## Follow-up Questions

1. Index on a high-cardinality filter column: an index lets the database locate matching rows without scanning the full table, which can dramatically reduce I/O. The tradeoff is extra storage and slower writes because the index must be maintained on insert, update, and delete.

2. CTE reuse behavior: in SQLite, a non-recursive CTE is typically treated as part of the statement plan and may be materialized or inlined depending on the optimizer. In many databases, the engine can cache or materialize it when reused, but the exact behavior is database-specific. For repeated reuse of the same intermediate result, a materialized view or an explicit temp table can be more predictable.

3. Techniques beyond SELECT optimization: partitioning, materialized views, pre-aggregated summary tables, clustering on join/filter columns, incremental refreshes, and better indexing can all improve performance when the filtered dataset is still very large.
