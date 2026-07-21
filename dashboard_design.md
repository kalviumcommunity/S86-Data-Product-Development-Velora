# Dashboard Design Documentation

## Overview

This dashboard follows the **information pyramid** principle — critical information at the top,
detail available on demand. Designed to serve three distinct audiences with different needs
from the same interface.

---

## Information Hierarchy Applied

### Level 1 — Status: KPI Cards (Top Row)

Five KPI cards answer "are we on track?" in under 5 seconds.

| Card | Metric | Business Question Answered |
|------|--------|---------------------------|
| 1 | Monthly Revenue ($M) | Are we hitting revenue targets this month? |
| 2 | Active Customers | Is our customer base growing or shrinking? |
| 3 | Avg Order Value ($) | Are customers spending more per transaction? |
| 4 | Churn Rate (%) | Are we retaining customers effectively? |
| 5 | NPS Score | Are customers satisfied and likely to recommend us? |

**Why these five?** Together they cover the four dimensions of business health:
revenue performance, customer growth, revenue quality, and customer satisfaction.
If all five are green, no further investigation is needed.
If one is red, the user scrolls down to the relevant trend or segment chart.

### Level 2 — Trends: Time Series Charts

Three charts that reveal patterns over the past 12 months.

**Chart 1: Monthly Revenue Trend (Line Chart)**
- Shows month-over-month revenue trajectory
- Green dashed target line ($5M) gives immediate context — number alone is meaningless
- Current month highlighted in red for instant orientation
- Answers: "Is revenue trending up? Are we above or below target?"

**Chart 2: Customer Growth vs Churn (Dual-Axis Line Chart)**
- Active customers (left axis, blue) and churned customers (right axis, red) on same time axis
- Dual axis reveals the relationship: are we growing fast enough to offset churn?
- Answers: "Is net customer growth positive? Is churn accelerating?"

**Chart 3: Monthly Churn Rate Trend (Bar Chart)**
- Bars coloured green (<4% target) or red (≥4% target) — no legend needed, colour tells the story
- Target line at 4.0% provides context for every bar
- Answers: "Are we consistently hitting our churn target? Which months were problematic?"

### Level 3 — Segments: Comparison Charts

Two charts that break performance down by customer type.

**Chart 1: Revenue by Segment (Horizontal Bar Chart)**
- Horizontal bars chosen because segment names are long labels — easier to read than vertical
- Sorted by revenue ascending so highest-value segment is at the top (natural eye path)
- Dollar values labelled directly on bars — no need to read the axis for key values
- Answers: "Which segment drives the most revenue? Where should sales focus?"

**Chart 2: Customer Distribution by Segment (Pie Chart)**
- Paired with the revenue chart to reveal revenue concentration vs customer concentration
- Enterprise has the smallest customer share but highest revenue — strategic insight visible immediately
- Answers: "Are we over-reliant on one segment? Where is growth opportunity?"

### Level 4 — Detail: Filters & Data Table

Progressive disclosure for analysts who need to investigate further.

**Sidebar Filters:**
- Customer Segment (multiselect) — isolate one segment's data
- Region (multiselect) — regional analysis
- Churn Risk (multiselect) — focus on at-risk customers
- Revenue Range (slider) — filter by deal size

**Data Table:**
- Sorted by revenue descending by default — highest value customers visible first
- Revenue column has blue gradient — magnitude visible without reading numbers
- High churn risk rows highlighted red — at-risk customers stand out immediately
- 400px fixed height — scrollable without taking over the page

**Export:**
- CSV download respects all active filters — exported data matches exactly what is displayed
- Answers: "I found a pattern in the filters, now I need to work with this subset offline"

---

## Design Principles Applied

### 1. Progressive Disclosure
Summary KPIs are visible immediately on page load with no scrolling.
Trends require a small scroll — users who need context scroll down.
Segment details require further scrolling — only users investigating drill deeper.
Raw data and filters are in the sidebar — power users know to look there, casual users are not overwhelmed.

