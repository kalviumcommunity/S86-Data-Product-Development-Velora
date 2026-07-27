import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Dataset Upload",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Dataset Upload & Dynamic Preview")
st.write("Upload a CSV or JSON dataset to preview, validate, and explore your data.")

uploaded_file = st.file_uploader(
    "Upload CSV or JSON",
    type=["csv", "json"]
)

if uploaded_file is None:
    st.info("Upload a CSV or JSON file to begin.")
    st.stop()

try:
    # Load file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)

    else:
        st.error("Unsupported file type.")
        st.stop()

    # Empty file validation
    if df.empty:
        st.warning("Uploaded file is empty.")
        st.stop()

except Exception:
    st.error("Could not read this file. Please check the format and try again.")
    st.stop()

# Success Message
st.success(
    f"Loaded **{uploaded_file.name}** ({len(df)} rows, {len(df.columns)} columns)"
)

st.divider()

# ---------------------------
# Dataset Summary
# ---------------------------

st.header("Dataset Preview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Rows", len(df))

with col2:
    st.metric("Columns", len(df.columns))

with col3:
    total_nulls = df.isnull().sum().sum()
    total_cells = max(df.shape[0] * df.shape[1], 1)
    null_pct = (total_nulls / total_cells) * 100
    st.metric("Null %", f"{null_pct:.1f}%")

st.divider()

# ---------------------------
# First 10 Rows
# ---------------------------

st.subheader("First 10 Rows")
st.dataframe(df.head(10), use_container_width=True)

# ---------------------------
# Column Summary
# ---------------------------

st.subheader("Column Summary")

summary = pd.DataFrame({
    "Column": df.columns,
    "Type": df.dtypes.astype(str).values,
    "Non-Null": df.notnull().sum().values,
    "Null Count": df.isnull().sum().values,
    "Null %": (df.isnull().sum() / len(df) * 100).round(1).values
})

st.dataframe(summary, use_container_width=True)

# ---------------------------
# Descriptive Statistics
# ---------------------------

st.subheader("Descriptive Statistics")

st.dataframe(
    df.describe(include="all"),
    use_container_width=True
)

# ---------------------------
# Quick Filter
# ---------------------------

st.subheader("Quick Filter")

filter_columns = df.columns.tolist()

selected_column = st.selectbox(
    "Select a column",
    filter_columns
)

unique_values = df[selected_column].dropna().unique()

if len(unique_values) > 0:
    selected_value = st.selectbox(
        "Select a value",
        unique_values
    )

    filtered_df = df[df[selected_column] == selected_value]

    st.write(f"Filtered Records: {len(filtered_df)}")

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

st.divider()

# ---------------------------
# Quick Exploration
# ---------------------------

st.subheader("Quick Exploration")

numeric_cols = df.select_dtypes(include="number").columns.tolist()

if numeric_cols:

    selected_numeric = st.selectbox(
        "Choose Numeric Column",
        numeric_cols
    )

    st.bar_chart(
        df[selected_numeric].value_counts().head(20)
    )

else:
    st.info("No numeric columns available.")

# ---------------------------
# Download Dataset
# ---------------------------

st.subheader("Export Dataset")

csv = df.to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="uploaded_dataset.csv",
    mime="text/csv"
)