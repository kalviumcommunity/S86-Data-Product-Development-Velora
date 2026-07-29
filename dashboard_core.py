import hashlib
import io
import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dynamic KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _normalize_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _default_index(options: list[str], preferred: str | None) -> int:
    if preferred and preferred in options:
        return options.index(preferred)
    return 0


def _guess_column(columns: list[str], keywords: list[str]) -> str | None:
    for column in columns:
        normalized = _normalize_name(column)
        if any(keyword in normalized for keyword in keywords):
            return column
    return None


def _coerce_numeric(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r"[,$%]", "", regex=True)
    cleaned = cleaned.str.replace(r"[^0-9eE\-\.]+", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _coerce_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=False)


@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    suffix = file_name.lower().rsplit(".", 1)[-1]

    if suffix == "csv":
        return pd.read_csv(io.BytesIO(file_bytes))

    if suffix == "json":
        try:
            return pd.read_json(io.BytesIO(file_bytes))
        except ValueError:
            text = file_bytes.decode("utf-8", errors="ignore")
            return pd.read_json(io.StringIO(text), lines=True)

    raise ValueError(f"Unsupported file type: {suffix}")


def _format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def _safe_metric_mean(series: pd.Series) -> float:
    valid = series.dropna()
    if valid.empty:
        return 0.0
    return float(valid.mean())


def _safe_null_percentage(df: pd.DataFrame) -> float:
    total_cells = max(df.shape[0] * df.shape[1], 1)
    return float(df.isnull().sum().sum() / total_cells * 100)


def _filter_categorical(df: pd.DataFrame, column: str, key: str) -> pd.DataFrame:
    values = df[column].dropna().astype(str)
    options = sorted(values.unique().tolist())

    if len(options) <= 1 or len(options) > 50:
        return df

    selected = st.sidebar.multiselect(
        f"{column} values",
        options=options,
        default=options,
        key=key,
    )

    if len(selected) == len(options):
        return df

    return df[df[column].astype(str).isin(selected)]