### 2. Spatial Organisation
- **Top-left:** Revenue KPI card — the single most-watched metric
- **Top row:** All five KPIs — scanned left to right in order of strategic importance
- **Centre:** Trend charts — equal-width columns, balanced visual weight
- **Bottom:** Segment comparison — supporting context for the trends above
- **Sidebar:** Filters — accessible but out of main reading path

### 3. Consistent Metaphor
| Visual Signal | Meaning | Applied In |
|---|---|---|
| Green | Good / on-target | Revenue target line, churn bars below threshold |
| Red | Bad / needs attention | Churn bars above threshold, current month highlight, high risk rows |
| Blue | Primary metric | Revenue line, active customers, main bars |
| Orange | Comparison / secondary | Mid-Market segment colour |
| Delta arrows ↑↓ | Direction of change | All KPI cards (Streamlit `st.metric` delta) |
| `delta_color='inverse'` | Lower is better | Churn Rate card only |

### 4. Context Over Numbers
Every number on the dashboard has comparison context:

| Number | Context Provided |
|---|---|
| Revenue $5.2M | +/- % vs last month + $5M target line on chart |
| Active Customers 2,500 | +/- absolute change vs last month |
| Churn Rate 3.4% | +/- vs last month + 4.0% target line on chart |
| Bar chart values | Value labels on every bar (no axis-reading needed) |
| Filtered table | Summary metrics recalculate dynamically (count, total revenue, avg, risk %) |

---

## Colour Palette

| Role | Hex | Usage |
|---|---|---|
| Primary | `#1f77b4` | Main metrics, revenue line, Enterprise bars |
| Secondary | `#ff7f0e` | Comparison data, Mid-Market segment |
| Success / Good | `#2ca02c` | Target lines, on-target bars, SMB segment |
| Danger / Bad | `#d62728` | Off-target bars, churn highlights, high-risk rows |
| Neutral | `#7f7f7f` | Grid lines, threshold references |

All colours sourced from matplotlib's default category palette for maximum accessibility
contrast. Green/red usage is consistent — user learns the language once.

---

## Target Audience

| Audience | Usage Pattern | What They Use |
|---|---|---|
| **CEO** | Weekly, 30-second glance | KPI cards only (Level 1) |
| **VP of Sales / Marketing** | Daily, 2-3 minute review | KPIs + trend charts (Level 1 + 2) |
| **Business Analyst** | Deep investigation | Full dashboard including filters and CSV export (all levels) |

The hierarchy serves all three without compromise: the CEO gets their answer in 5 seconds
and never sees the data table; the analyst gets the full drill-down without extra clicks.

---

## Data Sources

| Section | Source Table / View |
|---|---|
| KPI Cards | `monthly_df` — last row vs second-to-last row |
| Revenue Trend | `monthly_df['revenue']` — 12-month aggregated series |
| Customer Trend | `monthly_df['active_customers']`, `monthly_df['churned_customers']` |
| Churn Rate Trend | `monthly_df['churn_rate']` — derived: churned / active × 100 |
| Segment Revenue | `segment_df['revenue']` — aggregated from `detailed_df` |
| Segment Distribution | `segment_df['customer_count']` — count per segment |
| Detail Table | `detailed_df` — 1000 customer records with segment, region, revenue, churn risk |

In production, `monthly_df` maps to a `vw_monthly_metrics` SQL view,
`segment_df` maps to `vw_revenue_by_segment`, and `detailed_df` maps to the
`customers` table joined with transactions.

---

## Files

```
dashboard_app.py          # Main Streamlit application (all 4 levels)
dashboard_design.md       # This document
output/                   # Generated charts (also embedded in dashboard)
queries/                  # SQL queries that power the metrics
scripts/sql_business_metrics.py  # Backend metric computation
```
