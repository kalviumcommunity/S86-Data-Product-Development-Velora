-- View: Customer Revenue

CREATE VIEW vw_customer_revenue AS

SELECT

segment,

COUNT(*) AS total_customers,

AVG(order_amount) AS average_order

FROM customers c

JOIN orders o

ON c.customer_id=o.customer_id

GROUP BY segment;