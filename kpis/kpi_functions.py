"""Reusable KPI calculations for the Velora project."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


DEFAULT_SUCCESS_STATUSES = {"success", "successful", "paid", "completed", "approved", "settled"}


def _resolve_column(df: pd.DataFrame, candidates: Iterable[str], *, required: bool = True) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    if required:
        raise KeyError(f"None of the expected columns were found: {', '.join(candidates)}")
    return None


def _coerce_datetime(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Missing required datetime column: {column}")
    return pd.to_datetime(df[column], errors="coerce")


def _coerce_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Missing required numeric column: {column}")
    return pd.to_numeric(df[column], errors="coerce")


def _format_currency(value: float) -> str:
    return f"${value:,.2f}"


def _format_percentage(value: float) -> str:
    return f"{value:.1%}"


def calculate_mau(df: pd.DataFrame, days: int = 30, formatted: bool = False) -> int | str:
    """Monthly Active Users: distinct customers active in the last N days."""
    transaction_date = _coerce_datetime(df, "transaction_date")
    customer_column = _resolve_column(df, ["customer_id"])
    cutoff = pd.Timestamp.now(tz=None) - pd.Timedelta(days=days)
    active_customers = df.loc[transaction_date >= cutoff, customer_column].dropna().nunique()
    return str(active_customers) if formatted else int(active_customers)


def calculate_revenue_per_customer(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Average revenue generated per unique customer."""
    amount_column = _resolve_column(df, ["amount", "revenue", "transaction_amount"])
    customer_column = _resolve_column(df, ["customer_id"])
    total_revenue = _coerce_numeric(df, amount_column).fillna(0).sum()
    unique_customers = df[customer_column].dropna().nunique()
    revenue_per_customer = total_revenue / unique_customers if unique_customers > 0 else 0.0
    return _format_currency(revenue_per_customer) if formatted else float(revenue_per_customer)


def calculate_churn_rate(df: pd.DataFrame, period_days: int = 30, formatted: bool = False) -> float | str:
    """Customers active in the prior period but not in the current period."""
    transaction_date = _coerce_datetime(df, "transaction_date")
    customer_column = _resolve_column(df, ["customer_id"])
    now = pd.Timestamp.now(tz=None)
    current_start = now - pd.Timedelta(days=period_days)
    previous_start = current_start - pd.Timedelta(days=period_days)

    active_previous = df.loc[
        (transaction_date >= previous_start) & (transaction_date < current_start), customer_column
    ].dropna().unique()
    active_current = df.loc[
        (transaction_date >= current_start) & (transaction_date <= now), customer_column
    ].dropna().unique()

    if len(active_previous) == 0:
        return "0.0%" if formatted else 0.0

    churned_customers = sum(customer not in active_current for customer in active_previous)
    churn_rate = churned_customers / len(active_previous)
    return _format_percentage(churn_rate) if formatted else float(churn_rate)


def calculate_payment_success_rate(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Successful payments divided by all payment attempts."""
    if "payment_success" in df.columns:
        success_ratio = pd.to_numeric(df["payment_success"], errors="coerce").fillna(0).mean()
    else:
        status_column = _resolve_column(df, ["status", "payment_status", "transaction_status"])
        status = df[status_column].astype(str).str.strip().str.lower()
        success_ratio = status.isin(DEFAULT_SUCCESS_STATUSES).mean()
    return _format_percentage(float(success_ratio)) if formatted else float(success_ratio)


def calculate_customer_acquisition_cost(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Total acquisition spend divided by newly acquired customers."""
    spend_column = _resolve_column(df, ["marketing_spend", "acquisition_cost", "cac_spend"])
    acquisition_column = _resolve_column(df, ["is_new_customer", "new_customer", "acquired_customer"], required=False)
    spend = _coerce_numeric(df, spend_column).fillna(0).sum()

    if acquisition_column is not None:
        acquired_customers = pd.to_numeric(df[acquisition_column], errors="coerce").fillna(0).astype(bool).sum()
    else:
        customer_column = _resolve_column(df, ["customer_id"])
        acquired_customers = df[customer_column].dropna().nunique()

    cac = spend / acquired_customers if acquired_customers > 0 else 0.0
    return _format_currency(cac) if formatted else float(cac)


def calculate_average_order_value(df: pd.DataFrame, formatted: bool = False) -> float | str:
    """Average order value across all transactions."""
    amount_column = _resolve_column(df, ["amount", "revenue", "transaction_amount"])
    amounts = _coerce_numeric(df, amount_column).fillna(0)
    average_order_value = amounts.sum() / len(amounts) if len(amounts) > 0 else 0.0
    return _format_currency(average_order_value) if formatted else float(average_order_value)


def calculate_retention_rate(df: pd.DataFrame, period_days: int = 30, formatted: bool = False) -> float | str:
    """Customers active in both the previous and current period."""
    churn_rate = calculate_churn_rate(df, period_days=period_days, formatted=False)
    retention_rate = 1.0 - float(churn_rate)
    return _format_percentage(retention_rate) if formatted else float(retention_rate)


def validate_kpis(current_kpis: dict[str, float], targets: dict[str, dict[str, float]]) -> pd.DataFrame:
    """Compare current KPI values against target ranges."""
    validation_rows = []
    for kpi_name, target_range in targets.items():
        actual = current_kpis.get(kpi_name)
        min_val = target_range["min"]
        max_val = target_range["max"]
        status = "PASS" if actual is not None and min_val <= actual <= max_val else "ALERT"
        validation_rows.append(
            {
                "kpi": kpi_name,
                "actual": actual,
                "target_min": min_val,
                "target_max": max_val,
                "status": status,
            }
        )

    return pd.DataFrame(validation_rows)


def revenue_decomposition(df: pd.DataFrame) -> dict[str, pd.Series | float]:
    """Break total revenue into segment and product components."""
    amount_column = _resolve_column(df, ["amount", "revenue", "transaction_amount"])
    total_revenue = _coerce_numeric(df, amount_column).fillna(0).sum()

    segment_column = _resolve_column(df, ["customer_type", "customer_segment"], required=False)
    product_column = _resolve_column(df, ["product", "product_category", "category"], required=False)

    revenue_by_segment = (
        df.groupby(segment_column)[amount_column].sum() if segment_column else pd.Series(dtype=float)
    )
    revenue_by_product = (
        df.groupby(product_column)[amount_column].sum() if product_column else pd.Series(dtype=float)
    )

    return {
        "total_revenue": float(total_revenue),
        "revenue_by_segment": revenue_by_segment,
        "revenue_by_product": revenue_by_product,
    }


if __name__ == "__main__":
    sample_df = pd.DataFrame(
        {
            "customer_id": [1, 2, 1, 3],
            "transaction_date": pd.to_datetime(["2026-06-10", "2026-06-12", "2026-07-02", "2026-07-10"]),
            "amount": [100, 200, 150, 250],
            "status": ["paid", "failed", "paid", "paid"],
        }
    )
    print("MAU:", calculate_mau(sample_df))
    print("Revenue per Customer:", calculate_revenue_per_customer(sample_df, formatted=True))
    print("Churn Rate:", calculate_churn_rate(sample_df, formatted=True))