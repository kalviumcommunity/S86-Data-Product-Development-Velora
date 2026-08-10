import pandas as pd

# ==========================================================
# Load Cleaned Data
# ==========================================================

customers = pd.read_csv("data/customers_clean.csv")
tickets = pd.read_csv("data/tickets_clean.csv")
escalations = pd.read_csv("data/escalations_clean.csv")
cancellations = pd.read_csv("data/cancellations_clean.csv")

# ==========================================================
# Merge Data
# ==========================================================

df = tickets.merge(
    customers,
    on="customer_id",
    how="left"
)

df = df.merge(
    escalations[
        ["ticket_id", "escalated", "escalation_level"]
    ],
    on="ticket_id",
    how="left"
)

df = df.merge(
    cancellations[
        ["customer_id", "cancelled"]
    ],
    on="customer_id",
    how="left"
)

# ==========================================================
# Handle Missing Values
# ==========================================================

df["escalated"] = df["escalated"].fillna("No")
df["cancelled"] = df["cancelled"].fillna("No")

# ==========================================================
# Date Conversion
# ==========================================================

df["created_date"] = pd.to_datetime(df["created_date"])
df["resolved_date"] = pd.to_datetime(df["resolved_date"])

# ==========================================================
# Resolution Days
# ==========================================================

df["created_date"] = pd.to_datetime(df["created_date"])
df["resolved_date"] = pd.to_datetime(df["resolved_date"])

current_date = pd.Timestamp("2026-07-01")

df["resolution_days"] = (
    df["resolved_date"] - df["created_date"]
).dt.days

# For unresolved tickets, calculate how long
# they have remained unresolved.
df.loc[
    df["resolution_days"].isna(),
    "resolution_days"
] = (
    current_date - df.loc[
        df["resolution_days"].isna(),
        "created_date"
    ]
).dt.days

df["resolution_days"] = (
    df["resolution_days"]
    .clip(lower=0)
    .astype(int)
)

# ==========================================================
# Flags
# ==========================================================

df["is_unresolved"] = df["status"] != "Resolved"

df["is_escalated"] = df["escalated"] == "Yes"

df["churned"] = df["cancelled"] == "Yes"

# ==========================================================
# Complaint Count
# ==========================================================

complaints = (
    df.groupby("customer_id")
      .size()
      .reset_index(name="complaint_count")
)

df = df.merge(
    complaints,
    on="customer_id",
    how="left"
)

df["repeat_customer"] = df["complaint_count"] >= 3

# ==========================================================
# Priority Score
# ==========================================================

df["priority_score"] = (
    df["complaint_count"] * 10 +
    df["is_unresolved"].astype(int) * 30 +
    df["is_escalated"].astype(int) * 20 +
    df["resolution_days"] * 2
)

# ==========================================================
# Priority Level
# ==========================================================

def get_priority(score):
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    return "Low"

df["priority_level"] = df["priority_score"].apply(get_priority)

# ==========================================================
# Recommended Action
# ==========================================================

def get_action(level):
    if level == "High":
        return "📞 Contact Customer Immediately"
    elif level == "Medium":
        return "📧 Follow Up Within 24 Hours"
    else:
        return "👀 Monitor"

df["recommended_action"] = df["priority_level"].apply(get_action)

# ==========================================================
# Sort by Priority
# ==========================================================

df = df.sort_values(
    by=["priority_score", "complaint_count"],
    ascending=False
)

# ==========================================================
# Priority Reason
# ==========================================================

def get_priority_reason(row):
    reasons = []

    if row["is_unresolved"]:
        reasons.append("Unresolved Ticket")

    if row["is_escalated"]:
        reasons.append("Escalated Case")

    if row["repeat_customer"]:
        reasons.append("Repeat Complaints")

    if row["resolution_days"] > 7:
        reasons.append("Delayed Resolution")

    return ", ".join(reasons) if reasons else "No Immediate Risk"

df["priority_reason"] = df.apply(get_priority_reason, axis=1)

# ==========================================================
# Save Master Dataset
# ==========================================================

df.to_csv(
    "data/master_dataset.csv",
    index=False
)

print("✅ Master dataset created successfully!")
print(f"Total Records: {len(df)}")
print(f"High Priority Customers: {(df['priority_level'] == 'High').sum()}")
print(f"Medium Priority Customers: {(df['priority_level'] == 'Medium').sum()}")
print(f"Low Priority Customers: {(df['priority_level'] == 'Low').sum()}")