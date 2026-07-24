# Analysis Report — Stakeholder Guide

> This guide explains every file in the export package, who should use it,
> and how to get the most out of each format.

---

## What's Included

Each export produces a timestamped folder (e.g. `2026-07-21_093000_analysis/`)
containing four files:

### `cleaned_data.csv`

| Property | Detail |
|---|---|
| **Purpose** | Raw analysis dataset for self-service exploration in Excel |
| **Typical size** | 200–500 KB depending on date range |
| **Columns** | order_id, customer_id, order_date, order_amount, customer_type, month, week |
| **Use case** | Build your own pivot tables, filters, and charts in Excel or Sheets |
| **Refresh** | Generated fresh at each export run |

**How to use in Excel:**
1. Open Excel → Data → From Text/CSV
2. Select `cleaned_data.csv`
3. Use PivotTable to slice by `customer_type` or `month`

---

### `summary_report.pdf` (or `summary_report.txt`)

| Property | Detail |
|---|---|
| **Purpose** | Executive summary — key metrics and findings in portable format |
| **Format** | PDF (plain text fallback if weasyprint unavailable) |
| **Length** | 1–2 pages |
| **Content** | Revenue vs target, customer counts, segment breakdown, observations |
| **Use case** | Email to leadership, embed in PowerPoint, print for meetings |

**Note:** If your machine doesn't have `weasyprint` installed, the summary is
exported as a `.txt` file with identical content. Install PDF support with:
```
pip install weasyprint
```

---

### `interactive_report.html`

| Property | Detail |
|---|---|
| **Purpose** | Full analysis with embedded charts — explore in any browser |
| **Format** | Single self-contained HTML file |
| **Charts** | Revenue trend, segment revenue bar chart, KPI overview |
| **Use case** | Email to any stakeholder — opens in browser, no Python needed |
| **Sharing** | Attach to email as a file, or host on SharePoint/intranet |

**How to open:**
- Double-click the `.html` file — opens in your default browser
- Or drag and drop into any browser window

**Tip:** All charts are static images (matplotlib), so they render everywhere
including mobile browsers.

---

### `README.md`

| Property | Detail |
|---|---|
| **Purpose** | Metadata about this specific export run |
| **Content** | Generation timestamp, record count, column list, data types, file sizes |
| **Use case** | Auditing — know exactly when this dataset was generated and what it contains |

---

### `metadata.json`

| Property | Detail |
|---|---|
| **Purpose** | Machine-readable version of the README metadata |
| **Use case** | Automated systems that need to read report provenance |

---

## How to Use Each File by Role

| Role | Recommended Files | Typical Action |
|---|---|---|
| **Executive / VP** | `summary_report.pdf` | Read key metrics, share with team |
| **Business Analyst** | `cleaned_data.csv` + `interactive_report.html` | Build pivot tables, explore trends |
| **Data Engineer** | `metadata.json` | Verify data lineage and row counts |
| **Marketing** | `interactive_report.html` | View segment charts, identify opportunities |
| **Operations** | `cleaned_data.csv` | Filter by region or customer type for operations review |

---

## When Are These Files Updated?

| Schedule | Trigger |
|---|---|
| **Daily at 5:00 AM** | Automated — `scheduled_export.py` runs via Task Scheduler |
| **Friday at 5:00 PM** | Weekly summary with full month context |
| **On demand** | Click "🚀 Export Analysis Now" button in the dashboard |

Each run creates a new timestamped folder. Previous reports are never overwritten.

---

## How Auto-Update Works (Technical)

When new data is added to the `orders`, `logins`, or `customers` tables in
`analytics.db`, the next export run automatically picks it up. No code changes needed.

```
New data arrives in DB
        ↓
scheduled_export.py runs (cron / Task Scheduler)
        ↓
run_analysis() queries latest data
        ↓
generate_summary() + generate_charts() build outputs
        ↓
export_analysis() saves CSV, HTML, PDF, metadata
        ↓
verify_exports() confirms all files are valid
        ↓
Outputs available in output/<timestamp>_analysis/
```

Date ranges in all queries use `date.today()` — never hardcoded strings.
A new month's data automatically appears in the next report without any
developer intervention.

---

## Error Handling

If an export job fails:

1. The error is logged to `output/logs/export_YYYY-MM.log`
2. The failure is recorded in `output/logs/failures.json`
3. The previous report remains available — stakeholders are not left without data
4. The next scheduled run retries automatically

**To check recent run history:**
```
output/logs/run_history.json   # last 30 successful runs
output/logs/failures.json      # last 10 failures with error detail
```

---

## Files Reference

```
export_functions.py              # Core: export_analysis() + verify_exports()
streamlit_export_integration.py  # Dashboard with export button + download buttons
scheduled_export.py              # Scheduler: run daily/weekly automatically
export_documentation.md          # This file
output/
  <timestamp>_analysis/
    cleaned_data.csv
    summary_report.pdf (.txt fallback)
    interactive_report.html
    README.md
    metadata.json
  logs/
    export_YYYY-MM.log
    run_history.json
    failures.json
```

---

## Frequently Asked Questions

**Q: Can I share the HTML report with someone who doesn't have Python?**
Yes. The HTML file is self-contained. Open it in any browser — no Python,
no dashboard access, no dependencies needed.

**Q: How do I get a fresh report right now?**
Open the dashboard and click **"🚀 Export Analysis Now"** in the sidebar,
or run `python scheduled_export.py --run-now` in the terminal.

**Q: Where are older reports?**
In `output/` — each run creates a new folder with a timestamp prefix.
They are never deleted automatically.

**Q: The PDF shows as a `.txt` file — what happened?**
The `weasyprint` PDF library is not installed. The content is identical,
just in text format. Install `weasyprint` for proper PDF output.

**Q: Can I change the schedule?**
Edit `scheduled_export.py`. Change the `schedule.every().friday.at("17:00")`
line to your preferred schedule, or update the Windows Task Scheduler trigger.
