"""
scheduled_export.py
--------------------
BSB 2.50 - Task 4: Scheduled Export

Runs the full analysis export pipeline on a defined schedule.
Supports three modes:
  1. Run once immediately (for testing / manual trigger)
  2. Scheduled loop using the 'schedule' library (daily/weekly runs)
  3. Windows Task Scheduler / cron instructions for production deployment

Usage:
  python scheduled_export.py --run-now          # single immediate run
  python scheduled_export.py --schedule         # start schedule loop
  python scheduled_export.py                    # defaults to run-now
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine

from export_functions import export_analysis, verify_exports

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────

LOG_DIR = "output/logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"export_{datetime.now().strftime('%Y-%m')}.log")
        ),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DB Connection
# ─────────────────────────────────────────────

DB_PATH = "analytics.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


# ─────────────────────────────────────────────
# Analysis Functions
# ─────────────────────────────────────────────

def run_analysis():
    """
    Query all data needed for the weekly report.
    Returns a cleaned DataFrame ready for export.
    """
    log.info("Loading data from database...")
    
    orders = pd.read_sql("SELECT * FROM orders", engine)
    logins = pd.read_sql("SELECT * FROM logins", engine)
    customers = pd.read_sql("SELECT * FROM customers", engine)
    
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    
    # Enrich with customer segment
    enriched = orders.merge(customers, on='customer_id', how='left')
    enriched['month'] = enriched['order_date'].dt.to_period('M').astype(str)
    enriched['week']  = enriched['order_date'].dt.to_period('W').astype(str)
    
    log.info(f"Loaded: {len(enriched):,} orders across {enriched['month'].nunique()} months")
    return enriched


def generate_summary(df: pd.DataFrame) -> str:
    """Build the executive summary text from analysis results."""
    
    today = date.today()
    curr_start = today.replace(day=1)
    prev_start = (curr_start - timedelta(days=1)).replace(day=1)
    
    curr = df[df['order_date'] >= pd.Timestamp(curr_start)]
    prev = df[(df['order_date'] >= pd.Timestamp(prev_start)) &
              (df['order_date'] < pd.Timestamp(curr_start))]
    
    curr_rev = curr['order_amount'].sum()
    prev_rev = prev['order_amount'].sum()
    rev_change = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev else 0
    
    curr_customers = curr['customer_id'].nunique()
    
    summary = f"""
## Weekly Analysis Report

**Report Date:** {datetime.now().strftime('%B %d, %Y')}
**Period:** {curr_start.strftime('%B %Y')} vs {prev_start.strftime('%B %Y')}

### Revenue Performance
- **Current Month Revenue:** ${curr_rev:,.2f}
- **Prior Month Revenue:** ${prev_rev:,.2f}
- **Month-over-Month Change:** {rev_change:+.1f}%

### Customer Activity
- **Active Customers (Current Month):** {curr_customers:,}
- **Total Orders (Current Month):** {len(curr):,}
- **Average Order Value:** ${curr['order_amount'].mean():,.2f}

### Segment Breakdown
{_segment_summary(df)}

