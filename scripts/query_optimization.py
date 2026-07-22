"""Query optimization assignment runner.

This script creates a local SQLite database, executes the inefficient and
optimized versions of the three assignment queries, compares their results,
and writes a markdown report to output/query_optimization_report.md.

Removing SELECT * reduces the number of columns transferred from the database,
which lowers I/O, network payload, and client-side memory usage.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "analytics.db"
OUTPUT_DIR = BASE_DIR / "output"

engine = create_engine(f"sqlite:///{DB_PATH}")


def seed_database() -> None:
	"""Create deterministic sample tables used by the optimization queries."""

	rng = np.random.default_rng(42)

	customer_count = 5000
	product_count = 150
	transaction_count = 75000

	customers = pd.DataFrame(
		{
			"id": np.arange(1, customer_count + 1),
			"customer_name": [f"Customer {i:04d}" for i in range(1, customer_count + 1)],
			"country": rng.choice(
				["USA", "Canada", "UK", "Germany", "Australia"],
				size=customer_count,
				p=[0.45, 0.15, 0.15, 0.15, 0.10],
			),
			"account_type": rng.choice(
				["Free", "Basic", "Premium", "Enterprise"],
				size=customer_count,
				p=[0.20, 0.35, 0.30, 0.15],
			),
			"customer_segment": rng.choice(
				["Consumer", "SMB", "Enterprise"],
				size=customer_count,
				p=[0.50, 0.30, 0.20],
			),
		}
	)

	products = pd.DataFrame(
		{
			"id": np.arange(1, product_count + 1),
			"product_name": [f"Product {i:03d}" for i in range(1, product_count + 1)],
			"product_category": rng.choice(
				["Software", "Services", "Hardware"],
				size=product_count,
				p=[0.55, 0.30, 0.15],
			),
		}
	)

	transaction_dates = pd.to_datetime(
		rng.choice(
			pd.date_range("2023-01-01", "2024-12-31", freq="D"),
			size=transaction_count,
		)
	)

	transactions = pd.DataFrame(
		{
			"transaction_id": np.arange(1, transaction_count + 1),
			"customer_id": rng.integers(1, customer_count + 1, size=transaction_count),
			"product_id": rng.integers(1, product_count + 1, size=transaction_count),
			"amount": np.round(rng.gamma(shape=3.0, scale=75.0, size=transaction_count), 2),
			"transaction_date": transaction_dates.strftime("%Y-%m-%d"),
		}
	)

	customers.to_sql("customers", engine, if_exists="replace", index=False)
	products.to_sql("products", engine, if_exists="replace", index=False)
	transactions.to_sql("transactions", engine, if_exists="replace", index=False)


def run_query(query: str) -> tuple[pd.DataFrame, float]:
	"""Execute a SQL query and return the result plus elapsed time in seconds."""

	start = time.perf_counter()
	result = pd.read_sql(query, engine)
	elapsed = time.perf_counter() - start
	return result, elapsed


def memory_mb(frame: pd.DataFrame) -> float:
	"""Return the approximate in-memory size of a pandas DataFrame in MB."""

	return frame.memory_usage(deep=True).sum() / (1024 ** 2)


def normalize_for_compare(frame: pd.DataFrame) -> pd.DataFrame:
	"""Sort columns and rows so two results can be compared deterministically."""

	normalized = frame.copy()
	normalized = normalized.reindex(sorted(normalized.columns), axis=1)
	return normalized.sort_values(by=list(normalized.columns)).reset_index(drop=True)


def format_seconds(seconds: float) -> str:
	return f"{seconds * 1000:.2f} ms"


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
	"""Render a small DataFrame as a markdown table without extra dependencies."""

	headers = list(frame.columns)
	lines = [
		f"| {' | '.join(headers)} |",
		f"| {' | '.join(['---'] * len(headers))} |",
	]
	for row in frame.itertuples(index=False):
		lines.append(f"| {' | '.join(str(value) for value in row)} |")
	return "\n".join(lines)


def main() -> None:
	seed_database()
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

	original_query_1 = """
	SELECT *
	FROM transactions t
	JOIN customers c ON t.customer_id = c.id
	WHERE strftime('%Y', t.transaction_date) = '2024'
	LIMIT 1000;
	"""

	optimized_query_1 = """
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
	"""

	original_result_1, original_time_1 = run_query(original_query_1)
	optimized_result_1, optimized_time_1 = run_query(optimized_query_1)
	original_core_1 = normalize_for_compare(original_result_1[optimized_result_1.columns])
	optimized_core_1 = normalize_for_compare(optimized_result_1)
	task1_identical = original_core_1.equals(optimized_core_1)

	original_query_2 = """
	SELECT t.transaction_id, t.amount, c.customer_name, p.product_name
	FROM transactions t
	JOIN customers c ON t.customer_id = c.id
	JOIN products p ON t.product_id = p.id
	WHERE t.transaction_date >= '2024-01-01'
	  AND t.amount > 100
	  AND c.country = 'USA'
	LIMIT 5000;
	"""

	optimized_query_2 = """
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
	"""

	transactions_count = int(
		pd.read_sql("SELECT COUNT(*) AS row_count FROM transactions", engine).iloc[0, 0]
	)
	filtered_transactions = int(
		pd.read_sql(
			"""
			SELECT COUNT(*) AS row_count
			FROM transactions
			WHERE transaction_date >= '2024-01-01'
			  AND amount > 100
			""",
			engine,
		).iloc[0, 0]
	)

	result_inefficient_2, inefficient_time_2 = run_query(original_query_2)
	result_efficient_2, efficient_time_2 = run_query(optimized_query_2)
	task2_identical = normalize_for_compare(result_inefficient_2).equals(
		normalize_for_compare(result_efficient_2)
	)
	reduction_factor = (
		transactions_count / filtered_transactions if filtered_transactions else float("inf")
	)

	original_query_3 = """
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
	"""

	optimized_query_3 = """
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
	"""

	result_original_3, original_time_3 = run_query(original_query_3)
	result_optimized_3, optimized_time_3 = run_query(optimized_query_3)
	task3_identical = normalize_for_compare(result_original_3).equals(
		normalize_for_compare(result_optimized_3)
	)

	comparison = pd.DataFrame(
		{
			"Metric": [
				"Columns Selected",
				"Intermediate Rows",
				"Filters Applied Before Join",
				"Nesting Depth",
				"Readability Score",
			],
			"Original": [
				f"{original_result_1.shape[1]} columns (SELECT *)",
				f"{transactions_count:,} rows",
				"No",
				"3 levels",
				"Hard to follow",
			],
			"Optimized": [
				f"{optimized_result_1.shape[1]} explicit columns",
				f"{filtered_transactions:,} rows",
				"Yes",
				"1 level (CTEs)",
				"Clear steps",
			],
		}
	)

	query_1_time_saving = original_time_1 - optimized_time_1
	query_1_memory_saving = memory_mb(original_result_1) - memory_mb(optimized_result_1)

	comparison_markdown = dataframe_to_markdown(comparison)

	report = f"""# Analytical SQL Query Optimization Report

