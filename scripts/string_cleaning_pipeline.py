import pandas as pd


def strip_all_strings(df):
    """Strip whitespace from all string columns."""
    string_cols = df.select_dtypes(include=["object"]).columns
    total_issues = 0

    for col in string_cols:
        before_counts = df[col].value_counts(dropna=False)

        whitespace_count = (
            df[col]
            .dropna()
            .astype(str)
            .apply(lambda value: value != value.strip())
            .sum()
        )

        total_issues += whitespace_count

        print(f"\nBefore stripping {col}:")
        print(before_counts)

        df[col] = df[col].str.strip()

        print(f"\nAfter stripping {col}:")
        print(df[col].value_counts(dropna=False))

        print(
            f"{col}: {whitespace_count} whitespace issues fixed"
        )

    print(
        f"\nTotal whitespace issues fixed: {total_issues}"
    )

    return df


def normalize_casing(df, columns_to_lower):
    """Normalize selected columns to lowercase."""
    for col in columns_to_lower:
        df[col] = df[col].str.lower()
        print(f"Normalized {col} to lowercase")

    return df


def remove_special_characters(df, columns):
    """Remove non-alphanumeric characters."""
    pattern = r"[^a-zA-Z0-9 ]"

    for col in columns:
        print(f"\nBefore special character cleaning - {col}:")
        print(df[col])

        df[col] = df[col].str.replace(
            pattern,
            "",
            regex=True
        )

        print(f"\nAfter special character cleaning - {col}:")
        print(df[col])

    return df


def clean_text_column(
    series,
    lowercase=True,
    strip=True,
    remove_special=False,
    mapping=None
):
    """
    Reusable text cleaning function.

    Args:
        series: Pandas Series to clean
        lowercase: Convert text to lowercase
        strip: Remove leading and trailing whitespace
        remove_special: Remove non-alphanumeric characters
        mapping: Dictionary for category standardization

    Returns:
        Cleaned Pandas Series
    """
    result = series.copy()

    if result.isna().any():
        print(
            f"Warning: {result.isna().sum()} "
            "null values in column"
        )

    if strip:
        result = result.str.strip()

    if lowercase:
        result = result.str.lower()

    if remove_special:
        result = result.str.replace(
            r"[^a-zA-Z0-9 ]",
            "",
            regex=True
        )

    if mapping:
        result = result.replace(mapping)

    return result


if __name__ == "__main__":

    # Synthetic dataset with messy text
    data = {
        "customer_name": [
            " JOHN ",
            "john",
            "John",
            " ALICE ",
            "alice",
            None
        ],
        "product_category": [
            " Electronics ",
            "electronics",
            "ELECTRONICS",
            " Clothing ",
            "clothing",
            "CLOTHING"
        ],
        "segment": [
            "B2B",
            "b2b",
            "B 2 B",
            "business-to-business",
            "SME",
            "small medium enterprise"
        ],
        "location": [
            "São Paulo",
            "Montréal",
            "Chennai",
            "New York!",
            "London#",
            "Bengaluru"
        ]
    }

    df = pd.DataFrame(data)

    print("\nORIGINAL DATA")
    print(df)

    # Task 1 - Strip whitespace
    print("\nTASK 1 - STRIP WHITESPACE")
    df = strip_all_strings(df)

    # Save data before casing normalization
    before_casing = df.copy()

    # Task 2 - Normalize casing
    print("\nTASK 2 - NORMALIZE CASING")

    print("\nBefore casing normalization:")
    print(
        before_casing[
            [
                "customer_name",
                "product_category",
                "segment"
            ]
        ].head()
    )

    df = normalize_casing(
        df,
        [
            "customer_name",
            "product_category",
            "segment"
        ]
    )

    print("\nAfter casing normalization:")
    print(
        df[
            [
                "customer_name",
                "product_category",
                "segment"
            ]
        ].head()
    )

    # Task 3 - Remove special characters
    print("\nTASK 3 - REMOVE SPECIAL CHARACTERS")

    df = remove_special_characters(
        df,
        ["location"]
    )

    # Task 4 - Mapping dictionaries
    print("\nTASK 4 - STANDARDIZE CATEGORIES")

    segment_map = {
        "b2b": "B2B",
        "b 2 b": "B2B",
        "business-to-business": "B2B",

        "sme": "SMB",
        "small medium enterprise": "SMB",
        "small business": "SMB",

        "enterprise": "Enterprise",
        "large enterprise": "Enterprise",
        "corporate": "Enterprise"
    }

    print("\nSegment counts before mapping:")
    print(df["segment"].value_counts())

    df["segment"] = df["segment"].replace(
        segment_map
    )

    print("\nSegment counts after mapping:")
    print(df["segment"].value_counts())

    # Task 5 - Reusable function
    print("\nTASK 5 - REUSABLE CLEANING FUNCTION")

    df["customer_name"] = clean_text_column(
        df["customer_name"],
        lowercase=True,
        strip=True
    )

    df["product_category"] = clean_text_column(
        df["product_category"],
        lowercase=True,
        strip=True,
        remove_special=True
    )

    df["segment"] = clean_text_column(
        df["segment"],
        lowercase=False,
        strip=True,
        mapping=segment_map
    )

    print("\nFINAL CLEANED DATA")
    print(df)

    # Edge-case testing
    print("\nEDGE CASE TESTING")

    test_cases = [
        "  Product A  ",
        "PRODUCT B",
        "Product_C",
        None,
        ""
    ]

    test_series = pd.Series(test_cases)

    result = clean_text_column(
        test_series,
        lowercase=True,
        strip=True,
        remove_special=True
    )

    print(result)