import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = "data/raw/customer_segments.csv"

OUTPUT_TABLE = "output/segment_summary.csv"
OUTPUT_HEATMAP = "output/segment_heatmap.png"
OUTPUT_INSIGHTS = "output/business_summary.txt"


def compute_metrics(df):
    """
    Compute average metrics for each customer segment.
    """

    segment_metrics = df.groupby("customer_type").agg({
        "lifetime_value": "mean",
        "churn": "mean",
        "support_tickets": "mean",
        "retention_days": "mean",
        "customer_id": "count"
    })

    segment_metrics.columns = [
        "avg_ltv",
        "churn_rate",
        "avg_tickets",
        "avg_retention",
        "count"
    ]

    return segment_metrics


def ranking_table(segment_metrics):
    """
    Rank segments.
    """

    summary = segment_metrics.copy()

    summary["ltv_rank"] = summary["avg_ltv"].rank(ascending=False)

    summary["churn_rank"] = summary["churn_rate"].rank(ascending=True)

    print(summary)

    return summary


def create_heatmap(segment_metrics):
    """
    Generate heatmap.
    """

    plt.figure(figsize=(8,6))

    sns.heatmap(
        segment_metrics[
            [
                "avg_ltv",
                "churn_rate",
                "avg_tickets"
            ]
        ],
        annot=True,
        cmap="RdYlGn"
    )

    plt.title("Segment Comparison Heatmap")

    plt.tight_layout()

    os.makedirs("output", exist_ok=True)

    plt.savefig(OUTPUT_HEATMAP)

    plt.close()


def top_bottom(segment_metrics):
    """
    Find best and worst segments.
    """

    top = segment_metrics["avg_ltv"].idxmax()

    high_churn = segment_metrics["churn_rate"].idxmax()

    best_retention = segment_metrics["avg_retention"].idxmax()

    print("\nSEGMENT PERFORMANCE")

    print(f"Highest Value : {top}")

    print(f"Highest Churn : {high_churn}")

    print(f"Best Retention : {best_retention}")


def business_summary():
    """
    Save business recommendations.
    """

    summary = """
SEGMENT STRATEGY SUMMARY

Enterprise
- Highest lifetime value
- Lowest churn
- Maintain premium support

SMB
- Medium value
- Higher churn
- Improve onboarding and customer support

Startup
- Lowest value
- Moderate churn
- Focus on education and self-service resources
"""

    with open(OUTPUT_INSIGHTS, "w") as f:
        f.write(summary)

    print(summary)


if __name__ == "__main__":

    df = pd.read_csv(INPUT_FILE)

    metrics = compute_metrics(df)

    summary = ranking_table(metrics)

    os.makedirs("output", exist_ok=True)

    summary.to_csv(OUTPUT_TABLE)

    create_heatmap(metrics)

    top_bottom(metrics)

    business_summary()

    print("\nUser Segmentation Completed Successfully.")