## Summary

{comparison_markdown}

## Task 1 - SELECT * to Explicit Columns

### Original Query

```sql
{original_query_1.strip()}
```

### Optimized Query

```sql
{optimized_query_1.strip()}
```

### Results

- Original columns: {original_result_1.shape[1]}
- Optimized columns: {optimized_result_1.shape[1]}
- Original time: {format_seconds(original_time_1)}
- Optimized time: {format_seconds(optimized_time_1)}
- Original DataFrame memory: {memory_mb(original_result_1):.2f} MB
- Optimized DataFrame memory: {memory_mb(optimized_result_1):.2f} MB
- Approximate time improvement: {query_1_time_saving * 1000:.2f} ms
- Approximate memory improvement: {query_1_memory_saving:.2f} MB
- Core data identical after projecting the same columns: {task1_identical}

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
{original_query_2.strip()}
```

### Optimized Query

```sql
{optimized_query_2.strip()}
```

### Results

- Full transactions table: {transactions_count:,} rows
- Filtered transactions before join: {filtered_transactions:,} rows
- Reduction factor before join: {reduction_factor:.2f}x smaller dataset
- Original final result rows: {len(result_inefficient_2):,}
- Optimized final result rows: {len(result_efficient_2):,}
- Final results identical: {task2_identical}

### Why this helps

Filtering first reduces the number of rows that must be carried into join operations, which lowers CPU, memory, and sort/hash work in the join stage.

## Task 3 - CTEs for Readability

### Original Query

```sql
{original_query_3.strip()}
```

### Refactored Query

```sql
{optimized_query_3.strip()}
```

### Results

- Original result rows: {len(result_original_3):,}
- Refactored result rows: {len(result_optimized_3):,}
- Identical results: {task3_identical}

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
"""

	report_path = OUTPUT_DIR / "query_optimization_report.md"
	report_path.write_text(report, encoding="utf-8")

	summary_path = OUTPUT_DIR / "query_optimization_summary.txt"
	summary_path.write_text(
		"\n".join(
			[
				"Analytical SQL Query Optimization",
				f"Task 1 identical core data: {task1_identical}",
				f"Task 2 identical final results: {task2_identical}",
				f"Task 3 identical final results: {task3_identical}",
				f"Task 2 reduction factor: {reduction_factor:.2f}x",
			]
		),
		encoding="utf-8",
	)

	print("Task 1 original result shape:", original_result_1.shape)
	print("Task 1 optimized result shape:", optimized_result_1.shape)
	print("Task 1 identical core data:", task1_identical)
	print("Task 2 original rows:", len(result_inefficient_2))
	print("Task 2 optimized rows:", len(result_efficient_2))
	print("Task 2 reduction factor before join:", f"{reduction_factor:.2f}x")
	print("Task 3 original rows:", len(result_original_3))
	print("Task 3 optimized rows:", len(result_optimized_3))
	print("Task 3 identical final results:", task3_identical)
	print(f"Report written to {report_path}")


if __name__ == "__main__":
	main()