import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

INPUT_FILE = "data/raw/daily_revenue.csv"

OUTPUT_LOG = "output/anomalies_log.csv"
OUTPUT_IMAGE = "output/anomaly_detection.png"


def threshold_detection(df):
    """Business rule alerts."""

    rules = {
        "daily_revenue": {"min": 5000, "max": 50000},
        "transaction_count": {"min": 100, "max": 10000},
        "signup_rate": {"min": 10, "max": 500},
    }

    today = {
        "daily_revenue": df.iloc[-1]["amount"],
        "transaction_count": df.iloc[-1]["transaction_count"],
        "signup_rate": df.iloc[-1]["signup_rate"],
    }

    alerts = []

    for metric, rule in rules.items():

        value = today[metric]

        if value < rule["min"]:

            alerts.append({
                "metric": metric,
                "value": value,
                "threshold": rule["min"],
                "direction": "BELOW_MIN",
                "severity": "HIGH",
            })

        elif value > rule["max"]:

            alerts.append({
                "metric": metric,
                "value": value,
                "threshold": rule["max"],
                "direction": "ABOVE_MAX",
                "severity": "MEDIUM",
            })

    print("\nThreshold Alerts")

    for alert in alerts:
        print(alert)

    return alerts


def detect_zscore(series, threshold=2):

    mean = series.mean()

    std = series.std()

    z = abs((series - mean) / std)

    anomalies = series[z > threshold]

    return anomalies, z, mean, std


def classify(value, mean, std):

    z = abs((value - mean) / std)

    if z > 3:
        return "CRITICAL"

    elif z > 2:
        return "HIGH"

    elif z > 1.5:
        return "MEDIUM"

    return "LOW"


def create_log(anomalies, z_scores, mean, std):

    records = []

    for date, value in anomalies.items():

        records.append({
            "timestamp": pd.Timestamp.now(),
            "anomaly_date": date,
            "metric": "daily_revenue",
            "value": value,
            "expected_range":
                f"{mean-2*std:.0f} - {mean+2*std:.0f}",
            "z_score": round(z_scores.loc[date], 2),
            "severity": classify(value, mean, std),
            "status": "OPEN",
        })

    os.makedirs("output", exist_ok=True)

    pd.DataFrame(records).to_csv(
        OUTPUT_LOG,
        index=False,
    )

    return pd.DataFrame(records)


def plot(df, anomalies, mean, std):

    plt.figure(figsize=(14,6))

    plt.plot(
        df["date"],
        df["amount"],
        marker="o",
        linewidth=2,
        label="Revenue",
    )

    rolling = df["amount"].rolling(7).mean()

    plt.plot(
        df["date"],
        rolling,
        linewidth=2,
        label="7-day MA",
    )

    for date, value in anomalies.items():

        plt.scatter(
            date,
            value,
            color="red",
            s=200,
            marker="X",
        )

        plt.text(
            date,
            value,
            "ANOMALY",
            ha="center",
        )

    plt.fill_between(
        df["date"],
        mean - 2 * std,
        mean + 2 * std,
        alpha=0.2,
        label="Expected Range",
    )

    plt.xticks(rotation=45)

    plt.title("Daily Revenue Anomaly Detection")

    plt.xlabel("Date")

    plt.ylabel("Revenue")

    plt.legend()

    plt.tight_layout()

    plt.savefig(OUTPUT_IMAGE)

    plt.close()


if __name__ == "__main__":

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])

    threshold_detection(df)

    revenue = df.set_index("date")["amount"].tail(30)

    anomalies, z, mean, std = detect_zscore(revenue)

    print(f"\nDetected {len(anomalies)} anomaly(s)\n")

    for date, value in anomalies.items():
        print(
            f"{date.date()} : "
            f"${value:.0f} "
            f"(z={z.loc[date]:.2f})"
        )

    log = create_log(
        anomalies,
        z,
        mean,
        std,
    )

    print("\nSeverity Classification")

    print(log)

    critical = log[
        log["severity"].isin(
            ["HIGH", "CRITICAL"]
        )
    ]

    print(
        f"\nCritical Alerts: {len(critical)}"
    )

    plot(
        df,
        anomalies,
        mean,
        std,
    )

    print("\nAnomaly Detection Completed.")