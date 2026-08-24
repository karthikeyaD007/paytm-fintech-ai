"""
Payments & Fraud Analytics dashboard.

Run from the payments_fraud_analytics/ directory:
    streamlit run dashboard/app.py

Reads directly from paytm_payments.db and the reconciliation report
(dashboard/reconciliation_summary.json, produced by ../reconcile.py).
"""

import json
import os
import sqlite3

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(ROOT, "paytm_payments.db")
RECON_SUMMARY_PATH = os.path.join(HERE, "reconciliation_summary.json")

st.set_page_config(page_title="Paytm Payments & Fraud Analytics", layout="wide")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    transactions = pd.read_sql("SELECT * FROM transactions", conn)
    merchants = pd.read_sql("SELECT * FROM merchants", conn)
    users = pd.read_sql("SELECT * FROM users", conn)
    conn.close()
    transactions["transaction_time"] = pd.to_datetime(transactions["transaction_time"])
    transactions["txn_date"] = transactions["transaction_time"].dt.date
    return transactions, merchants, users


def load_reconciliation():
    if os.path.exists(RECON_SUMMARY_PATH):
        with open(RECON_SUMMARY_PATH) as f:
            return json.load(f)
    return None


txns, merchants, users = load_data()
recon = load_reconciliation()

st.title("Paytm-style Payments & Fraud Analytics Dashboard")

# ---------------------------------------------------------------------------
# HEADLINE
# ---------------------------------------------------------------------------
st.header("Headline Metrics")

total_gmv = txns.loc[txns["status"] == "captured", "amount_inr"].sum()
success_rate = 100.0 * (txns["status"] == "captured").mean()
chargeback_ratio = 100.0 * (txns["status"] == "chargeback").mean()
recon_match_rate = recon["match_rate_pct"] if recon else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total GMV (captured)", f"₹{total_gmv:,.0f}")
c2.metric("Success Rate", f"{success_rate:.2f}%")
c3.metric("Reconciliation Match Rate", f"{recon_match_rate:.2f}%" if recon_match_rate is not None else "N/A (run reconcile.py)")
c4.metric("Chargeback Ratio", f"{chargeback_ratio:.2f}%")

st.caption(
    f"Interpretation: {len(txns)} total ledger transactions, {success_rate:.1f}% captured successfully. "
    f"Chargeback ratio of {chargeback_ratio:.2f}% is elevated versus a typical <1% healthy baseline, "
    "driven by the seeded burner-account and velocity-attack fraud patterns in this dataset."
)

st.divider()

# ---------------------------------------------------------------------------
# TRENDS
# ---------------------------------------------------------------------------
st.header("Trends")

daily = txns.groupby("txn_date").agg(
    gmv=("amount_inr", lambda s: s[txns.loc[s.index, "status"] == "captured"].sum()),
    chargebacks=("status", lambda s: (s == "chargeback").sum()),
    txn_count=("transaction_id", "count"),
).reset_index()

tcol1, tcol2 = st.columns(2)
with tcol1:
    st.subheader("Daily GMV")
    st.line_chart(daily.set_index("txn_date")["gmv"])
with tcol2:
    st.subheader("Daily Chargeback Count")
    st.line_chart(daily.set_index("txn_date")["chargebacks"])

peak_chargeback_day = daily.loc[daily["chargebacks"].idxmax(), "txn_date"]
st.caption(
    f"Interpretation: GMV fluctuates day to day with no strong weekly seasonality over this 30-day window "
    f"(synthetic, uniformly-random dates). Chargebacks peak on {peak_chargeback_day} "
    f"({int(daily['chargebacks'].max())} chargebacks), consistent with clustered burner-account fraud."
)

st.divider()

# ---------------------------------------------------------------------------
# BREAKDOWN
# ---------------------------------------------------------------------------
st.header("Breakdown")

bcol1, bcol2 = st.columns(2)
with bcol1:
    st.subheader("GMV by Payment Method")
    gmv_method = txns.loc[txns["status"] == "captured"].groupby("payment_method")["amount_inr"].sum().sort_values(ascending=False)
    st.bar_chart(gmv_method)
with bcol2:
    st.subheader("GMV by Merchant Category")
    merged = txns.merge(merchants, on="merchant_id")
    gmv_category = merged.loc[merged["status"] == "captured"].groupby("category")["amount_inr"].sum().sort_values(ascending=False)
    st.bar_chart(gmv_category)

st.subheader("Chargeback Rate by Payment Method")
method_stats = txns.groupby("payment_method").agg(
    total=("transaction_id", "count"),
    chargebacks=("status", lambda s: (s == "chargeback").sum()),
)
method_stats["chargeback_rate_pct"] = round(100 * method_stats["chargebacks"] / method_stats["total"], 2)
st.dataframe(method_stats.sort_values("chargeback_rate_pct", ascending=False), use_container_width=True)

st.caption(
    "Interpretation: UPI carries the highest transaction volume (reflecting its ~55% weight in the "
    "underlying data), while Card shows a disproportionately higher chargeback rate — expected, since all "
    "15 injected burner-account frauds and all 8 velocity-attack clusters were seeded specifically on Card transactions."
)

st.divider()

# ---------------------------------------------------------------------------
# DETAILS
# ---------------------------------------------------------------------------
st.header("Details")

st.subheader("Top 10 Merchants by GMV")
merchant_gmv = merged.loc[merged["status"] == "captured"].groupby(
    ["merchant_id", "merchant_name", "category"]
)["amount_inr"].sum().sort_values(ascending=False).head(10).reset_index()
st.dataframe(merchant_gmv, use_container_width=True)

st.subheader("Merchant-level Fraud / Chargeback Detail")
merchant_fraud = merged.groupby(["merchant_id", "merchant_name", "category"]).agg(
    total_txns=("transaction_id", "count"),
    chargebacks=("status", lambda s: (s == "chargeback").sum()),
    avg_risk_score=("risk_score", "mean"),
).reset_index()
merchant_fraud["chargeback_rate_pct"] = round(100 * merchant_fraud["chargebacks"] / merchant_fraud["total_txns"], 2)
merchant_fraud = merchant_fraud.sort_values("chargeback_rate_pct", ascending=False)
st.dataframe(merchant_fraud.head(15), use_container_width=True)

st.subheader("Burner-Account Fraud Transactions")
users_local = users.copy()
users_local["signup_date"] = pd.to_datetime(users_local["signup_date"])
txn_user = txns.merge(users_local, on="user_id")
txn_user["account_age_days"] = (txn_user["transaction_time"] - txn_user["signup_date"]).dt.days
burner = txn_user.loc[(txn_user["status"] == "chargeback") & (txn_user["account_age_days"] < 30)]
st.dataframe(
    burner[["transaction_id", "user_id", "account_age_days", "amount_inr", "risk_score", "transaction_time"]]
    .sort_values("account_age_days"),
    use_container_width=True,
)

if recon:
    st.subheader("Reconciliation Discrepancy Summary")
    st.json(recon)

st.caption(
    f"Interpretation: {len(burner)} chargeback transactions are tied to accounts less than 30 days old, "
    "matching the 15 seeded burner-account frauds. These accounts should be prioritized for manual review "
    "and additional KYC verification before further transactions are approved."
)
