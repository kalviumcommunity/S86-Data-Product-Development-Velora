"""
export_functions.py
-------------------
BSB 2.50 - Insight Export & Report Generation

Automated export system for analysis outputs:
  - CSV: cleaned datasets for Excel analysis
  - HTML: interactive reports with embedded Plotly charts
  - PDF: executive summary (fallback to text if weasyprint unavailable)
  - Metadata: README with generation info and data dictionary

Tasks covered:
  Task 1: export_analysis() function with all formats
  Task 2: verify_exports() validation function
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
# Helper: Markdown to HTML
# ─────────────────────────────────────────────

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to HTML. Minimal implementation without external deps.
    Handles: headers (##), bold (**text**), lists (- item).
    """
    html = markdown_text
    
    # Headers
    html = html.replace('### ', '<h3>').replace('\n## ', '</h3>\n<h2>').replace('## ', '<h2>')
    html = html.replace('\n# ', '</h2>\n<h1>').replace('# ', '<h1>')
    html += '</h2>' if '##' in markdown_text else ''
    
    # Bold
    import re
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Lists
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    
    html = '\n'.join(result)
    html = html.replace('\n', '<br>\n')
    
    return html


# ═════════════════════════════════════════════
# TASK 1: Export Analysis Function
# ═════════════════════════════════════════════

