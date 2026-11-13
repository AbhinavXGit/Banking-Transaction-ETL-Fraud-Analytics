CREATE DATABASE IF NOT EXISTS banking_analytics;
USE banking_analytics;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    transaction_date DATETIME NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(8),
    merchant_category VARCHAR(50),
    country VARCHAR(8),
    payment_method VARCHAR(30),
    transaction_status VARCHAR(16),
    device_id VARCHAR(32),
    high_amount_flag BOOLEAN,
    rapid_burst_flag BOOLEAN,
    repeated_failures_flag BOOLEAN,
    high_risk_country_flag BOOLEAN,
    risk_reasons TEXT,
    is_suspicious BOOLEAN,
    risk_rule_count INT,
    INDEX idx_customer_date (customer_id, transaction_date),
    INDEX idx_transaction_date (transaction_date)
);

CREATE TABLE IF NOT EXISTS suspicious_transactions LIKE transactions;
