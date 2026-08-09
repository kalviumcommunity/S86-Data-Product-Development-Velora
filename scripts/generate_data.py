import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)

# ----------------------------
# Configuration
# ----------------------------
NUM_CUSTOMERS = 500
NUM_TICKETS = 2000

SEGMENTS = ["Basic", "Premium", "Enterprise"]
CHANNELS = ["Email", "Chat", "Phone"]
REGIONS = ["North", "South", "East", "West"]

CATEGORIES = [
    "Billing",
    "Technical",
    "Payment",
    "Login",
    "Account"
]

STATUS = ["Resolved", "Open", "Pending"]

CANCEL_REASONS = [
    "Poor Support",
    "High Pricing",
    "Service Quality",
    "Competitor",
    "Product Issues"
]

# ----------------------------
# Generate Customers
# ----------------------------

customers = []

customer_ids = []

for i in range(1, NUM_CUSTOMERS + 1):

    cid = f"C{i:04d}"
    customer_ids.append(cid)

    customers.append({
        "customer_id": cid,
        "customer_name": fake.name(),
        "segment": random.choice(SEGMENTS),
        "region": random.choice(REGIONS),
        "support_channel": random.choice(CHANNELS),
        "subscription_start": fake.date_between(
            start_date="-2y",
            end_date="-6m"
        ),
        "subscription_status": "Active"
    })

customers_df = pd.DataFrame(customers)

# ----------------------------
# Generate Tickets
# ----------------------------

tickets = []

ticket_ids = []

start_date = datetime(2025, 1, 1)

for i in range(1, NUM_TICKETS + 1):

    tid = f"T{i:05d}"
    ticket_ids.append(tid)

    customer = random.choice(customer_ids)

    category = random.choice(CATEGORIES)

    status = random.choices(
        STATUS,
        weights=[70, 20, 10]
    )[0]

    created = start_date + timedelta(
        days=random.randint(0, 180)
    )

    resolved = None

    if status == "Resolved":

        resolution_days = random.randint(1, 10)

        resolved = created + timedelta(days=resolution_days)

    tickets.append({

        "ticket_id": tid,

        "customer_id": customer,

        "category": category,

        "status": status,

        "created_date": created.date(),

        "resolved_date": resolved

    })

tickets_df = pd.DataFrame(tickets)

# ----------------------------
# Generate Escalations
# ----------------------------

escalations = []

level_choices = ["L1", "L2", "L3"]

count = 1

for row in tickets:

    probability = 0.15

    if row["category"] == "Technical":
        probability = 0.45

    elif row["category"] == "Billing":
        probability = 0.35

    elif row["category"] == "Payment":
        probability = 0.30

    if random.random() < probability:

        escalations.append({

            "escalation_id": f"E{count:05d}",

            "ticket_id": row["ticket_id"],

            "customer_id": row["customer_id"],

            "escalated": "Yes",

            "escalation_level": random.choice(level_choices)

        })

        count += 1

escalations_df = pd.DataFrame(escalations)

# ----------------------------
# Generate Cancellations
# ----------------------------

cancelled_customers = random.sample(customer_ids, 100)

cancellations = []

for cid in cancelled_customers:

    cancellations.append({

        "customer_id": cid,

        "cancelled": "Yes",

        "cancellation_date": fake.date_between(
            start_date="-6m",
            end_date="today"
        ),

        "cancellation_reason": random.choice(
            CANCEL_REASONS
        )

    })

cancellations_df = pd.DataFrame(cancellations)

customers_df.loc[
    customers_df.customer_id.isin(cancelled_customers),
    "subscription_status"
] = "Cancelled"

# ----------------------------
# Save CSV Files
# ----------------------------

customers_df.to_csv("data/customers.csv", index=False)

tickets_df.to_csv("data/tickets.csv", index=False)

escalations_df.to_csv("data/escalations.csv", index=False)

cancellations_df.to_csv("data/cancellations.csv", index=False)

print("✅ Customers :", len(customers_df))
print("✅ Tickets :", len(tickets_df))
print("✅ Escalations :", len(escalations_df))
print("✅ Cancellations :", len(cancellations_df))

print("\nDatasets generated successfully!")