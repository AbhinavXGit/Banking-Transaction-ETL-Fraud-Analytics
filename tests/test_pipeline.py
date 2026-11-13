import pandas as pd
from src.generate_data import generate_transactions
from src.pipeline import transform

def test_transform_removes_duplicate_and_rejects_invalid_rows():
    raw = generate_transactions(n=100, seed=7)
    clean, rejected = transform(raw)
    assert clean["transaction_id"].is_unique
    assert len(rejected) >= 2
    assert clean["amount"].gt(0).all()

def test_suspicious_flags_are_boolean():
    raw = generate_transactions(n=100, seed=7)
    clean, _ = transform(raw)
    assert clean["is_suspicious"].dtype == bool
    assert clean["risk_rule_count"].ge(0).all()

def test_known_high_amount_transaction_is_flagged():
    raw = generate_transactions(n=100, seed=7)
    clean, _ = transform(raw)
    row = clean.loc[clean["transaction_id"] == "TXN0000031"]
    assert not row.empty
    assert bool(row.iloc[0]["high_amount_flag"])
