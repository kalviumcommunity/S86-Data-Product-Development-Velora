-- View: Active Customers

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
c.segment;