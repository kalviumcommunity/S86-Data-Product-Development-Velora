import os
import pandas as pd
from sqlalchemy import create_engine

os.makedirs("output", exist_ok=True)

engine = create_engine("sqlite:///analytics.db")

# --------------------------
# Sample Data
# --------------------------

customers = pd.DataFrame({
    "customer_id":[1,2,3,4,5],
    "customer_type":[
        "Enterprise",
        "SMB",
        "Enterprise",
        "Individual",
        "SMB"
    ],
    "signup_date":[
        "2024-01-01",
        "2024-01-10",
        "2024-02-15",
        "2024-03-01",
        "2024-03-20"
    ]
})

orders = pd.DataFrame({
    "order_id":[101,102,103,104,105,106],
    "customer_id":[1,1,2,3,3,6],
    "order_amount":[500,800,300,900,400,700],
    "order_date":[
        "2024-04-01",
        "2024-04-05",
        "2024-04-10",
        "2024-04-15",
        "2024-04-20",
        "2024-04-25"
    ]
})

order_items = pd.DataFrame({
    "order_id":[101,101,102,103,104,105],
    "product_id":[1,2,2,3,1,4],
    "quantity":[2,1,3,1,2,5],
    "unit_price":[100,300,200,300,200,50]
})

products = pd.DataFrame({
    "product_id":[1,2,3,4],
    "product_name":[
        "Laptop",
        "Mouse",
        "Keyboard",
        "Monitor"
    ]
})

customers.to_sql(
    "customers",
    engine,
    if_exists="replace",
    index=False
)

orders.to_sql(
    "orders",
    engine,
    if_exists="replace",
    index=False
)

order_items.to_sql(
    "order_items",
    engine,
    if_exists="replace",
    index=False
)

products.to_sql(
    "products",
    engine,
    if_exists="replace",
    index=False
)

# --------------------------
# Task 1
# LEFT JOIN
# --------------------------

query = """
SELECT
c.customer_id,
c.customer_type,
COUNT(o.order_id) AS order_count,
SUM(o.order_amount) AS total_spent

FROM customers c

LEFT JOIN orders o

ON c.customer_id=o.customer_id

GROUP BY
c.customer_id,
c.customer_type
"""

left_join = pd.read_sql(query, engine)

print("LEFT JOIN")
print(left_join)

print()

print("Customers Before :",len(customers))
print("Rows After :",len(left_join))

# --------------------------
# Task 2
# Unmatched Records
# --------------------------

no_orders = pd.read_sql("""

SELECT
c.customer_id,
c.customer_type

FROM customers c

LEFT JOIN orders o

ON c.customer_id=o.customer_id

WHERE o.order_id IS NULL

""",engine)

orphan_orders = pd.read_sql("""

SELECT
o.order_id,
o.customer_id

FROM orders o

LEFT JOIN customers c

ON o.customer_id=c.customer_id

WHERE c.customer_id IS NULL

""",engine)

print()

print("Customers Without Orders")

print(no_orders)

print()

print("Orphan Orders")

print(orphan_orders)

# --------------------------
# Task 3
# Compare Join Types
# --------------------------

inner = pd.read_sql("""

SELECT *

FROM customers c

INNER JOIN orders o

ON c.customer_id=o.customer_id

""",engine)

left = pd.read_sql("""

SELECT *

FROM customers c

LEFT JOIN orders o

ON c.customer_id=o.customer_id

""",engine)

full = pd.merge(
    customers,
    orders,
    how="outer",
    on="customer_id"
)

print()

print("INNER :",len(inner))

print("LEFT :",len(left))

print("FULL :",len(full))

# --------------------------
# Task 4
# Multi Table Join
# --------------------------

query = """

SELECT

c.customer_id,

c.customer_type,

o.order_id,

o.order_date,

oi.product_id,

p.product_name,

oi.quantity,

oi.unit_price,

(oi.quantity*oi.unit_price)

AS line_total

FROM customers c

LEFT JOIN orders o

ON c.customer_id=o.customer_id

LEFT JOIN order_items oi

ON o.order_id=oi.order_id

LEFT JOIN products p

ON oi.product_id=p.product_id

"""

multi = pd.read_sql(query,engine)

print()

print("MULTI TABLE JOIN")

print(multi)

# --------------------------
# Task 5
# Documentation
# --------------------------

report = """
SQL JOIN ANALYSIS

LEFT JOIN
Keeps all customers.
Customers without orders remain.

INNER JOIN
Returns only matching customers.

FULL OUTER JOIN
Returns every customer and every order.

Validation
Checked row counts.
Checked orphan orders.
Verified join outputs.

Business Use
Customer analysis
Revenue analysis
Product analysis
"""

with open(
    "output/join_report.txt",
    "w"
) as f:

    f.write(report)

print()

print("Report Saved")