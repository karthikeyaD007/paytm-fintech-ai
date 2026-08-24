"""
Risk-based pricing: maps predicted probability of default (from the Logistic
Regression model) to a risk tier, then to an interest-rate range, and
compares actual default rates across tiers to validate monotonicity
(lower-risk tiers should show a lower actual default rate than
higher-risk tiers).

Tiers are quartiles of predicted default probability on the test set (4
equal-sized groups), as suggested by the spec. Interest-rate bands are
illustrative (not specified numerically in the brief):

    Q1 (lowest risk):  10% - 14% p.a.
    Q2:                14% - 18% p.a.
    Q3:                18% - 24% p.a.
    Q4 (highest risk): 24% - 32% p.a.

Run:
    python risk_pricing.py
"""

import os

import pandas as pd
from sklearn.linear_model import LogisticRegression

from preprocessing import preprocess_data

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
RANDOM_STATE = 42

TIER_LABELS = ["Q1 - Low Risk", "Q2 - Moderate Risk", "Q3 - Elevated Risk", "Q4 - High Risk"]
RATE_BANDS = {
    "Q1 - Low Risk": (0.10, 0.14),
    "Q2 - Moderate Risk": (0.14, 0.18),
    "Q3 - Elevated Risk": (0.18, 0.24),
    "Q4 - High Risk": (0.24, 0.32),
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    X_train, X_test, y_train, y_test, scaler, meta = preprocess_data()

    model = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
    model.fit(X_train, y_train)
    pd_scores = model.predict_proba(X_test)[:, 1]

    result = pd.DataFrame({
        "applicant_id": meta["applicant_ids_test"].values,
        "predicted_pd": pd_scores,
        "actual_default": y_test.values,
    })
    result["risk_tier"] = pd.qcut(result["predicted_pd"], 4, labels=TIER_LABELS)
    result["rate_range"] = result["risk_tier"].map(
        lambda t: f"{RATE_BANDS[t][0]*100:.0f}% - {RATE_BANDS[t][1]*100:.0f}%"
    )

    tier_summary = result.groupby("risk_tier", observed=True).agg(
        applicants=("applicant_id", "count"),
        avg_predicted_pd=("predicted_pd", "mean"),
        actual_default_rate=("actual_default", "mean"),
    ).reindex(TIER_LABELS)
    tier_summary["rate_range"] = tier_summary.index.map(
        lambda t: f"{RATE_BANDS[t][0]*100:.0f}% - {RATE_BANDS[t][1]*100:.0f}%"
    )

    is_monotonic = tier_summary["actual_default_rate"].is_monotonic_increasing

    print("Risk Tier Summary (test set, quartiles of predicted PD):")
    print(tier_summary.to_string())
    print(f"\nMonotonically increasing default rate across tiers: {is_monotonic}")

    result.to_csv(os.path.join(OUT_DIR, "risk_pricing_applicants.csv"), index=False)
    tier_summary.to_csv(os.path.join(OUT_DIR, "risk_pricing_tier_summary.csv"))

    print(f"\nOutputs written to {OUT_DIR}")
    return result, tier_summary


if __name__ == "__main__":
    main()
