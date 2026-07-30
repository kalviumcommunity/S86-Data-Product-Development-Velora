"""
alert_config.py
---------------
BSB 2.56 - Alert Monitoring & Metric Threshold Detection

Task 3: All thresholds live here — NOT in display logic.
To change a threshold, edit this file only. The dashboard
code in app.py reads this config and never hardcodes limits.

Threshold keys map directly to metric keys produced by
compute_metrics() in app.py.
"""

# ─────────────────────────────────────────────
# Alert Threshold Configuration
# ─────────────────────────────────────────────
# Each entry defines:
#   metric    — Human-readable metric name shown in the alert banner
#   threshold — The numeric boundary that triggers the alert
#   direction — "above"  → alert when value > threshold (bad if high)
#               "below"  → alert when value < threshold (bad if low)
#   severity  — "critical" → st.error (red)
#               "warning"  → st.warning (amber)
#   message   — Plain-language description of the risk and what to do
# ─────────────────────────────────────────────

ALERT_THRESHOLDS = {

    # ── 1. Churn Rate ────────────────────────
    # Critical: losing customers fast erodes the entire revenue base.
    "churn_rate": {
        "metric":    "Churn Rate (%)",
        "threshold": 7.0,
        "direction": "above",
        "severity":  "critical",
        "message": (
            "Churn rate has exceeded the 7% safe-operating limit. "
            "Investigate which segments are churning, check recent support tickets, "
            "and escalate to the Customer Success team immediately."
        ),
    },

    # ── 2. Average Order Value ───────────────
    # Warning: drop in AOV signals pricing pressure or product-mix shift.
    "avg_order_value": {
        "metric":    "Avg Order Value ($)",
        "threshold": 80.0,
        "direction": "below",
        "severity":  "warning",
        "message": (
            "Average order value has dropped below $80. "
            "Review active promotions, check whether high-value products are "
            "out of stock, and alert the pricing team for a review."
        ),
    },

    # ── 3. Data Quality — Null Percentage ────
    # Warning: too many nulls means the pipeline is dropping data.
    "null_percentage": {
        "metric":    "Data Quality — Null % (revenue col)",
        "threshold": 5.0,
        "direction": "above",
        "severity":  "warning",
        "message": (
            "More than 5% of revenue values are null in the filtered dataset. "
            "Check the ETL pipeline for schema changes, inspect the source system "
            "for missing fields, and reprocess affected records before reporting."
        ),
    },

    # ── 4. Revenue Coverage ──────────────────
    # Warning: fewer than 10% of records shown may mean filters are too tight
    # or that a data-load issue has dropped rows.
    "coverage_pct": {
        "metric":    "Data Coverage (%)",
        "threshold": 10.0,
        "direction": "below",
        "severity":  "warning",
        "message": (
            "Less than 10% of the total dataset is visible with the current filters. "
            "This may indicate an overly narrow filter selection or a data ingestion gap. "
            "Broaden filters or check the data pipeline for the missing period."
        ),
    },

    # ── 5. Active Customers ──────────────────
    # Critical: a very low unique customer count in filtered view signals
    # either a narrow filter or a real retention problem.
    "unique_customers": {
        "metric":    "Unique Customers",
        "threshold": 5,
        "direction": "below",
        "severity":  "critical",
        "message": (
            "Fewer than 5 unique customers exist in the current filtered view. "
            "This is an unusually low number — verify that filters are not hiding "
            "valid customers, and check whether a customer-data sync has failed."
        ),
    },
}