def export_analysis(df: pd.DataFrame, 
                    summary_text: str, 
                    charts_dict: dict, 
                    output_dir: str = 'output') -> str:
    """
    Export analysis in three formats: CSV, PDF-fallback, HTML.
    
    All outputs are saved to a timestamped subfolder for version tracking.
    Prior reports remain accessible for historical comparison.
    
    Args:
        df: Cleaned DataFrame with analysis results
        summary_text: Executive summary as markdown string
        charts_dict: Dict of {chart_name: matplotlib_figure or plotly_figure}
        output_dir: Base directory to save outputs (default: 'output')
    
    Returns:
        str: Path to the timestamped report directory
    
    Example:
        >>> df = pd.read_sql("SELECT * FROM customers", engine)
        >>> summary = "## Churn Analysis\\nFinding: Support speed impacts retention..."
        >>> charts = {'Revenue Trend': fig1, 'Churn by Segment': fig2}
        >>> report_path = export_analysis(df, summary, charts)
        >>> print(f"Exported to: {report_path}")
    """
    
    # Create timestamped output folder
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    report_dir = os.path.join(output_dir, f"{timestamp}_analysis")
    os.makedirs(report_dir, exist_ok=True)
    
    print(f"\n{'='*70}")
    print(f"EXPORTING ANALYSIS REPORT")
    print(f"{'='*70}")
    print(f"Output directory: {report_dir}\n")
    
    # ── 1. Export Cleaned CSV ──────────────────
    csv_path = os.path.join(report_dir, "cleaned_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"✓ CSV exported: {csv_path}")
    print(f"  Rows: {len(df):,} | Columns: {len(df.columns)}")
    
    # ── 2. Export PDF (or fallback to text) ───
    pdf_path = os.path.join(report_dir, "summary_report.pdf")
    try:
        from weasyprint import HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                strong {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <h1>Analysis Report</h1>
            <p><em>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
            {markdown_to_html(summary_text)}
        </body>
        </html>
        """
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"✓ PDF exported: {pdf_path}")
    except ImportError:
        # Fallback: save as text if weasyprint not installed
        txt_path = os.path.join(report_dir, "summary_report.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write("=" * 70 + "\n\n")
            f.write(summary_text)
        print(f"⚠ PDF library unavailable — exported as text: {txt_path}")
    except Exception as e:
        print(f"✗ PDF export failed: {e}")
    
    # ── 3. Export HTML with Embedded Charts ────
    html_path = os.path.join(report_dir, "interactive_report.html")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analysis Report</title>
        <script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f7fa;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 4px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 30px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 40px;
                margin-bottom: 20px;
                padding-left: 10px;
                border-left: 4px solid #3498db;
            }}
            .summary {{
                background: #ecf0f1;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
                line-height: 1.8;
            }}
            .chart-container {{
                margin: 30px 0;
                padding: 20px;
                background: #fafafa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            .metadata {{
                font-size: 0.9em;
                color: #7f8c8d;
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Analysis Report</h1>
            <p><em>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                {markdown_to_html(summary_text)}
            </div>
    """
    
    # Embed all charts
    for chart_name, fig in charts_dict.items():
        html_content += f"""
        <div class="chart-container">
            <h2>📈 {chart_name}</h2>
        """
        
        # Check if matplotlib or plotly figure
        if hasattr(fig, 'to_html'):  # Plotly figure
            html_content += fig.to_html(include_plotlyjs=False, div_id=chart_name.replace(' ', '_'))
        else:  # Matplotlib figure
            # Save matplotlib fig as PNG and embed as base64
            import io
            import base64
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            html_content += f'<img src="data:image/png;base64,{img_base64}" alt="{chart_name}">'
            buf.close()
        
        html_content += "</div>"
    
    html_content += f"""
            <div class="metadata">
                <strong>Report Metadata:</strong><br>
                Records: {len(df):,} | Columns: {len(df.columns)} | 
                Export Time: {datetime.now().isoformat()}
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ HTML exported: {html_path}")
    
    # ── 4. Create Metadata File ────────────────
    metadata = {
        'Generated': datetime.now().isoformat(),
        'Records': int(len(df)),
        'Columns': list(df.columns),
        'Column_Types': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'Data_Range': f"{df.iloc[0, 0]} to {df.iloc[-1, 0]}" if len(df) > 0 else "N/A",
        'File_Sizes': {}
    }
    
    # Calculate file sizes
    for fname in ['cleaned_data.csv', 'interactive_report.html']:
        fpath = os.path.join(report_dir, fname)
        if os.path.exists(fpath):
            size_bytes = os.path.getsize(fpath)
            metadata['File_Sizes'][fname] = f"{size_bytes:,} bytes ({size_bytes/1024:.1f} KB)"
    
    readme_path = os.path.join(report_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# Analysis Report Metadata\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        f.write("## Dataset Summary\n\n")
        f.write(f"- **Total Records:** {len(df):,}\n")
        f.write(f"- **Total Columns:** {len(df.columns)}\n")
        f.write(f"- **Column Names:** {', '.join(df.columns)}\n\n")
        f.write("## Column Data Types\n\n")
        for col, dtype in df.dtypes.items():
            f.write(f"- `{col}`: {dtype}\n")
        f.write("\n## Files Included\n\n")
        f.write("- `cleaned_data.csv`: Raw dataset for Excel analysis\n")
        f.write("- `summary_report.pdf` (or `.txt`): Executive summary\n")
        f.write("- `interactive_report.html`: Full report with embedded charts\n")
        f.write("- `README.md`: This metadata file\n")
    
    print(f"✓ Metadata created: {readme_path}")
    
    # ── 5. Save Metadata JSON ──────────────────
    json_path = os.path.join(report_dir, "metadata.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata JSON: {json_path}")
    
    print(f"\n{'='*70}")
    print(f"EXPORT COMPLETE")
    print(f"{'='*70}")
    print(f"All files saved to: {report_dir}\n")
    
    return report_dir


# ═════════════════════════════════════════════
# TASK 2: Verify Exports
# ═════════════════════════════════════════════

def verify_exports(report_dir: str) -> bool:
    """
    Verify all export files are present and readable.
    
    Args:
        report_dir: Path to the timestamped report directory
    
    Returns:
        bool: True if all validations pass, False otherwise
    """
    
    print(f"\n{'='*70}")
    print(f"VERIFYING EXPORTS")
    print(f"{'='*70}")
    print(f"Directory: {report_dir}\n")
    
    required_files = ['cleaned_data.csv', 'interactive_report.html', 'README.md', 'metadata.json']
    optional_files = ['summary_report.pdf', 'summary_report.txt']
    
    all_valid = True
    
    # Check required files
    for filename in required_files:
        filepath = os.path.join(report_dir, filename)
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ {filename}: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        else:
            print(f"✗ {filename}: MISSING")
            all_valid = False
    
    # Check optional files (at least one must exist)
    pdf_exists = os.path.exists(os.path.join(report_dir, 'summary_report.pdf'))
    txt_exists = os.path.exists(os.path.join(report_dir, 'summary_report.txt'))
    
    if pdf_exists or txt_exists:
        fname = 'summary_report.pdf' if pdf_exists else 'summary_report.txt'
        fpath = os.path.join(report_dir, fname)
        file_size = os.path.getsize(fpath)
        print(f"✓ {fname}: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    else:
        print(f"✗ summary_report.pdf or .txt: MISSING")
        all_valid = False
    
    print()
    
    # Test CSV is readable
    try:
        csv_path = os.path.join(report_dir, "cleaned_data.csv")
        df_test = pd.read_csv(csv_path)
        print(f"✓ CSV readable: {len(df_test):,} rows × {len(df_test.columns)} columns")
        print(f"  Columns: {', '.join(df_test.columns[:5])}{'...' if len(df_test.columns) > 5 else ''}")
    except Exception as e:
        print(f"✗ CSV read failed: {e}")
        all_valid = False
    
    # Test HTML is readable
    try:
        html_path = os.path.join(report_dir, "interactive_report.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        if len(html_content) > 1000 and '<html' in html_content.lower():
            print(f"✓ HTML readable: {len(html_content):,} characters")
        else:
            print(f"✗ HTML appears corrupted or empty")
            all_valid = False
    except Exception as e:
        print(f"✗ HTML read failed: {e}")
        all_valid = False
    
    # Test metadata JSON
    try:
        json_path = os.path.join(report_dir, "metadata.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"✓ Metadata JSON readable: {len(metadata)} keys")
    except Exception as e:
        print(f"✗ Metadata JSON read failed: {e}")
        all_valid = False
    
    print()
    
    # Show browser path
    html_abs_path = os.path.abspath(os.path.join(report_dir, "interactive_report.html"))
    print(f"Open in browser: file:///{html_abs_path.replace(os.sep, '/')}")
    
    print(f"\n{'='*70}")
    if all_valid:
        print("VERIFICATION PASSED")
    else:
        print("VERIFICATION FAILED - Some files are missing or corrupted")
    print(f"{'='*70}\n")
    
    return all_valid


# ═════════════════════════════════════════════
# Test Export with Sample Data
# ═════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing export system with sample data...\n")
    
    # Generate sample data
    np.random.seed(42)
    sample_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'revenue': np.random.uniform(5000, 15000, 100).round(2),
        'customers': np.random.randint(100, 300, 100),
        'churn_rate': np.random.uniform(3, 8, 100).round(2),
        'segment': np.random.choice(['Enterprise', 'SMB', 'Individual'], 100),
    })
    
    # Sample summary
    summary_md = """
## Key Findings

**Revenue Performance:**
- Average daily revenue: $10,234
- Peak revenue day: 2024-03-15 ($14,892)
- Growth trend: +12% quarter-over-quarter

**Customer Metrics:**
- Active customers averaged 215/day
- Churn rate: 5.2% (within acceptable 6% threshold)
- Enterprise segment shows strongest retention

**Recommendations:**
- Focus retention efforts on SMB segment (highest churn)
- Expand Enterprise offerings (highest revenue per customer)
- Investigate March revenue spike for replication opportunities
    """
    
    # Create sample charts
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(sample_df['date'], sample_df['revenue'], linewidth=2, color='#3498db')
    ax1.set_title('Daily Revenue Trend', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Revenue ($)')
    ax1.grid(alpha=0.3)
    plt.tight_layout()
    
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    segment_revenue = sample_df.groupby('segment')['revenue'].sum()
    ax2.bar(segment_revenue.index, segment_revenue.values, color=['#3498db', '#e74c3c', '#2ecc71'])
    ax2.set_title('Revenue by Segment', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Total Revenue ($)')
    plt.tight_layout()
    
    charts = {
        'Daily Revenue Trend': fig1,
        'Revenue by Customer Segment': fig2,
    }
    
    # Export
    report_path = export_analysis(sample_df, summary_md, charts, 'output')
    
    # Verify
    verify_exports(report_path)
    
    plt.close('all')
