"""Generate a reproducible fictional banking transaction dataset."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "raw" / "transactions.csv"

def generate_transactions(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    customers = [f"CUST{i:04d}" for i in range(1, 301)]
    start = pd.Timestamp("2025-01-01")
    seconds = rng.integers(0, 90 * 24 * 60 * 60, size=n)
    dates = start + pd.to_timedelta(seconds, unit="s")
    amounts = np.round(rng.lognormal(mean=3.5, sigma=1.0, size=n), 2)
    amounts = np.clip(amounts, 1, 12000)

    df = pd.DataFrame({
        "transaction_id": [f"TXN{i:07d}" for i in range(1, n + 1)],
        "customer_id": rng.choice(customers, n),
        "transaction_date": dates,
        "amount": amounts,
        "currency": "USD",
        "merchant_category": rng.choice(
            ["Grocery", "Fuel", "Travel", "Electronics", "Dining", "Utilities", "Shopping"],
            n, p=[.20, .12, .08, .10, .18, .12, .20]
        ),
        "country": rng.choice(["US", "IN", "GB", "CA", "AU", "XX", "YY"], n,
                              p=[.42, .22, .10, .08, .08, .05, .05]),
        "payment_method": rng.choice(["Card", "UPI", "Bank Transfer", "Wallet"], n),
        "transaction_status": rng.choice(["Success", "Failed"], n, p=[.94, .06]),
        "device_id": rng.choice([f"DEV{i:04d}" for i in range(1, 501)], n),
    })

    # Add deliberately suspicious patterns for demonstration.
    for j, offset in enumerate([0, 1, 2]):
        idx = 10 + j
        df.loc[idx, "customer_id"] = "CUST_RAPID"
        df.loc[idx, "transaction_date"] = pd.Timestamp("2025-02-10 10:00:00") + pd.Timedelta(minutes=offset)
        df.loc[idx, "amount"] = 75 + j * 10
    for idx in [20, 21, 22]:
        df.loc[idx, "customer_id"] = "CUST_FAILURE"
        df.loc[idx, "transaction_date"] = pd.Timestamp("2025-02-11 12:00:00") + pd.Timedelta(minutes=idx-20)
        df.loc[idx, "transaction_status"] = "Failed"
    df.loc[30, "amount"] = 8500
    df.loc[31, "country"] = "XX"

    # Data quality issues: one duplicate, one missing customer, one invalid amount.
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df.loc[40, "customer_id"] = None
    df["amount"] = df["amount"].astype(object)
    df.loc[41, "amount"] = "not-a-number"
    return df

if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generate_transactions().to_csv(OUTPUT, index=False)
    print(f"Generated {OUTPUT}")
