import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze revenue distribution and segment behavior"
    )
    parser.add_argument(
        "--input",
        default="data/raw/revenue_data.csv",
        help="Path to revenue dataset (default: data/raw/revenue_data.csv)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save generated artifacts (default: output)",
    )
    parser.add_argument(
        "--column",
        default="revenue",
        help="Numeric column to analyze (default: revenue)",
    )
    return parser.parse_args()


def resolve_repo_root():
    return Path(__file__).resolve().parents[1]


def load_data(input_path, revenue_col):
    df = pd.read_csv(input_path)
    if revenue_col not in df.columns:
        raise ValueError(f"Column '{revenue_col}' not found in {input_path}")

    df = df.copy()
    df[revenue_col] = pd.to_numeric(df[revenue_col], errors="coerce")
    df = df.dropna(subset=[revenue_col])

    if df.empty:
        raise ValueError("No valid numeric rows found for analysis")
    return df


def plot_distribution(df, revenue_col, output_dir):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(df[revenue_col], bins=50, edgecolor="black")
    axes[0].set_title("Revenue Distribution (Histogram)")
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Count")

    df[revenue_col].plot(kind="density", ax=axes[1])
    axes[1].set_title("Revenue Distribution (KDE)")
    axes[1].set_xlabel("Revenue")

    fig.tight_layout()
    distribution_plot_path = output_dir / "revenue_distribution.png"
    fig.savefig(distribution_plot_path)
    plt.close(fig)

    return distribution_plot_path


def compute_shape_metrics(df, revenue_col):
    values = df[revenue_col]
    skewness = float(stats.skew(values, bias=False))
    # Use Pearson kurtosis so values > 3 represent heavier tails than normal.
    kurtosis = float(stats.kurtosis(values, fisher=False, bias=False))
    return skewness, kurtosis


def abnormal_pattern_summary(df, revenue_col):
    describe = df[revenue_col].describe().to_dict()
    percentiles = (
        df[revenue_col]
        .quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
        .to_dict()
    )

    gap_75_90 = float(percentiles[0.9] - percentiles[0.75])
    iqr = float(percentiles[0.75] - percentiles[0.25])
    gap_ratio_vs_iqr = float(gap_75_90 / iqr) if iqr else np.nan

    hidden_segment_flag = bool(gap_ratio_vs_iqr > 1.0)

    return {
        "describe": {k: float(v) for k, v in describe.items()},
        "percentiles": {str(k): float(v) for k, v in percentiles.items()},
        "gap_75_to_90": gap_75_90,
        "iqr": iqr,
        "gap_ratio_vs_iqr": gap_ratio_vs_iqr,
        "hidden_segment_flag": hidden_segment_flag,
        "hidden_segment_note": (
            "Large jump from 75th to 90th percentile suggests a distinct high-value segment"
            if hidden_segment_flag
            else "No strong separation signal between upper-middle and top customers"
        ),
    }


def compare_segments(df, revenue_col, output_dir):
    q1 = float(df[revenue_col].quantile(0.25))
    q3 = float(df[revenue_col].quantile(0.75))

    high_value = df[df[revenue_col] > q3]
    low_value = df[df[revenue_col] < q1]

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    ax.hist(high_value[revenue_col], bins=30, alpha=0.7, label="High-Value")
    ax.hist(low_value[revenue_col], bins=30, alpha=0.7, label="Low-Value")
    ax.legend()
    ax.set_title("Revenue: High vs Low Value Customers")
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Count")

    fig.tight_layout()
    segment_plot_path = output_dir / "revenue_segment_distribution.png"
    fig.savefig(segment_plot_path)
    plt.close(fig)

    high_metrics = {
        "count": int(len(high_value)),
        "mean": float(high_value[revenue_col].mean()) if len(high_value) else np.nan,
        "median": float(high_value[revenue_col].median()) if len(high_value) else np.nan,
    }
    low_metrics = {
        "count": int(len(low_value)),
        "mean": float(low_value[revenue_col].mean()) if len(low_value) else np.nan,
        "median": float(low_value[revenue_col].median()) if len(low_value) else np.nan,
    }

    return {
        "q1_threshold": q1,
        "q3_threshold": q3,
        "high_value_metrics": high_metrics,
        "low_value_metrics": low_metrics,
        "segment_plot": str(segment_plot_path),
    }


def build_business_interpretation(df, revenue_col, skewness, kurtosis):
    right_skewed = skewness > 1
    heavy_tails = kurtosis > 3

    interpretation = f"""
Revenue Distribution Analysis:

Skewness: {skewness:.2f} -> {'Highly right-skewed' if right_skewed else 'Moderate/low skew'}
Mean: ${df[revenue_col].mean():.0f}
Median: ${df[revenue_col].median():.0f}
Interpretation: {'Most customers are small/mid-value; a few very large accounts pull the average up' if right_skewed else 'Revenue is more balanced around the center'}

Kurtosis (Pearson): {kurtosis:.2f} -> {'Fat tails (outliers likely)' if heavy_tails else 'Tail weight close to normal'}
Max: ${df[revenue_col].max():.0f}
Top 1%: ${df[revenue_col].quantile(0.99):.0f}

Business Action: {'Use separate playbooks for SMB vs enterprise/key accounts; track median and segment KPIs, not just mean' if right_skewed else 'A more uniform strategy may be sufficient'}
""".strip()

    return interpretation


def main():
    args = parse_args()
    repo_root = resolve_repo_root()

    input_path = repo_root / args.input
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(input_path, args.column)

    distribution_plot_path = plot_distribution(df, args.column, output_dir)
    skewness, kurtosis = compute_shape_metrics(df, args.column)
    abnormal_summary = abnormal_pattern_summary(df, args.column)
    segment_summary = compare_segments(df, args.column, output_dir)
    interpretation = build_business_interpretation(
        df, args.column, skewness, kurtosis
    )

    # Persist all numeric and narrative outputs for PR evidence.
    result = {
        "dataset": str(input_path),
        "row_count": int(len(df)),
        "column": args.column,
        "mean": float(df[args.column].mean()),
        "median": float(df[args.column].median()),
        "skewness": skewness,
        "kurtosis_pearson": kurtosis,
        "distribution_plot": str(distribution_plot_path),
        "abnormal_patterns": abnormal_summary,
        "segment_comparison": segment_summary,
        "business_interpretation": interpretation,
    }

    json_path = output_dir / "revenue_analysis_summary.json"
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)

    txt_path = output_dir / "revenue_business_interpretation.txt"
    txt_path.write_text(interpretation + "\n", encoding="utf-8")

    print(f"Skewness: {skewness:.2f}")
    print(f"Kurtosis (Pearson): {kurtosis:.2f}")
    if abs(skewness) > 1:
        print("Highly skewed - use median not mean")
    if kurtosis > 3:
        print("Heavy tails - expect outliers")

    print("\nPercentiles:")
    for k, v in abnormal_summary["percentiles"].items():
        print(f"  p{k}: {v:.2f}")

    high_m = segment_summary["high_value_metrics"]
    low_m = segment_summary["low_value_metrics"]
    print(
        f"\nHigh-value: mean={high_m['mean']:.0f}, median={high_m['median']:.0f}"
    )
    print(
        f"Low-value: mean={low_m['mean']:.0f}, median={low_m['median']:.0f}"
    )

    print("\n" + interpretation)
    print(f"\nSaved: {distribution_plot_path}")
    print(f"Saved: {segment_summary['segment_plot']}")
    print(f"Saved: {json_path}")
    print(f"Saved: {txt_path}")


if __name__ == "__main__":
    main()