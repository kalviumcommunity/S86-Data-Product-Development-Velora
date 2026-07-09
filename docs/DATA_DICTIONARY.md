# Data Dictionary

## Dataset Overview

**Project Name:** Velora

This dataset contains customer transaction records used to analyze customer behavior, revenue, and service cancellations. It supports business intelligence, customer retention analysis, and revenue reporting.

**Maintained By:** Velora Data Engineering Team

**Update Frequency:** Daily

**Source:** Customer Relationship Management (CRM) System

---

# Columns

## customer_id

- **Type:** Integer
- **Description:** Unique identifier assigned to each customer.
- **Business Meaning:** Used to uniquely identify every customer in the system.
- **Example:** 1
- **Null Handling:** Never null (Primary Key)
- **Related KPI:** Customer Tracking
- **Updates:** Assigned when a customer account is created.

---

## customer_name

- **Type:** String
- **Description:** Full name of the customer.
- **Business Meaning:** Helps identify customers in reports and support records.
- **Example:** Alice Smith
- **Null Handling:** Should not be null.
- **Related KPI:** Customer Records
- **Updates:** Updated whenever customer profile changes.

---

## transaction_amount

- **Type:** Float
- **Description:** Amount paid by the customer during a transaction.
- **Business Meaning:** Represents revenue generated from each transaction.
- **Example:** 150.50
- **Unit:** USD
- **Null Handling:** Missing values should be investigated.
- **Related KPI:** Monthly Revenue, Average Transaction Value
- **Updates:** Recorded when payment is completed.

---

## transaction_date

- **Type:** Datetime
- **Description:** Date when the transaction occurred.
- **Business Meaning:** Used to analyze sales trends over time.
- **Example:** 2025-01-15
- **Format:** YYYY-MM-DD
- **Null Handling:** Never null.
- **Related KPI:** Daily Revenue, Sales Trend
- **Updates:** Recorded automatically during each transaction.

---

## customer_segment

- **Type:** String
- **Description:** Category assigned to each customer.
- **Business Meaning:** Used to classify customers into business groups.
- **Valid Values:**
  - Business
  - Individual
- **Example:** Business
- **Null Handling:** If missing, classify as UNKNOWN.
- **Related KPI:** Segment Performance
- **Updates:** Updated monthly based on CRM data.

---

## has_cancelled

- **Type:** Boolean (0 = No, 1 = Yes)
- **Description:** Indicates whether the customer has cancelled the service.
- **Business Meaning:** Used to identify customers who discontinued the service.
- **Example:** 0
- **Null Handling:** Missing values treated as Unknown.
- **Related KPI:** Customer Retention
- **Updates:** Updated whenever a cancellation occurs.

---

# Column to KPI Mapping

## Monthly Revenue

**Formula**

SUM(transaction_amount)

**Related Columns**

- transaction_amount
- transaction_date

**Business Importance**

Measures total revenue generated during a selected period.

**Update Frequency**

Daily

---

## Customer Retention

**Formula**

(Number of Active Customers / Total Customers) × 100

**Related Columns**

- customer_id
- has_cancelled

**Business Importance**

Measures how successfully the company retains customers.

**Update Frequency**

Monthly

---

## Daily Revenue

**Formula**

SUM(transaction_amount) grouped by transaction_date

**Related Columns**

- transaction_amount
- transaction_date

**Business Importance**

Tracks daily sales performance.

**Update Frequency**

Daily

---

## Segment Performance

**Formula**

SUM(transaction_amount) grouped by customer_segment

**Related Columns**

- customer_segment
- transaction_amount

**Business Importance**

Identifies the most profitable customer segment.

**Update Frequency**

Monthly

---

## Transaction Count

**Formula**

COUNT(customer_id)

**Related Columns**

- customer_id

**Business Importance**

Measures business activity and customer engagement.

**Update Frequency**

Daily

---

# Ambiguous Columns & Resolutions

## Column: has_cancelled

**Original Ambiguity**

Could represent current cancellation status or future cancellation prediction.

**Resolved Meaning**

Indicates whether the customer has already cancelled the service.

**Business Interpretation**

Historical customer cancellation status used for retention analysis.

**Suggested Rename**

is_customer_cancelled

**Risk if Misunderstood**

Incorrect customer retention reports and misleading business decisions.

---

## Column: customer_segment

**Original Ambiguity**

Could refer to customer category, geographic region, subscription plan, or sales territory.

**Resolved Meaning**

Represents the customer's business category.

**Business Interpretation**

Used to compare revenue and customer behavior across different market segments.

**Suggested Rename**

market_segment

**Risk if Misunderstood**

Incorrect segmentation analysis and inaccurate business insights.

---

# Column Relationships

## Revenue per Customer

**Definition**

SUM(transaction_amount) grouped by customer_id

**Business Importance**

Identifies high-value customers for loyalty programs and personalized offers.

**Example**

Top 20% of customers contribute to over 60% of total revenue.

**Related Columns**

- customer_id
- transaction_amount
- customer_segment

---

## Revenue by Customer Segment

**Definition**

SUM(transaction_amount) grouped by customer_segment

**Business Importance**

Determines which customer segment contributes the highest revenue.

**Example**

Business customers generate more revenue than Individual customers.

**Related Columns**

- customer_segment
- transaction_amount

---

## Customer Cancellation Analysis

**Definition**

COUNT(has_cancelled = 1) grouped by customer_segment

**Business Importance**

Identifies which customer segments have the highest cancellation rate.

**Example**

Individual customers show a higher cancellation percentage than Business customers.

**Related Columns**

- has_cancelled
- customer_segment
- customer_id