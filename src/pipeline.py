"""ETL pipeline: extract, validate, transform, flag, and load."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Tuple

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "transactions.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_FILE = ROOT / "reports" / "pipeline_summary.json"

REQUIRED = [
    "transaction_id", "customer_id", "transaction_date", "amount", "currency",
    "merchant_category", "country", "payment_method", "transaction_status", "device_id"
]
HIGH_AMOUNT_THRESHOLD = 5000.0
RAPID_WINDOW = "5min"
RAPID_COUNT = 3
FAILURE_WINDOW = "24h"
FAILURE_COUNT = 3
# Fictional placeholders used only to demonstrate configurable rule logic.
HIGH_RISK_COUNTRIES = {"XX", "YY"}

def extract(path: Path = RAW_FILE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}. Run `python -m src.generate_data` first.")
    return pd.read_csv(path)

def transform(raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    missing_cols = sorted(set(REQUIRED) - set(raw.columns))
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = raw[REQUIRED].copy()
    df["transaction_id"] = df["transaction_id"].astype("string").str.strip()
    df["customer_id"] = df["customer_id"].astype("string").str.strip()
    df["country"] = df["country"].astype("string").str.strip().str.upper()
    df["transaction_status"] = df["transaction_status"].astype("string").str.strip().str.title()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    invalid = (
        df["transaction_id"].isna() | df["transaction_id"].eq("") |
        df["customer_id"].isna() | df["customer_id"].eq("") |
        df["transaction_date"].isna() | df["amount"].isna() |
        (df["amount"] <= 0) |
        ~df["transaction_status"].isin(["Success", "Failed"])
    )
    rejected = df.loc[invalid].copy()
    rejected["rejection_reason"] = "Missing/invalid required field, amount, date, or status"
    valid = df.loc[~invalid].copy()

    # Keep the first occurrence of each transaction ID.
    valid = valid.drop_duplicates(subset=["transaction_id"], keep="first")
    valid = valid.sort_values(["customer_id", "transaction_date", "transaction_id"]).reset_index(drop=True)

    # Calculate rolling rule indicators per customer.
    valid["high_amount_flag"] = valid["amount"] >= HIGH_AMOUNT_THRESHOLD
    valid["high_risk_country_flag"] = valid["country"].isin(HIGH_RISK_COUNTRIES)

    valid["rapid_burst_flag"] = False
    valid["repeated_failures_flag"] = False
    for _, group in valid.groupby("customer_id", sort=False):
        times = group["transaction_date"]
        # For each transaction, count events in the trailing 5-minute window.
        counts = pd.Series(1, index=group.index).rolling(
            RAPID_WINDOW, on=None
        ) if False else None
        time_indexed = pd.Series(1, index=pd.DatetimeIndex(times))
        rapid_counts = time_indexed.rolling(RAPID_WINDOW).sum()
        valid.loc[group.index, "rapid_burst_flag"] = rapid_counts.to_numpy() >= RAPID_COUNT

        failed = group["transaction_status"].eq("Failed").astype(int)
        failed_series = pd.Series(failed.to_numpy(), index=pd.DatetimeIndex(times))
        failure_counts = failed_series.rolling(FAILURE_WINDOW).sum()
        valid.loc[group.index, "repeated_failures_flag"] = (
            (failure_counts.to_numpy() >= FAILURE_COUNT) & failed.to_numpy().astype(bool)
        )

    flag_cols = ["high_amount_flag", "rapid_burst_flag",
                 "repeated_failures_flag", "high_risk_country_flag"]
    valid["risk_reasons"] = valid.apply(
        lambda row: ",".join(
            name.replace("_flag", "").upper()
            for name in flag_cols if bool(row[name])
        ), axis=1
    )
    valid["is_suspicious"] = valid[flag_cols].any(axis=1)
    valid["risk_rule_count"] = valid[flag_cols].sum(axis=1).astype(int)
    return valid, rejected

def load_to_database(clean: pd.DataFrame, database_url: str) -> None:
    engine = create_engine(database_url)
    clean.to_sql("transactions", engine, if_exists="replace", index=False, method="multi", chunksize=500)
    suspicious = clean.loc[clean["is_suspicious"]].copy()
    suspicious.to_sql("suspicious_transactions", engine, if_exists="replace",
                      index=False, method="multi", chunksize=500)
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_customer ON transactions (customer_id)")) if database_url.startswith("sqlite") else None
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transactions_date ON transactions (transaction_date)")) if database_url.startswith("sqlite") else None
    engine.dispose()

def run_pipeline() -> dict:
    load_dotenv(ROOT / ".env")
    database_url = os.getenv("DATABASE_URL", "sqlite:///" + str(ROOT / "banking_analytics.db"))
    raw = extract()
    clean, rejected = transform(raw)
    suspicious = clean.loc[clean["is_suspicious"]].copy()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    clean.to_csv(PROCESSED_DIR / "cleaned_transactions.csv", index=False)
    suspicious.to_csv(PROCESSED_DIR / "suspicious_transactions.csv", index=False)
    rejected.to_csv(PROCESSED_DIR / "rejected_transactions.csv", index=False)
    load_to_database(clean, database_url)

    summary = {
        "source_rows": int(len(raw)),
        "clean_rows": int(len(clean)),
        "rejected_rows": int(len(rejected)),
        "suspicious_rows": int(len(suspicious)),
        "duplicate_rows_removed": int(len(raw) - len(rejected) - len(clean)),
        "suspicious_rate_percent": round(float(len(suspicious) / max(len(clean), 1) * 100), 2),
        "database_url": database_url.split("@")[-1] if "@" in database_url else database_url,
    }
    REPORT_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
