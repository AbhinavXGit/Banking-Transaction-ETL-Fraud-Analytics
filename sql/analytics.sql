-- 1. Daily transaction volume and value
SELECT DATE(transaction_date) AS transaction_day,
       COUNT(*) AS transaction_count,
       ROUND(SUM(amount), 2) AS total_value
FROM transactions
GROUP BY DATE(transaction_date)
ORDER BY transaction_day;

-- 2. Overall suspicious transaction rate
SELECT COUNT(*) AS total_transactions,
       SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END) AS flagged_transactions,
       ROUND(100.0 * SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END) / COUNT(*), 2) AS flagged_rate_pct
FROM transactions;

-- 3. Top 10 customers by transaction value
SELECT customer_id, COUNT(*) AS transaction_count, ROUND(SUM(amount), 2) AS total_value
FROM transactions
GROUP BY customer_id
ORDER BY total_value DESC
LIMIT 10;

-- 4. Flagged transactions by rule
SELECT 'HIGH_AMOUNT' AS rule_name, COUNT(*) AS flagged_count
FROM transactions WHERE high_amount_flag = 1
UNION ALL
SELECT 'RAPID_BURST', COUNT(*) FROM transactions WHERE rapid_burst_flag = 1
UNION ALL
SELECT 'REPEATED_FAILURES', COUNT(*) FROM transactions WHERE repeated_failures_flag = 1
UNION ALL
SELECT 'HIGH_RISK_COUNTRY', COUNT(*) FROM transactions WHERE high_risk_country_flag = 1;

-- 5. Rank transactions by amount within each customer (window function)
SELECT customer_id, transaction_id, amount,
       ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS amount_rank
FROM transactions;

-- 6. Customer summary using a CTE
WITH customer_summary AS (
    SELECT customer_id, COUNT(*) AS txn_count, SUM(amount) AS total_spend,
           SUM(CASE WHEN is_suspicious THEN 1 ELSE 0 END) AS flagged_count
    FROM transactions
    GROUP BY customer_id
)
SELECT * FROM customer_summary
WHERE flagged_count > 0
ORDER BY flagged_count DESC, total_spend DESC;
