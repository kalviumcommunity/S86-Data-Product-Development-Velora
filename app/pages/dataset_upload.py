import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dataset Upload", layout="wide")

st.title("📂 Dataset Upload & Preview")
st.write("Upload complaint, customer or churn datasets for instant analysis.")

uploaded_file = st.file_uploader(
    "Upload CSV or JSON",
    type=["csv", "json"]
)

if uploaded_file is None:
    st.info("Please upload a CSV or JSON dataset.")
    st.stop()

try:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)

    else:
        st.error("Unsupported file type.")
        st.stop()

    if df.empty:
        st.warning("Uploaded dataset is empty.")
        st.stop()

except Exception:
    st.error("Unable to read the uploaded file.")
    st.stop()

st.success(
    f"{uploaded_file.name} loaded successfully "
    f"({len(df)} rows × {len(df.columns)} columns)"
)

st.divider()

# ------------------------
# KPI Cards
# ------------------------

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Rows", len(df))

with c2:
    st.metric("Columns", len(df.columns))

with c3:
    total_nulls = df.isnull().sum().sum()
    total_cells = df.shape[0] * df.shape[1]
    null_pct = (total_nulls / total_cells) * 100
    st.metric("Null %", f"{null_pct:.2f}%")

st.divider()

# ------------------------
# Preview
# ------------------------

st.subheader("First 10 Records")

st.dataframe(
    df.head(10),
    use_container_width=True
)

# ------------------------
# Column Summary
# ------------------------

st.subheader("Column Summary")

summary = pd.DataFrame({

    "Column": df.columns,

    "Data Type": df.dtypes.astype(str),

    "Non Null": df.notnull().sum().values,

    "Null Count": df.isnull().sum().values,

    "Null %": (
        df.isnull().sum() /
        len(df) * 100
    ).round(2).values

})

st.dataframe(summary, use_container_width=True)

# ------------------------
# Statistics
# ------------------------

numeric_df = df.select_dtypes(include="number")

if not numeric_df.empty:

    st.subheader("Descriptive Statistics")

    st.dataframe(
        numeric_df.describe(),
        use_container_width=True
    )

# ------------------------
# Complaint Analytics
# ------------------------

st.subheader("Quick Exploration")

numeric_columns = numeric_df.columns.tolist()

if numeric_columns:

    selected = st.selectbox(
        "Choose Numeric Column",
        numeric_columns
    )

    st.bar_chart(
        df[selected].value_counts().head(20)
    )

# ------------------------
# Download Clean Dataset
# ------------------------

st.subheader("Export Dataset")

csv = df.to_csv(index=False)

st.download_button(
    "Download CSV",
    csv,
    file_name="velora_dataset.csv",
    mime="text/csv"
)