### Automated Report
This report was generated automatically by `scheduled_export.py`.
Next scheduled run: {_next_run_time()}
"""
    return summary


def _segment_summary(df: pd.DataFrame) -> str:
    if 'customer_type' not in df.columns:
        return "- Segment data unavailable"
    seg = df.groupby('customer_type')['order_amount'].agg(['sum', 'mean', 'count'])
    lines = []
    for seg_name, row in seg.iterrows():
        lines.append(f"- **{seg_name}:** ${row['sum']:,.0f} revenue, "
                     f"{row['count']:.0f} orders, ${row['mean']:,.0f} AOV")
    return '\n'.join(lines)


def _next_run_time() -> str:
    today = datetime.now()
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    next_fri = today + timedelta(days=days_until_friday)
    return next_fri.strftime('%A, %B %d, %Y at 5:00 PM')


def generate_charts(df: pd.DataFrame) -> dict:
    """Build all charts for the report."""
    
    charts = {}
    monthly = df.groupby('month').agg(
        revenue=('order_amount', 'sum'),
        orders=('order_id', 'count'),
    ).reset_index().sort_values('month').tail(6)
    
    # Revenue trend
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(monthly['month'], monthly['revenue'], marker='o', linewidth=2.5, color='#1f77b4')
    target_line = monthly['revenue'].mean() * 1.05  # 5% above average as target
    ax1.axhline(y=target_line, color='#2ca02c', linestyle='--', linewidth=1.5, label='Target')
    ax1.set_title('Monthly Revenue Trend', fontweight='bold', fontsize=13)
    ax1.set_ylabel('Revenue ($)')
    ax1.tick_params(axis='x', rotation=30)
    ax1.legend()
    ax1.grid(alpha=0.25, linestyle=':')
    plt.tight_layout()
    charts['Monthly Revenue Trend'] = fig1
    
    # Segment revenue bar chart
    if 'customer_type' in df.columns:
        seg_rev = df.groupby('customer_type')['order_amount'].sum().sort_values(ascending=True)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        bars = ax2.barh(seg_rev.index, seg_rev.values,
                        color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        for bar, val in zip(bars, seg_rev.values):
            ax2.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                     f'${val:,.0f}', va='center', fontsize=10)
        ax2.set_title('Revenue by Customer Segment', fontweight='bold', fontsize=13)
        ax2.set_xlabel('Revenue ($)')
        ax2.grid(axis='x', alpha=0.25, linestyle=':')
        plt.tight_layout()
        charts['Revenue by Segment'] = fig2
    
    return charts


# ─────────────────────────────────────────────
# Scheduled Export Job
# ─────────────────────────────────────────────

def scheduled_export():
    """
    Full export job. Called by the scheduler or directly.
    Handles errors gracefully — logs failures without crashing.
    """
    log.info(f"Starting scheduled export job...")
    
    try:
        df = run_analysis()
        summary = generate_summary(df)
        charts = generate_charts(df)
        
        report_dir = export_analysis(df, summary, charts, 'output')
        
        is_valid = verify_exports(report_dir)
        
        if is_valid:
            log.info(f"Export completed successfully: {report_dir}")
        else:
            log.error(f"Export verification failed: {report_dir}")
        
        plt.close('all')
        
        # Update run log
        run_log_path = os.path.join(LOG_DIR, "run_history.json")
        history = []
        if os.path.exists(run_log_path):
            with open(run_log_path, 'r') as f:
                history = json.load(f)
        
        history.append({
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS' if is_valid else 'PARTIAL',
            'output_dir': report_dir,
            'records_exported': len(df),
        })
        
        with open(run_log_path, 'w') as f:
            json.dump(history[-30:], f, indent=2)  # Keep last 30 runs
        
        return report_dir
        
    except Exception as e:
        log.error(f"Export job FAILED: {e}", exc_info=True)
        
        # Log failure
        failure_log = {
            'timestamp': datetime.now().isoformat(),
            'status': 'FAILED',
            'error': str(e),
        }
        failure_path = os.path.join(LOG_DIR, "failures.json")
        failures = []
        if os.path.exists(failure_path):
            with open(failure_path, 'r') as f:
                failures = json.load(f)
        failures.append(failure_log)
        with open(failure_path, 'w') as f:
            json.dump(failures[-10:], f, indent=2)
        
        return None


# ─────────────────────────────────────────────
# Schedule Loop (Task 4)
# ─────────────────────────────────────────────

def start_schedule():
    """
    Start the scheduled export loop.
    
    Schedule: Every Friday at 5:00 PM
    Uses the 'schedule' library. Install with: pip install schedule
    
    For production, prefer Windows Task Scheduler or cron instead:
    
    # Windows Task Scheduler (PowerShell):
    #   Program: python.exe
    #   Arguments: path/to/scheduled_export.py --run-now
    #   Trigger: Weekly, Friday, 5:00 PM
    
    # Linux/Mac cron (crontab -e):
    #   0 17 * * 5 /usr/bin/python3 /path/to/scheduled_export.py --run-now
    """
    try:
        import schedule
        import time
        
        log.info("Starting scheduled export loop...")
        log.info("Schedule: Every Friday at 5:00 PM")
        log.info("Press Ctrl+C to stop")
        
        # Weekly schedule: Friday 5pm
        schedule.every().friday.at("17:00").do(scheduled_export)
        
        # Also run daily at 5pm for daily dashboards
        schedule.every().day.at("05:00").do(scheduled_export)
        
        log.info(f"Next scheduled run: {_next_run_time()}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except ImportError:
        log.warning("'schedule' library not installed. Running once and exiting.")
        log.warning("Install with: pip install schedule")
        scheduled_export()


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scheduled export runner")
    parser.add_argument(
        '--schedule', action='store_true',
        help='Start the schedule loop (runs continuously)'
    )
    parser.add_argument(
        '--run-now', action='store_true',
        help='Run export immediately and exit'
    )
    args = parser.parse_args()
    
    if args.schedule:
        start_schedule()
    else:
        # Default: run once now
        log.info("Running export immediately (--run-now mode)...")
        result = scheduled_export()
        if result:
            log.info(f"Done. Report saved to: {result}")
        else:
            log.error("Export failed. Check output/logs/ for details.")
            sys.exit(1)
