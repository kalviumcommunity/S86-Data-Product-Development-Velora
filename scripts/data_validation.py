import os
import pandas as pd


def create_sample_data():
    """Create sample data containing valid and invalid records."""

    data = {
        "customer_id": [
            101,
            102,
            None,
            104,
            105,
            106
        ],
        "age": [
            25,
            200,
            35,
            -5,
            45,
            30
        ],
        "price": [
            500,
            -100,
            750,
            300,
            1000,
            250
        ],
        "birth_date": [
            "2000-01-15",
            "2050-05-10",
            "1995-03-20",
            "1985-06-12",
            "1910-01-01",
            "1998-09-25"
        ],
        "email": [
            "alice@example.com",
            "bobexample.com",
            "carol@example.com",
            None,
            "david@example.com",
            "john@example.com"
        ],
        "phone": [
            "9876543210",
            "98765",
            "9123456789",
            "abcdefghij",
            "9988776655",
            "9012345678"
        ],
        "start_date": [
            "2025-01-01",
            "2025-03-01",
            "2025-04-01",
            "2025-06-01",
            "2025-07-01",
            "2025-08-01"
        ],
        "end_date": [
            "2025-02-01",
            "2025-02-01",
            "2025-05-01",
            "2025-05-01",
            "2025-08-01",
            "2025-09-01"
        ]
    }

    return pd.DataFrame(data)


def validate_data(df):
    """Apply validation rules to the dataset."""

    df = df.copy()

    # Convert date columns to datetime
    df["birth_date"] = pd.to_datetime(
        df["birth_date"],
        errors="coerce"
    )

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        errors="coerce"
    )

    df["end_date"] = pd.to_datetime(
        df["end_date"],
        errors="coerce"
    )

    # Rule 1: Age must be between 0 and 150
    df["valid_age"] = (
        (df["age"] >= 0)
        & (df["age"] <= 150)
    )

    # Rule 2: Price cannot be negative
    df["valid_price"] = df["price"] >= 0

    # Rule 3: Birth date must be between 1920 and today
    df["valid_birth_date"] = (
        (df["birth_date"] >= pd.Timestamp("1920-01-01"))
        & (df["birth_date"] <= pd.Timestamp.now())
    )

    # Rule 4: Customer ID is required
    df["valid_customer_id"] = (
        df["customer_id"].notna()
    )

    # Rule 5: Email is required
    df["valid_email"] = df["email"].notna()

    # Rule 6: Email must contain @
    df["valid_email_format"] = (
        df["email"]
        .str.contains("@", na=False)
    )

    # Rule 7: Phone must contain exactly 10 digits
    df["valid_phone"] = (
        df["phone"]
        .str.match(r"^\d{10}$", na=False)
    )

    # Rule 8: End date must be after or equal to start date
    df["valid_date_order"] = (
        df["end_date"] >= df["start_date"]
    )

    return df


def generate_validation_report(df):
    """Generate a structured validation report."""

    validation_rules = {
        "Age Range": "valid_age",
        "Non-Negative Price": "valid_price",
        "Birth Date Range": "valid_birth_date",
        "Customer ID Required": "valid_customer_id",
        "Email Required": "valid_email",
        "Email Format": "valid_email_format",
        "Phone Format": "valid_phone",
        "Date Order": "valid_date_order"
    }

    report = []

    print("\nVALIDATION REPORT")
    print("=" * 60)

    for rule_name, column in validation_rules.items():
        passed = int(df[column].sum())
        failed = int((~df[column]).sum())

        report.append({
            "validation_rule": rule_name,
            "passed": passed,
            "failed": failed
        })

        print(
            f"{rule_name}: "
            f"Passed = {passed}, Failed = {failed}"
        )

    return pd.DataFrame(report)


if __name__ == "__main__":

    print("Starting data validation...\n")

    os.makedirs("output", exist_ok=True)

    # Create sample data
    df = create_sample_data()

    print("ORIGINAL DATA")
    print(df)

    # Apply validation rules
    df = validate_data(df)

    validation_cols = [
        "valid_age",
        "valid_price",
        "valid_birth_date",
        "valid_customer_id",
        "valid_email",
        "valid_email_format",
        "valid_phone",
        "valid_date_order"
    ]

    # Check whether each record passes every rule
    df["passes_all_checks"] = (
        df[validation_cols]
        .all(axis=1)
    )

    # Isolate failed records
    failures = df[
        ~df["passes_all_checks"]
    ]

    # Keep clean records
    df_clean = df[
        df["passes_all_checks"]
    ]

    # Generate structured validation report
    validation_report = generate_validation_report(df)

    print("\nOVERALL VALIDATION SUMMARY")
    print("=" * 60)

    print(f"Records: {len(df)}")

    print(
        f"Passed: "
        f"{df['passes_all_checks'].sum()}"
    )

    print(
        f"Failed: "
        f"{(~df['passes_all_checks']).sum()}"
    )

    # Save validation outputs
    failures.to_csv(
        "output/validation_failures.csv",
        index=False
    )

    validation_report.to_csv(
        "output/validation_report.csv",
        index=False
    )

    df_clean.to_csv(
        "output/validated_data.csv",
        index=False
    )

    print("\nFiles created:")

    print(
        "output/validation_failures.csv"
    )

    print(
        "output/validation_report.csv"
    )

    print(
        "output/validated_data.csv"
    )

    print("\nData validation completed.")