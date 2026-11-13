"""Streamlit dashboard for the loaded banking analytics database."""
from pathlib import Path
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///" + str(ROOT / "banking_analytics.db"))

st.set_page_config(page_title="Banking Transaction & Risk Analytics", page_icon="🏦", layout="wide")
st.title("🏦 Banking Transaction ETL & Fraud Analytics")
st.caption("Educational demo using synthetic data and transparent screening rules — not a production fraud detector.")

try:
    engine = create_engine(DB_URL)
    df = pd.read_sql("SELECT * FROM transactions", engine, parse_dates=["transaction_date"])
    engine.dispose()
except Exception as exc:
    st.error(f"Could not read the database: {exc}")
    st.info("Generate data and run the ETL first: `python -m src.generate_data` then `python -m src.pipeline`.")
    st.stop()

if df.empty:
    st.warning("No transaction records found. Run the ETL pipeline first.")
    st.stop()

df["transaction_date"] = pd.to_datetime(df["transaction_date"])
suspicious = df[df["is_suspicious"].astype(str).str.lower().isin(["true", "1"])].copy()
total_value = df["amount"].sum()
suspicious_value = suspicious["amount"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", f"{len(df):,}")
c2.metric("Total transaction value", f"${total_value:,.2f}")
c3.metric("Flagged transactions", f"{len(suspicious):,}")
c4.metric("Flagged value", f"${suspicious_value:,.2f}")

st.subheader("Transaction trends")
daily = df.set_index("transaction_date").resample("D").agg(
    transaction_count=("transaction_id", "count"), transaction_value=("amount", "sum")
).reset_index()
left, right = st.columns(2)
left.plotly_chart(px.line(daily, x="transaction_date", y="transaction_count",
                          title="Daily transaction volume"), use_container_width=True)
right.plotly_chart(px.line(daily, x="transaction_date", y="transaction_value",
                           title="Daily transaction value"), use_container_width=True)

st.subheader("Suspicious activity")
left, right = st.columns(2)
if not suspicious.empty:
    reasons = suspicious["risk_reasons"].fillna("").str.split(",").explode()
    reasons = reasons[reasons.ne("")]
    left.plotly_chart(px.bar(reasons.value_counts().reset_index(name="count"),
                             x="risk_reasons", y="count", title="Flags by rule"),
                      use_container_width=True)
    right.plotly_chart(px.histogram(suspicious, x="amount", nbins=30,
                                    title="Amount distribution of flagged transactions"),
                       use_container_width=True)
else:
    left.info("No transactions were flagged in this dataset.")
    right.info("No flagged transaction amounts to display.")

st.subheader("Transaction filters")
countries = sorted(df["country"].dropna().unique().tolist())
selected_countries = st.multiselect("Country", countries, default=countries)
status_options = sorted(df["transaction_status"].dropna().unique().tolist())
selected_status = st.multiselect("Status", status_options, default=status_options)
filtered = df[df["country"].isin(selected_countries) & df["transaction_status"].isin(selected_status)]
st.dataframe(filtered.sort_values("transaction_date", ascending=False), use_container_width=True, hide_index=True)

st.subheader("Flagged transactions")
if not suspicious.empty:
    st.dataframe(suspicious.sort_values("risk_rule_count", ascending=False),
                 use_container_width=True, hide_index=True)
    st.download_button("Download flagged transactions CSV",
                       suspicious.to_csv(index=False).encode("utf-8"),
                       file_name="suspicious_transactions.csv", mime="text/csv")
