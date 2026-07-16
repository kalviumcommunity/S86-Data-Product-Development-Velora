import json
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

INPUT_FILE = "data/raw/customer_correlation.csv"

OUTPUT_IMAGE = "output/correlation_heatmap.png"


def compute_correlations(df):
    """
    Compute Pearson and Spearman correlations.
    """

    pearson = df.corr(numeric_only=True, method="pearson")

    spearman = df.corr(numeric_only=True, method="spearman")

    comparison = pd.DataFrame({
        "pearson": pearson["churn"],
        "spearman": spearman["churn"],
    })

    print("\nCorrelation Comparison")

    print(comparison)

    return pearson, spearman


def create_heatmap(pearson):
    """
    Generate correlation heatmap.
    """

    os.makedirs("output", exist_ok=True)

    plt.figure(figsize=(10, 8))

    sns.heatmap(
        pearson,
        annot=True,
        cmap="coolwarm",
        center=0,
    )

    plt.title("Feature Correlation Matrix")

    plt.tight_layout()

    plt.savefig(OUTPUT_IMAGE)

    plt.close()

    print("\nHeatmap saved.")


def strong_correlations(pearson):
    """
    Display strongest feature pairs.
    """

    corr_flat = pearson.unstack()

    strong = (
        corr_flat[corr_flat.abs() > 0.7]
        .sort_values(ascending=False)
    )

    strong_pairs = strong[strong != 1.0].drop_duplicates()

    print("\nStrong Correlations")

    print(strong_pairs.head(10))

    return strong_pairs


def business_analysis():
    """
    Explain why correlation is not causation.
    """

    analysis = {
        "support_tickets <-> churn": {
            "possible_directions": [
                "Support tickets cause churn",
                "Customers about to churn contact support",
                "Customer frustration causes both"
            ],
            "most_likely":
                "Customer frustration is the underlying cause.",
            "business_action":
                "Improve product quality rather than reducing support."
        }
    }

    print("\nBusiness Interpretation")

    print(json.dumps(analysis, indent=4))

    with open(
        "output/business_interpretation.json",
        "w",
    ) as file:

        json.dump(
            analysis,
            file,
            indent=4,
        )


def feature_selection(df):
    """
    Remove redundant feature.
    """

    selected = df[
        [
            "transactions_per_month",
            "support_tickets",
            "total_spent",
            "churn",
        ]
    ]

    print("\nSelected Features")

    print(selected.corr())

    selected.to_csv(
        "data/processed/selected_features.csv",
        index=False,
    )


if __name__ == "__main__":

    df = pd.read_csv(INPUT_FILE)

    pearson, spearman = compute_correlations(df)

    create_heatmap(pearson)

    strong_correlations(pearson)

    business_analysis()

    feature_selection(df)

    print("\nCorrelation Analysis Completed.")