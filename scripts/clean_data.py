import pandas as pd

# Load datasets
customers = pd.read_csv("data/customers.csv")
tickets = pd.read_csv("data/tickets.csv")
escalations = pd.read_csv("data/escalations.csv")
cancellations = pd.read_csv("data/cancellations.csv")

# Remove duplicates
customers.drop_duplicates(inplace=True)
tickets.drop_duplicates(inplace=True)
escalations.drop_duplicates(inplace=True)
cancellations.drop_duplicates(inplace=True)

# Convert dates
tickets["created_date"] = pd.to_datetime(tickets["created_date"])
tickets["resolved_date"] = pd.to_datetime(tickets["resolved_date"], errors="coerce")

customers["subscription_start"] = pd.to_datetime(customers["subscription_start"])

cancellations["cancellation_date"] = pd.to_datetime(
    cancellations["cancellation_date"]
)

# Standardize text columns
tickets["category"] = tickets["category"].str.title()
tickets["status"] = tickets["status"].str.title()

customers["segment"] = customers["segment"].str.title()

# Save cleaned datasets
customers.to_csv("data/customers_clean.csv", index=False)
tickets.to_csv("data/tickets_clean.csv", index=False)
escalations.to_csv("data/escalations_clean.csv", index=False)
cancellations.to_csv("data/cancellations_clean.csv", index=False)

print("✅ Data cleaned successfully!")