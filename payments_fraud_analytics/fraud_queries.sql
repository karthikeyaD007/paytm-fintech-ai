-- ============================================================================
-- fraud_queries.sql
-- Run against paytm_payments.db (SQLite)
--   sqlite3 paytm_payments.db < fraud_queries.sql
-- Demonstrates: SELECT, WHERE, ORDER BY, LIMIT, DISTINCT, GROUP BY, HAVING,
-- INNER JOIN, LEFT JOIN, plus the required fraud-analysis queries.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CHARGEBACK IDENTIFICATION
-- All chargeback transactions, newest first, joined to merchant + user info.
-- Demonstrates: SELECT, WHERE, ORDER BY, INNER JOIN
-- ----------------------------------------------------------------------------
SELECT
    t.transaction_id,
    t.user_id,
    u.signup_date,
    t.merchant_id,
    m.merchant_name,
    t.transaction_time,
    t.amount_inr,
    t.risk_score
FROM transactions t
INNER JOIN users u      ON t.user_id = u.user_id
INNER JOIN merchants m  ON t.merchant_id = m.merchant_id
WHERE t.status = 'chargeback'
ORDER BY t.transaction_time DESC;


-- ----------------------------------------------------------------------------
-- 2. BURNER-ACCOUNT DETECTION
-- Chargeback transactions where the account signed up less than 30 days
-- before the transaction (newly created / "burner" accounts). Boundary is
-- explicit and unambiguous: 0 <= (transaction_time - signup_date) < 30 days
-- -- signup must be on/before the transaction (never a negative age), and
-- strictly less than 30 days earlier (never exactly 30 or more).
-- Demonstrates: SELECT, WHERE, ORDER BY, INNER JOIN, LIMIT
-- ----------------------------------------------------------------------------
SELECT
    t.transaction_id,
    t.user_id,
    u.signup_date,
    t.transaction_time,
    CAST(julianday(t.transaction_time) - julianday(u.signup_date) AS INTEGER) AS account_age_days,
    t.amount_inr,
    t.merchant_id,
    t.risk_score
FROM transactions t
INNER JOIN users u ON t.user_id = u.user_id
WHERE t.status = 'chargeback'
  AND (julianday(t.transaction_time) - julianday(u.signup_date)) >= 0
  AND (julianday(t.transaction_time) - julianday(u.signup_date)) < 30
ORDER BY account_age_days ASC
LIMIT 50;


-- ----------------------------------------------------------------------------
-- 3. VELOCITY-ATTACK DETECTION
-- Users making 3+ transactions within any rolling 10-minute window.
-- Self-join transactions to their peers within 10 minutes for the same user,
-- then keep users whose peer-count reaches the 3-transaction threshold.
-- Demonstrates: SELECT, WHERE, GROUP BY, HAVING, DISTINCT, INNER JOIN, ORDER BY
-- ----------------------------------------------------------------------------
SELECT
    t1.user_id,
    COUNT(DISTINCT t1.transaction_id) AS txns_in_window,
    MIN(t1.transaction_time) AS window_start,
    MAX(t1.transaction_time) AS window_end
FROM transactions t1
INNER JOIN transactions t2
    ON t1.user_id = t2.user_id
   AND t1.transaction_id != t2.transaction_id
   AND ABS(julianday(t1.transaction_time) - julianday(t2.transaction_time)) * 24 * 60 <= 10
GROUP BY t1.user_id
HAVING COUNT(DISTINCT t1.transaction_id) >= 3
ORDER BY txns_in_window DESC;


-- ----------------------------------------------------------------------------
-- 3b. VELOCITY-ATTACK DETAIL
-- The individual transactions belonging to flagged velocity-attack users.
-- Demonstrates: SELECT, WHERE, ORDER BY, DISTINCT
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    t.transaction_id,
    t.user_id,
    t.transaction_time,
    t.amount_inr,
    t.status,
    t.risk_score
