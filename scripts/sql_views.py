import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

os.makedirs("database/views", exist_ok=True)
os.makedirs("database/aggregations", exist_ok=True)
os.makedirs("output", exist_ok=True)

engine = create_engine("sqlite:///analytics.db")
conn = engine.raw_connection()
cursor = conn.cursor()

# --------------------------
# Sample Tables
# --------------------------

customers = pd.DataFrame({
    "customer_id":[1,2,3],
    "customer_name":["Alice","Bob","Charlie"],
    "segment":["Enterprise","SMB","Enterprise"]
})

orders = pd.DataFrame({
    "order_id":[101,102,103,104],
    "customer_id":[1,1,2,3],
    "order_amount":[500,300,700,600],
    "order_date":[
        "2024-04-01",
        "2024-04-05",
        "2024-04-08",
        "2024-04-12"
    ]
})

products = pd.DataFrame({
    "product_id":[1,2],
    "product_name":["Laptop","Mouse"]
})

customers.to_sql("customers",engine,if_exists="replace",index=False)
orders.to_sql("orders",engine,if_exists="replace",index=False)
products.to_sql("products",engine,if_exists="replace",index=False)

# --------------------------
# View 1
# --------------------------

cursor.execute("DROP VIEW IF EXISTS vw_active_customers")

cursor.execute("""
CREATE VIEW vw_active_customers AS

SELECT

c.customer_id,

c.customer_name,

c.segment,

COUNT(o.order_id) AS order_count,

SUM(o.order_amount) AS revenue

FROM customers c

LEFT JOIN orders o

ON c.customer_id=o.customer_id

GROUP BY

c.customer_id,
c.customer_name,
c.segment
""")

# --------------------------
# View 2
# --------------------------

cursor.execute("DROP VIEW IF EXISTS vw_customer_revenue")

cursor.execute("""

CREATE VIEW vw_customer_revenue AS

SELECT

segment,

COUNT(*) AS total_customers,

AVG(order_amount) AS average_order

FROM customers c

JOIN orders o

ON c.customer_id=o.customer_id

GROUP BY segment

""")

conn.commit()

print("Views Created")

# --------------------------
# Aggregated Table
# --------------------------

cursor.execute("DROP TABLE IF EXISTS agg_daily_metrics")

cursor.execute("""

CREATE TABLE agg_daily_metrics(

aggregation_date TEXT,

metric_name TEXT,

metric_value REAL,

row_count INTEGER,

updated_at TEXT

)

""")

cursor.execute("""

INSERT INTO agg_daily_metrics

SELECT

order_date,

'total_revenue',

SUM(order_amount),

COUNT(*),

datetime('now')

FROM orders

GROUP BY order_date

""")

conn.commit()

print("Aggregation Table Created")

# --------------------------
# Query Views
# --------------------------

active = pd.read_sql(

"SELECT * FROM vw_active_customers",

engine

)

summary = pd.read_sql(

"SELECT * FROM vw_customer_revenue",

engine

)

agg = pd.read_sql(

"SELECT * FROM agg_daily_metrics",

engine

)

print(active)

print(summary)

print(agg)

# --------------------------
# Save Report
# --------------------------

with open(

"output/data_layer_report.txt",

"w"

) as f:

    f.write("Views Created\n\n")

    f.write(str(active))

    f.write("\n\n")

    f.write(str(summary))

    f.write("\n\n")

    f.write(str(agg))

print("Report Saved")