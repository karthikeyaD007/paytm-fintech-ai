"""
Payment reconciliation: compares ledger.csv (source of truth) against
gateway_export.csv (deliberately corrupted export) and reports discrepancies.

reconcile_payments(ledger_df, gateway_df) uses set operations on
transaction_id (for missing/extra rows) and pd.merge (for the pairwise
amount/status comparison), and returns four DataFrames:
    missing_in_gateway   -- full ledger rows whose transaction_id has no
                             matching row in the gateway export
    missing_in_ledger    -- full gateway rows whose transaction_id has no
                             matching row in the ledger ("extra in gateway")
    amount_mismatches    -- rows present in both, with differing amount_inr
                             (includes the computed amount_diff)
    status_mismatches    -- rows present in both, with differing status

Run:
    python reconcile.py
"""

import os
import json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def reconcile_payments(ledger_df, gateway_df):
    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    missing_in_gateway_ids = ledger_ids - gateway_ids
    missing_in_ledger_ids = gateway_ids - ledger_ids

    missing_in_gateway = (
        ledger_df[ledger_df["transaction_id"].isin(missing_in_gateway_ids)]
        .sort_values("transaction_id").reset_index(drop=True)
    )
    missing_in_ledger = (
        gateway_df[gateway_df["transaction_id"].isin(missing_in_ledger_ids)]
        .sort_values("transaction_id").reset_index(drop=True)
    )

    common = pd.merge(ledger_df, gateway_df, on="transaction_id", suffixes=("_ledger", "_gateway"))

    amount_mismatches = common[common["amount_inr_ledger"] != common["amount_inr_gateway"]].copy()
    amount_mismatches["amount_diff"] = (
        amount_mismatches["amount_inr_gateway"] - amount_mismatches["amount_inr_ledger"]
    )
    amount_mismatches = amount_mismatches[
        ["transaction_id", "amount_inr_ledger", "amount_inr_gateway", "amount_diff"]
    ].sort_values("transaction_id").reset_index(drop=True)

    status_mismatches = common[common["status_ledger"] != common["status_gateway"]][
        ["transaction_id", "status_ledger", "status_gateway"]
    ].sort_values("transaction_id").reset_index(drop=True)

    return missing_in_gateway, missing_in_ledger, amount_mismatches, status_mismatches


def compute_headline_match_rate(ledger_df, gateway_df):
    """
    match_rate = (# transactions present in BOTH files with identical
    amount_inr AND identical status) / (total transaction count in ledger).
    Amount mismatches, status mismatches, and rows missing from either file
    all count as NOT matched.
    """
    common = pd.merge(ledger_df, gateway_df, on="transaction_id", suffixes=("_ledger", "_gateway"))
    fully_matched = common[
        (common["amount_inr_ledger"] == common["amount_inr_gateway"])
        & (common["status_ledger"] == common["status_gateway"])
    ]
    return 100.0 * len(fully_matched) / len(ledger_df)


def main():
    ledger_df = pd.read_csv(os.path.join(HERE, "ledger.csv"))
    gateway_df = pd.read_csv(os.path.join(HERE, "gateway_export.csv"))

    missing_in_gateway, missing_in_ledger, amount_mismatches, status_mismatches = reconcile_payments(
        ledger_df, gateway_df
    )
    match_rate_pct = compute_headline_match_rate(ledger_df, gateway_df)

    summary = {
        "ledger_rows": len(ledger_df),
        "gateway_rows": len(gateway_df),
        "missing_in_gateway_count": len(missing_in_gateway),
        "missing_in_ledger_count": len(missing_in_ledger),
        "amount_mismatch_count": len(amount_mismatches),
        "status_mismatch_count": len(status_mismatches),
        "match_rate_pct": round(match_rate_pct, 2),
    }

    print("=" * 60)
    print("PAYMENT RECONCILIATION REPORT")
    print("=" * 60)
    for k, v in summary.items():
        print(f"{k:30s}: {v}")

    print(f"\nInjection-rate check (expected ~5%/~3%/~2%/~2% of {len(ledger_df)} ledger rows):")
    n = len(ledger_df)
    print(f"  missing_in_gateway: {len(missing_in_gateway)} ({100*len(missing_in_gateway)/n:.1f}%, expected ~5%)")
    print(f"  amount_mismatches:  {len(amount_mismatches)} ({100*len(amount_mismatches)/n:.1f}%, expected ~3%)")
    print(f"  missing_in_ledger:  {len(missing_in_ledger)} ({100*len(missing_in_ledger)/n:.1f}%, expected ~2%)")
    print(f"  status_mismatches:  {len(status_mismatches)} ({100*len(status_mismatches)/n:.1f}%, expected ~2%)")

    print("\n--- Missing in gateway (sample, up to 10) ---")
    print(missing_in_gateway.head(10).to_string(index=False))

    print("\n--- Missing in ledger / extra in gateway (sample, up to 10) ---")
    print(missing_in_ledger.head(10).to_string(index=False))

    print("\n--- Amount mismatches (sample) ---")
    print(amount_mismatches.head(10).to_string(index=False))

    print("\n--- Status mismatches (sample) ---")
    print(status_mismatches.head(10).to_string(index=False))

    out_dir = os.path.join(HERE, "dashboard")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "reconciliation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    missing_in_gateway.to_csv(os.path.join(out_dir, "reconciliation_missing_in_gateway.csv"), index=False)
    missing_in_ledger.to_csv(os.path.join(out_dir, "reconciliation_missing_in_ledger.csv"), index=False)
    amount_mismatches.to_csv(os.path.join(out_dir, "reconciliation_amount_mismatches.csv"), index=False)
    status_mismatches.to_csv(os.path.join(out_dir, "reconciliation_status_mismatches.csv"), index=False)

    print(f"\nReports written to {out_dir}")

    return missing_in_gateway, missing_in_ledger, amount_mismatches, status_mismatches, summary


if __name__ == "__main__":
    main()