def main() -> None:
    st.title("Operational KPI Dashboard")
    st.write(
        "Upload a CSV or JSON dataset, map the core columns, and explore KPIs that update with every filter change."
    )

    uploaded_file = st.file_uploader("Upload CSV or JSON", type=["csv", "json"])

    if uploaded_file is None:
        st.info("Upload a CSV or JSON file to begin.")
        st.stop()

    file_bytes = uploaded_file.getvalue()
    file_signature = hashlib.sha256(file_bytes).hexdigest()[:12]

    try:
        df = load_data(file_bytes, uploaded_file.name).copy()
    except Exception as exc:
        st.error(f"Could not read {uploaded_file.name}: {exc}")
        st.stop()

    if df.empty:
        st.warning("Uploaded file is empty.")
        st.stop()

    df.columns = [str(column).strip() for column in df.columns]

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    all_columns = df.columns.tolist()
    date_like_columns = [
        column for column in all_columns if any(token in _normalize_name(column) for token in ["date", "time", "timestamp"])
    ]
    categorical_columns = [
        column for column in all_columns if column not in numeric_columns and df[column].nunique(dropna=True) > 1
    ]

    suggested_measure = _guess_column(
        numeric_columns,
        ["revenue", "sales", "amount", "value", "price", "order"],
    ) or (numeric_columns[0] if numeric_columns else None)
    suggested_customer = _guess_column(
        all_columns,
        ["customer", "client", "account", "user", "buyer", "customerid", "userid"],
    ) or (all_columns[0] if all_columns else None)
    suggested_date = _guess_column(all_columns, ["date", "time", "timestamp", "created", "ordered"]) or (
        date_like_columns[0] if date_like_columns else None
    )
    suggested_segment = _guess_column(all_columns, ["segment", "category", "region", "channel", "group", "tier"])

    widget_prefix = f"{file_signature}_dashboard"

    with st.sidebar:
        st.header("Column Mapping")

        if numeric_columns:
            measure_column = st.selectbox(
                "Metric / revenue column",
                options=numeric_columns,
                index=_default_index(numeric_columns, suggested_measure),
                key=f"{widget_prefix}_measure_column",
            )
        else:
            st.error("No numeric column was detected for KPI calculations.")
            st.stop()

        customer_column = st.selectbox(
            "Customer / ID column",
            options=all_columns,
            index=_default_index(all_columns, suggested_customer),
            key=f"{widget_prefix}_customer_column",
        )

        date_options = ["<none>"] + all_columns
        selected_date_column = st.selectbox(
            "Date column",
            options=date_options,
            index=_default_index(date_options, suggested_date if suggested_date in date_options else None),
            key=f"{widget_prefix}_date_column",
        )

        segment_options = ["<none>"] + all_columns
        selected_segment_column = st.selectbox(
            "Segment / comparison column",
            options=segment_options,
            index=_default_index(segment_options, suggested_segment if suggested_segment in segment_options else None),
            key=f"{widget_prefix}_segment_column",
        )

        st.divider()
        st.header("Filters")

        filtered_df = df.copy()

        filtered_df[measure_column] = _coerce_numeric(filtered_df[measure_column])
        filtered_df = filtered_df[filtered_df[measure_column].notna()]

        if filtered_df.empty:
            st.warning("The selected metric column does not contain usable numeric values.")
            st.stop()

        if selected_date_column != "<none>":
            filtered_df[selected_date_column] = _coerce_datetime(filtered_df[selected_date_column])
            valid_dates = filtered_df[selected_date_column].dropna()

            if not valid_dates.empty:
                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()

                selected_dates = st.date_input(
                    f"{selected_date_column} range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key=f"{widget_prefix}_date_range",
                )

                if isinstance(selected_dates, tuple):
                    start_date, end_date = selected_dates
                else:
                    start_date = end_date = selected_dates

                filtered_df = filtered_df[
                    filtered_df[selected_date_column].dt.date.between(start_date, end_date)
                ]

        if measure_column in filtered_df.columns:
            metric_min = float(filtered_df[measure_column].min())
            metric_max = float(filtered_df[measure_column].max())

            if metric_min != metric_max:
                selected_metric_range = st.slider(
                    f"{measure_column} range",
                    min_value=metric_min,
                    max_value=metric_max,
                    value=(metric_min, metric_max),
                    key=f"{widget_prefix}_metric_range",
                )
                filtered_df = filtered_df[
                    filtered_df[measure_column].between(selected_metric_range[0], selected_metric_range[1])
                ]

        filter_candidates = [
            column
            for column in categorical_columns
            if column not in {customer_column, selected_date_column, selected_segment_column, measure_column}
        ]

        if selected_segment_column != "<none>" and selected_segment_column not in filter_candidates:
            filter_candidates.insert(0, selected_segment_column)

        for column in filter_candidates[:3]:
            filtered_df = _filter_categorical(
                filtered_df,
                column,
                key=f"{widget_prefix}_filter_{_normalize_name(column)}",
            )

    if filtered_df.empty:
        st.warning("No data matches current filters. Broaden your selection.")
        st.stop()

    measure_series = filtered_df[measure_column]
    total_revenue = float(measure_series.sum(skipna=True))
    avg_order = _safe_metric_mean(measure_series)
    row_count = len(filtered_df)
    unique_customers = int(filtered_df[customer_column].nunique(dropna=True))
    null_pct = _safe_null_percentage(filtered_df)

    st.success(
        f"Loaded {uploaded_file.name} with {len(df):,} rows and {len(df.columns):,} columns. "
        f"Filtered view: {row_count:,} rows."
    )

    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Revenue", f"${total_revenue:,.0f}")
    with col2:
        st.metric("Avg Order", f"${avg_order:,.0f}")
    with col3:
        st.metric("Records", f"{row_count:,}")
    with col4:
        st.metric("Customers", f"{unique_customers:,}")
    with col5:
        st.metric("Quality", f"{100 - null_pct:.1f}%")

    st.divider()

    st.subheader("Revenue Over Time")
    if selected_date_column != "<none>" and filtered_df[selected_date_column].notna().any():
        trend_df = (
            filtered_df.dropna(subset=[selected_date_column])
            .assign(_date=filtered_df[selected_date_column].dt.floor("D"))
            .groupby("_date", as_index=False)[measure_column]
            .sum()
            .sort_values("_date")
        )
        st.line_chart(trend_df.set_index("_date")[measure_column])
    else:
        trend_df = filtered_df.reset_index(drop=True).reset_index(names="record_order")
        st.info("No valid date column was selected, so the trend chart uses record order.")
        st.line_chart(trend_df.set_index("record_order")[measure_column])

    st.subheader("Revenue by Segment")
    if selected_segment_column != "<none>" and filtered_df[selected_segment_column].nunique(dropna=True) > 1:
        segment_df = (
            filtered_df.groupby(selected_segment_column, dropna=False, as_index=False)[measure_column]
            .sum()
            .sort_values(measure_column, ascending=True)
        )
        st.bar_chart(segment_df.set_index(selected_segment_column)[measure_column])
    else:
        fallback_df = filtered_df.reset_index(drop=True).reset_index(names="row_group")
        fallback_df["row_group"] = fallback_df["row_group"] // max(len(fallback_df) // 10, 1)
        segment_df = fallback_df.groupby("row_group", as_index=False)[measure_column].sum()
        st.info("No usable segment column was selected, so the comparison chart uses row groups.")
        st.bar_chart(segment_df.set_index("row_group")[measure_column])

    st.subheader("Metric Distribution")
    histogram = px.histogram(
        filtered_df,
        x=measure_column,
        nbins=30,
        title=f"{measure_column} distribution",
    )
    histogram.update_layout(showlegend=False)
    st.plotly_chart(histogram, use_container_width=True)

    st.divider()

    st.subheader("Filtered Data Preview")
    st.dataframe(filtered_df.head(50), use_container_width=True)

    st.download_button(
        label="Download filtered CSV",
        data=filtered_df.to_csv(index=False),
        file_name=f"filtered_{uploaded_file.name.rsplit('.', 1)[0]}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()