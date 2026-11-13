# Banking Transaction ETL & Fraud Analytics

An entry-level, end-to-end data engineering project that ingests synthetic banking transactions, validates and transforms them with Python/Pandas, loads analytical tables into SQLite (or MySQL), applies transparent rule-based suspicious-activity checks, and provides a Streamlit dashboard.

> **Important:** This is an educational portfolio project. The data is synthetic and the rules flag *potentially suspicious transactions*; they do not prove fraud and are not a production banking fraud system.

## What this project demonstrates

- ETL: extract CSV data, validate and transform records, load a relational database.
- Data quality: required-field checks, type conversion, invalid-record quarantine, duplicate removal.
- SQL analytics: aggregations, CTEs, joins and window functions.
- Rule-based risk screening: high-value transactions, rapid transaction bursts, repeated failed attempts and high-risk countries.
- Reporting: CSV outputs and an interactive Streamlit dashboard.
- Basic testing and reproducible setup.

## Architecture

```text
Synthetic CSV source
       |
       v
Python + Pandas ETL
  - validate / standardize
  - quarantine invalid rows
  - deduplicate
  - derive transaction features
       |
       v
Rule-based suspicious activity checks
       |
       v
SQLite database (default) / MySQL (optional)
       |
       +----> SQL analytics queries
       |
       +----> Streamlit dashboard
       |
       +----> CSV reports
```

## Repository structure

```text
banking-transaction-etl-fraud-analytics/
├── data/
│   ├── raw/                 # Generated input CSV
│   └── processed/           # ETL output CSVs
├── reports/                 # Generated summary report
├── sql/
│   ├── schema_mysql.sql     # MySQL table definitions
│   └── analytics.sql        # Example analytical queries
├── src/
│   ├── __init__.py
│   ├── generate_data.py     # Reproducible synthetic data generator
│   ├── pipeline.py          # Extract, transform, flag, load
│   └── dashboard.py         # Streamlit dashboard
├── tests/
│   └── test_pipeline.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Quick start (SQLite — no database server required)

Python 3.10+ is recommended.

### 1. Create and activate a virtual environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate the sample dataset

```bash
python -m src.generate_data
```

This creates `data/raw/transactions.csv` with deterministic, fictional records.

### 4. Run the ETL pipeline

```bash
python -m src.pipeline
```

The pipeline creates `banking_analytics.db` and writes:
- `data/processed/cleaned_transactions.csv`
- `data/processed/suspicious_transactions.csv`
- `data/processed/rejected_transactions.csv`
- `reports/pipeline_summary.json`

### 5. Launch the dashboard

```bash
streamlit run src/dashboard.py
```

The dashboard reads the database created by the pipeline. Run the ETL step first.

### 6. Run tests

```bash
pytest -q
```

## Optional: use MySQL

1. Create a database:
   ```sql
   CREATE DATABASE banking_analytics;
   ```
2. Copy `.env.example` to `.env` and set:
   ```env
   DATABASE_URL=mysql+mysqlconnector://YOUR_USER:YOUR_PASSWORD@localhost:3306/banking_analytics
   ```
3. Install dependencies (the MySQL driver is already listed):
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python -m src.pipeline
   ```

The pipeline uses SQLAlchemy and creates the required tables automatically. `sql/schema_mysql.sql` is also supplied as a reference schema. Do not commit your `.env` file or database credentials.

## Data dictionary

| Column | Meaning |
|---|---|
| transaction_id | Unique transaction identifier |
| customer_id | Fictional customer identifier |
| transaction_date | Transaction timestamp (UTC-naive in this sample) |
| amount | Transaction amount in USD |
| currency | Currency code |
| merchant_category | Merchant category |
| country | Country where transaction originated |
| payment_method | Card, UPI, bank transfer or wallet |
| transaction_status | Success or Failed |
| device_id | Fictional device identifier |

The generator intentionally includes a small number of duplicates, missing values and suspicious-looking patterns so that data quality and screening logic can be demonstrated.

## Suspicious activity rules

A transaction is flagged when one or more rules match:

1. **HIGH_AMOUNT** — amount is greater than or equal to USD 5,000.
2. **RAPID_BURST** — the customer has at least 3 transactions within a rolling 5-minute window.
3. **REPEATED_FAILURES** — the customer has at least 3 failed transactions in the preceding 24 hours (including the current row).
4. **HIGH_RISK_COUNTRY** — transaction country is in the illustrative configured list (`XX`, `YY`).

These are intentionally simple demonstration rules. Thresholds and country codes are configurable in `src/pipeline.py`; the country codes are fictional placeholders, not a real-world risk list.

## Database tables

- `transactions`: one row per valid, deduplicated transaction, including rule flags.
- `suspicious_transactions`: only rows flagged by at least one rule.

## Example SQL analysis

Open `sql/analytics.sql` for queries covering:
- daily transaction volume and value
- suspicious transaction rate
- top customers by transaction value
- suspicious activity by rule
- transaction ranking by customer

## Suggested GitHub description

**Banking Transaction ETL & Fraud Analytics | Python, Pandas, SQL, MySQL, Streamlit**

Built an end-to-end ETL pipeline to validate, clean, deduplicate and load synthetic banking transaction data into a relational database. Implemented explainable rule-based screening for potentially suspicious activity and created a Streamlit dashboard for transaction and risk analytics.

## Good interview explanation

"I generated a reproducible synthetic transaction dataset, extracted it from CSV using Pandas, validated required fields and data types, quarantined invalid rows, removed duplicate transaction IDs, and derived rule-based risk indicators. I then loaded the cleaned data into a relational database and used SQL and a Streamlit dashboard to analyse transaction trends and suspicious activity."

Be ready to explain each rule, its limitations, and how you would improve the pipeline with incremental loads, orchestration, logging, data tests, cloud storage and scalable processing.
