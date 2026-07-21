-- queries/monthly_active_users.sql
-- Monthly Active Users: distinct customers with a transaction in the last 12 months
-- Broken down by total, Enterprise, and SMB segments
SELECT
    strftime('%Y-%m-01', transaction_date)        AS month,
    COUNT(DISTINCT customer_id)                   AS active_users,
    COUNT(DISTINCT CASE WHEN customer_type = 'Enterprise'
                        THEN customer_id END)     AS enterprise_users,
    COUNT(DISTINCT CASE WHEN customer_type = 'SMB'
                        THEN customer_id END)     AS smb_users
FROM transactions
WHERE transaction_date >= date('now', '-12 months')
GROUP BY strftime('%Y-%m-01', transaction_date)
ORDER BY month DESC;
