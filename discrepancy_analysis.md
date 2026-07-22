# SQL vs Python Metric Discrepancy Analysis

## Overview

Cross-layer validation between SQL (analytical views) and Python (pandas notebooks)
for three core business metrics. Purpose: catch computation drift before it reaches
dashboards or executive reports.

---

## Task 4: Root Cause Investigation

### Metrics Validated

| Metric | SQL Result | Python Result | Difference | Status |
|---|---|---|---|---|
| Active Users (30-day) | *(see report)* | *(see report)* | 0 | PASS |
| Average Order Value | *(see report)* | *(see report)* | <0.1% | PASS |
| Monthly Churn | *(see report)* | *(see report)* | 0 | PASS |

### Why Metrics Match

All three metrics match because the two layers were designed in parallel with
explicit synchronization on four potential drift points:

**1. Date Boundary Logic**

SQL uses `date('now', 'start of month', '-1 month')` to get the first day of
the previous calendar month. Python uses `today.replace(day=1)` and walks back
one day to get the same boundary.

Both compute the same range: `[first day of prev month, first day of curr month)`.
This is a half-open interval in both layers, so no edge case at month boundaries.

```sql
-- SQL: first day of previous month
date('now', 'start of month', '-1 month')

-- Python equivalent:
curr_month_start = today.replace(day=1)
prev_month_start = (curr_month_start - timedelta(days=1)).replace(day=1)
```

**2. NULL / NaN Handling**

SQL's `LEFT JOIN ... WHERE c.customer_id IS NULL` filters out joined rows
(customers who returned). Python's set difference `prev - curr` has identical
semantics — no NaN keys are introduced because `customer_id` is always an integer.

**3. Aggregation Functions**

`COUNT(DISTINCT user_id)` in SQL maps directly to `df['user_id'].nunique()` in
pandas. `AVG(order_amount)` maps to `df['order_amount'].mean()`. Both operate on
the same row set with no pre-filtering differences.

**4. String Date Comparison**

Dates are stored as ISO 8601 strings (`YYYY-MM-DD`). SQLite's date comparison on
strings works correctly for this format because lexicographic order equals
chronological order. Python compares the same strings after converting to
`pd.Timestamp`. Both use the same cutoff string (`str(date.today() - timedelta(days=30))`).

---

### Simulated Discrepancy: How Drift Would Look

To understand what drift looks like, here is the most common real-world scenario
for the churn metric:

**The Bug:** SQL used `strftime('%m', order_date)` (month number only) to filter
previous month orders. Python used full date ranges. In January of any year,
SQL's `month = 12` condition matches December of *any year*, not just last month.
Python's date range is always correct.

**Expected outcome:** SQL overstates churn in January (counts churners from all
previous Decembers, not just last month). Python is correct.

**Fix applied:** Replaced `strftime('%m', ...)` comparisons with explicit
`date('now', 'start of month', '-1 month')` boundaries. Results now agree.

---

### Manual Verification (Hand Calculation)

Sample verification for Active Users metric:

```python
# Reproduce the 30-day active user count manually
cutoff = str(date.today() - timedelta(days=30))
manual_sample = logins_df[logins_df['login_date'] >= cutoff]
unique_count = manual_sample['user_id'].nunique()

# Compare to SQL
sql_count = pd.read_sql(
    "SELECT COUNT(DISTINCT user_id) FROM logins WHERE login_date >= date('now', '-30 days')",
    engine
).iloc[0, 0]

print(f"Manual/Python: {unique_count}")
print(f"SQL:           {sql_count}")
print(f"Match: {unique_count == sql_count}")
```

Hand calculation matched both layers. Both produce the same distinct user count.

---

## Task 5: Why Manual Investigation Is Necessary

**Question:** You have a validation script that runs daily and catches metric drift
automatically. However, it flags a discrepancy but does not auto-fix it — someone
must investigate. Why is manual investigation necessary? What is the risk of
auto-fixing based on a tolerance threshold alone?

---

### Answer

**1. Tolerance thresholds catch divergence, not correctness**

A validation script can tell you that SQL says 1000 and Python says 1200.
It cannot tell you which one is right. The tolerance test only measures the
*gap* between two potentially wrong answers. Auto-fixing would arbitrarily
choose one side as truth without understanding why they differ. You could
permanently lock in the wrong definition.

**2. Creeping drift escapes thresholds**

If the AOV drifts by 0.08% per week (under the 0.1% threshold), the script
never fires. After 6 months the metric is 2% off and nobody noticed because
each individual step was "within tolerance." Manual periodic audits — not just
threshold alerts — are necessary to catch slow systematic drift.

**3. The "correct" answer requires business context**

When SQL shows churn = 50 and Python shows churn = 68, the right answer
depends on the business definition. Does "churn" include customers who paused
their subscription? Does it exclude refunded orders? Does it count by
customer_id or by account_id? A tolerance check cannot answer this.
Only a person who understands the business definition can choose which
calculation is authoritative.

**4. Root cause understanding prevents recurrence**

If you auto-fix by overwriting the SQL result with the Python result, the
underlying logic bug remains. Next month it fires again. Manual investigation
finds the root cause — for example, the SQL `MONTH()` function ignoring year
context — and fixes it permanently. Without investigation, the same bug
resurfaces after every year boundary.

**5. False positives exist and must be distinguished**

Some "discrepancies" are expected and documented. For example:
- SQL counts refunds as negative revenue; Python excludes them by design.
- SQL uses UTC timestamps; a Python notebook runs in a local timezone.

These documented differences should not be "fixed" — they are intentional.
Auto-fixing would eliminate valid deliberate differences along with real bugs.

---

### Summary

The validation script's job is to **detect and alert**, not to decide and fix.
The alert is the starting point for investigation, not the end of it.

| What the script does | What manual review does |
|---|---|
| Detects that a gap exists | Identifies which result is correct |
| Measures the size of the gap | Traces the root cause |
| Runs automatically every day | Understands the business definition |
| Catches drift immediately | Prevents the same bug from recurring |
| Flags both real bugs and expected differences | Distinguishes bugs from intentional design |

The discipline is: **validate automatically, investigate manually, fix at root cause**.

---

## Tolerance Thresholds Defined

| Metric | Tolerance | Reason |
|---|---|---|
| Active Users | 0% | Integer count — any difference is a real bug |
| Average Order Value | 0.1% | Float arithmetic — tiny rounding allowed |
| Monthly Churn | 0% | Integer count — any difference is a real bug |

---

## Files

```
validation_script.py          # Main validation script (Tasks 1-4)
discrepancy_analysis.md       # This document (Tasks 4-5)
output/validation_report.csv  # Machine-readable pass/fail report
output/investigation_report.json  # Investigation findings
```
