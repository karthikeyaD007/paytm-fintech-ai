"""
Four-layer payments/fraud analytics dashboard, built as saved chart images
(matplotlib) plus written interpretation -- no live BI tool required.

Reads paytm_payments.db and dashboard/reconciliation_summary.json (produced
by ../reconcile.py -- run that first).

Layers:
    HEADLINE   -> headline_scorecards.png
    TRENDS     -> trends_daily_gmv_chargebacks.png
    BREAKDOWN  -> breakdown_gmv_by_method_category.png
    DETAILS    -> details_top_merchants.png (saved table image, not a live DataFrame)

Written interpretations for each layer are in dashboard/README.md.

Run (from payments_fraud_analytics/):
    python dashboard/generate_dashboard.py
"""

import json
import os
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(ROOT, "paytm_payments.db")
RECON_SUMMARY_PATH = os.path.join(HERE, "reconciliation_summary.json")


def load_data():
    conn = sqlite3.connect(DB_PATH)
    txns = pd.read_sql("SELECT * FROM transactions", conn)
    merchants = pd.read_sql("SELECT * FROM merchants", conn)
    conn.close()
    txns["transaction_time"] = pd.to_datetime(txns["transaction_time"])
    txns["txn_date"] = txns["transaction_time"].dt.date
    return txns, merchants


def headline_layer(txns, recon_summary):
    total_gmv = txns.loc[txns["status"] == "captured", "amount_inr"].sum()
    success_rate = 100.0 * (txns["status"] == "captured").mean()
    match_rate = recon_summary["match_rate_pct"]
    chargeback_ratio = 100.0 * (txns["status"] == "chargeback").mean()

    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.axis("off")
    cards = [
        ("Total GMV", f"INR {total_gmv:,.0f}"),
        ("Success Rate", f"{success_rate:.2f}%"),
        ("Reconciliation Match Rate", f"{match_rate:.2f}%"),
        ("Chargeback Ratio", f"{chargeback_ratio:.2f}%"),
    ]
    for i, (label, value) in enumerate(cards):
        x = 0.02 + i * 0.245
        ax.add_patch(plt.Rectangle((x, 0.05), 0.22, 0.9, fill=True, facecolor="#eef3fb", edgecolor="#4a6fa5"))
        ax.text(x + 0.11, 0.65, value, ha="center", va="center", fontsize=15, fontweight="bold")
        ax.text(x + 0.11, 0.25, label, ha="center", va="center", fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.suptitle("Headline Scorecards", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "headline_scorecards.png"), dpi=140)
    plt.close(fig)

    return {
        "total_gmv_inr": float(total_gmv),
        "success_rate_pct": round(success_rate, 2),
        "match_rate_pct": match_rate,
        "chargeback_ratio_pct": round(chargeback_ratio, 2),
    }


def trends_layer(txns):
    daily = txns.groupby("txn_date").agg(
        gmv=("amount_inr", lambda s: s[txns.loc[s.index, "status"] == "captured"].sum()),
        chargebacks=("status", lambda s: (s == "chargeback").sum()),
    ).reset_index()

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(daily["txn_date"], daily["gmv"], marker="o", color="#2b6cb0")
    axes[0].set_title("Daily GMV (INR)")
    axes[0].set_ylabel("GMV (INR)")
    axes[0].grid(alpha=0.3)

    axes[1].plot(daily["txn_date"], daily["chargebacks"], marker="o", color="#c53030")
    axes[1].set_title("Daily Chargeback Count")
    axes[1].set_ylabel("Chargebacks")
    axes[1].set_xlabel("Date")
    axes[1].grid(alpha=0.3)
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "trends_daily_gmv_chargebacks.png"), dpi=140)
    plt.close(fig)

    return daily


def breakdown_layer(txns, merchants):
    gmv_method = txns.loc[txns["status"] == "captured"].groupby("payment_method")["amount_inr"].sum().sort_values(ascending=False)
    merged = txns.merge(merchants, on="merchant_id")
    gmv_category = merged.loc[merged["status"] == "captured"].groupby("category")["amount_inr"].sum().sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(gmv_method.index, gmv_method.values, color="#2b6cb0")
    axes[0].set_title("GMV by Payment Method")
    axes[0].set_ylabel("GMV (INR)")
    axes[0].tick_params(axis="x", rotation=30)

    axes[1].bar(gmv_category.index, gmv_category.values, color="#38a169")
    axes[1].set_title("GMV by Merchant Category")
    axes[1].tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "breakdown_gmv_by_method_category.png"), dpi=140)
    plt.close(fig)

    return gmv_method, gmv_category


def details_layer(txns, merchants):
    merged = txns.merge(merchants, on="merchant_id")
    stats = merged.groupby(["merchant_id", "merchant_name"]).agg(
        txn_count=("transaction_id", "count"),
        chargebacks=("status", lambda s: (s == "chargeback").sum()),
    ).reset_index()
    stats["chargeback_ratio_pct"] = round(100 * stats["chargebacks"] / stats["txn_count"], 2)
    stats["high_risk_flag"] = stats["chargeback_ratio_pct"].apply(lambda r: "HIGH RISK" if r > 1.0 else "")
    top10 = stats.sort_values("txn_count", ascending=False).head(10).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis("off")
    col_labels = ["Merchant ID", "Merchant Name", "Txn Count", "Chargebacks", "Chargeback %", "Flag"]
    cell_text = top10[["merchant_id", "merchant_name", "txn_count", "chargebacks", "chargeback_ratio_pct", "high_risk_flag"]].values.tolist()
    table = ax.table(cellText=cell_text, colLabels=col_labels, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    for row_idx, row in enumerate(top10.itertuples(), start=1):
        if row.high_risk_flag:
            for col_idx in range(len(col_labels)):
                table[(row_idx, col_idx)].set_facecolor("#fed7d7")

    ax.set_title("Top 10 Merchants by Transaction Count\n(flagged: chargeback ratio > 1%)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "details_top_merchants.png"), dpi=140)
    plt.close(fig)

    return top10


def main():
    if not os.path.exists(RECON_SUMMARY_PATH):
        raise SystemExit("Run reconcile.py first to produce dashboard/reconciliation_summary.json")

    with open(RECON_SUMMARY_PATH) as f:
        recon_summary = json.load(f)

    txns, merchants = load_data()

    headline = headline_layer(txns, recon_summary)
    daily = trends_layer(txns)
    gmv_method, gmv_category = breakdown_layer(txns, merchants)
    top10 = details_layer(txns, merchants)

    print("Headline:", headline)
    print("\nTop 10 merchants (details layer):")
    print(top10.to_string(index=False))
    print(f"\nHigh-risk merchants (chargeback ratio > 1%) among top 10: {(top10['high_risk_flag'] != '').sum()}")
    print(f"\nCharts saved to {HERE}")


if __name__ == "__main__":
    main()