FROM transactions t
WHERE t.user_id IN (
    SELECT t1.user_id
    FROM transactions t1
    INNER JOIN transactions t2
        ON t1.user_id = t2.user_id
       AND t1.transaction_id != t2.transaction_id
       AND ABS(julianday(t1.transaction_time) - julianday(t2.transaction_time)) * 24 * 60 <= 10
    GROUP BY t1.user_id
    HAVING COUNT(DISTINCT t1.transaction_id) >= 3
)
ORDER BY t.user_id, t.transaction_time;


-- ----------------------------------------------------------------------------
-- 4. MERCHANT-LEVEL FRAUD PATTERNS
-- Chargeback count / rate and average risk score per merchant.
-- Demonstrates: SELECT, GROUP BY, HAVING, LEFT JOIN, ORDER BY
-- ----------------------------------------------------------------------------
SELECT
    m.merchant_id,
    m.merchant_name,
    m.category,
    COUNT(t.transaction_id) AS total_transactions,
    SUM(CASE WHEN t.status = 'chargeback' THEN 1 ELSE 0 END) AS chargeback_count,
    ROUND(100.0 * SUM(CASE WHEN t.status = 'chargeback' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS chargeback_rate_pct,
    ROUND(AVG(t.risk_score), 1) AS avg_risk_score
FROM merchants m
LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
GROUP BY m.merchant_id, m.merchant_name, m.category
HAVING COUNT(t.transaction_id) > 0
ORDER BY chargeback_rate_pct DESC;


-- ----------------------------------------------------------------------------
-- 5. MERCHANTS WITH ZERO TRANSACTIONS (if any) -- data-quality check
-- Demonstrates: LEFT JOIN, WHERE
-- ----------------------------------------------------------------------------
SELECT m.merchant_id, m.merchant_name
FROM merchants m
LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
WHERE t.transaction_id IS NULL;


-- ----------------------------------------------------------------------------
-- 6. PAYMENT METHOD BREAKDOWN
-- Distinct payment methods used, with volume and GMV.
-- Demonstrates: SELECT, DISTINCT, GROUP BY, ORDER BY
-- ----------------------------------------------------------------------------
SELECT
    payment_method,
    COUNT(*) AS txn_count,
    SUM(amount_inr) AS gmv_inr,
    ROUND(AVG(amount_inr), 2) AS avg_amount_inr
FROM transactions
GROUP BY payment_method
ORDER BY gmv_inr DESC;


-- ----------------------------------------------------------------------------
-- 7. HIGH-RISK TRANSACTIONS (risk_score >= 70), captured or chargeback only
-- Demonstrates: SELECT, WHERE, ORDER BY, LIMIT
-- ----------------------------------------------------------------------------
SELECT transaction_id, user_id, merchant_id, transaction_time, amount_inr, status, risk_score
FROM transactions
WHERE risk_score >= 70
  AND status IN ('captured', 'chargeback')
ORDER BY risk_score DESC, transaction_time DESC
LIMIT 25;


-- ----------------------------------------------------------------------------
-- 8. TOP 10 USERS BY TOTAL SPEND (captured transactions only)
-- Demonstrates: SELECT, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, INNER JOIN
-- ----------------------------------------------------------------------------
SELECT
    u.user_id,
    u.signup_date,
    COUNT(t.transaction_id) AS captured_txns,
    SUM(t.amount_inr) AS total_spend_inr
FROM users u
INNER JOIN transactions t ON u.user_id = t.user_id
WHERE t.status = 'captured'
GROUP BY u.user_id, u.signup_date
HAVING COUNT(t.transaction_id) >= 1
ORDER BY total_spend_inr DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 9. DAILY GMV AND CHARGEBACK TREND
-- Demonstrates: SELECT, GROUP BY, ORDER BY
-- ----------------------------------------------------------------------------
SELECT
    DATE(transaction_time) AS txn_date,
    COUNT(*) AS txn_count,
    SUM(CASE WHEN status = 'captured' THEN amount_inr ELSE 0 END) AS gmv_inr,
    SUM(CASE WHEN status = 'chargeback' THEN 1 ELSE 0 END) AS chargebacks
FROM transactions
GROUP BY DATE(transaction_time)
ORDER BY txn_date ASC;
