# KPI Computation Sources & Data Lineage

## Overview

All five KPI cards in `kpi_dashboard.py` are computed from the validated
clean data layer (SQLite tables). No values are hardcoded. All date ranges
are calculated automatically from `date.today()` so a new dataset flows
through to updated KPIs without any code changes.

---

## KPI 1: Total Revenue

- **Source table:** `orders`
- **Column:** `order_amount`
- **Aggregation:** `SUM(order_amount)` filtered to current calendar month
- **Period comparison:** Prior calendar month (auto-calculated)
- **SQL:**
  ```sql
  -- Current month
  SELECT COALESCE(SUM(order_amount), 0)
  FROM orders
  WHERE order_date >= date('now', 'start of month');

  -- Prior month
  SELECT COALESCE(SUM(order_amount), 0)
  FROM orders
  WHERE order_date >= date('now', 'start of month', '-1 month')
    AND order_date < date('now', 'start of month');
  ```
- **Validation:** Cross-checked against `orders_df['order_amount'].sum()` in 2.44 — values match
- **Direction:** Higher is better → increase = 🟢, decrease = 🔴
- **Business question:** Are we hitting monthly revenue targets?

---

## KPI 2: Active Users

- **Source table:** `logins`
- **Column:** `user_id`
- **Aggregation:** `COUNT(DISTINCT user_id)` in the current calendar month
- **Period comparison:** Prior calendar month (auto-calculated)
- **SQL:**
  ```sql
  -- Current month
  SELECT COUNT(DISTINCT user_id)
  FROM logins
  WHERE login_date >= date('now', 'start of month');

  -- Prior month
  SELECT COUNT(DISTINCT user_id)
  FROM logins
  WHERE login_date >= date('now', 'start of month', '-1 month')
    AND login_date < date('now', 'start of month');
  ```
- **Validation:** Cross-checked against `logins_df['user_id'].nunique()` filtered by date in 2.44 — values match
- **Direction:** Higher is better → increase = 🟢, decrease = 🔴
- **Business question:** Is user engagement growing month over month?

---

## KPI 3: Average Order Value (AOV)

- **Source table:** `orders`
- **Column:** `order_amount`
- **Aggregation:** `AVG(order_amount)` for current calendar month
- **Period comparison:** Prior calendar month (auto-calculated)
- **SQL:**
  ```sql
  -- Current month
  SELECT COALESCE(AVG(order_amount), 0)
  FROM orders
  WHERE order_date >= date('now', 'start of month');

  -- Prior month
  SELECT COALESCE(AVG(order_amount), 0)
  FROM orders
  WHERE order_date >= date('now', 'start of month', '-1 month')
    AND order_date < date('now', 'start of month');
  ```
- **Validation:** Matches `orders_df['order_amount'].mean()` — cross-validated in 2.44
- **Direction:** Higher is better → increase = 🟢, decrease = 🔴
- **Business question:** Are customers spending more per transaction this month?

---

## KPI 4: Churn Rate

- **Source table:** `orders`
- **Column:** `customer_id`
- **Aggregation:** `(churned customers / prior month customers) × 100`
  where churned = customers who ordered in the prior month but NOT the current month
- **Period comparison:** Prior-prior month vs prior month (for the delta shown on the card)
- **SQL:**
  ```sql
  -- Customers active in prior month
  WITH prev AS (
    SELECT DISTINCT customer_id FROM orders
    WHERE order_date >= date('now', 'start of month', '-1 month')
      AND order_date < date('now', 'start of month')
  ),
  -- Customers active in current month
  curr AS (
    SELECT DISTINCT customer_id FROM orders
    WHERE order_date >= date('now', 'start of month')
  )
  SELECT
    100.0 * COUNT(*) / (SELECT COUNT(*) FROM prev) AS churn_rate
  FROM prev
  LEFT JOIN curr USING (customer_id)
  WHERE curr.customer_id IS NULL;
  ```
- **Validation:** Matches Python set-difference computation in 2.44 — values match
- **Direction:** **Lower is better** (`delta_color='inverse'` in Streamlit)
  → decrease = 🟢, increase = 🔴
- **Business question:** Are we retaining customers? Is churn getting better or worse?

---

## KPI 5: Customer Satisfaction

- **Source table:** `satisfaction_ratings`
- **Column:** `rating` (scale 1–5)
- **Aggregation:** `AVG(rating)` for current calendar month
- **Period comparison:** Prior calendar month (auto-calculated)
- **SQL:**
  ```sql
  -- Current month
  SELECT COALESCE(AVG(rating), 0)
  FROM satisfaction_ratings
  WHERE rating_date >= date('now', 'start of month');

  -- Prior month
  SELECT COALESCE(AVG(rating), 0)
  FROM satisfaction_ratings
  WHERE rating_date >= date('now', 'start of month', '-1 month')
    AND rating_date < date('now', 'start of month');
  ```
- **Validation:** Directly from ratings table — single aggregation, no drift risk
- **Direction:** Higher is better → increase = 🟢, decrease = 🔴
- **Business question:** Are customers satisfied enough to return and recommend us?

---

## Trend Indicator Logic

All KPI deltas use `get_trend_indicator()` in `kpi_dashboard.py`.

| Change | Standard metrics | Inverted metrics (Churn) |
|---|---|---|
| > +2% | 🟢 Green ↑ | 🔴 Red ↑ |
| −2% to +2% | 🟡 Yellow → | 🟡 Yellow → |
| < −2% | 🔴 Red ↓ | 🟢 Green ↓ |

Threshold of ±2% separates trending from flat (yellow band).

---

## Auto-Update Behaviour

KPI values are cached for 5 minutes (`@st.cache_data(ttl=300)`).
All date ranges use `date.today()` at query time — never hardcoded strings.
When new data is inserted into `orders`, `logins`, or `satisfaction_ratings`,
the KPIs update on the next cache refresh without any code changes.

---

## Files

| File | Purpose |
|---|---|
| `kpi_dashboard.py` | Streamlit app: Tasks 1–4 |
| `kpi_sources.md` | This document: Task 5 — data lineage |
| `analytics.db` | SQLite database: all source tables |
| `validation_script.py` | 2.44 cross-validation for Revenue, Active Users, AOV |
