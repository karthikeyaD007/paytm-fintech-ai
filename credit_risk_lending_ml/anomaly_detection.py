"""
Isolation Forest anomaly detection on txn_behaviour.csv.

Pipeline: StandardScaler -> IsolationForest, with contamination set to the
known seeded-anomaly proportion (15 / 265). This is an anomaly-recall task,
not a normal classification-accuracy problem: we report how many of the 15
seeded anomalies (txn_id starting with "BTXNA") were flagged.

Run:
    python anomaly_detection.py
"""

import os
import json

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
RANDOM_STATE = 42

FEATURES = ["txn_hour", "is_new_device", "txn_amount_inr"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(os.path.join(HERE, "txn_behaviour.csv"))
    df = pd.get_dummies(df, columns=["channel"], drop_first=True)
    feature_cols = FEATURES + [c for c in df.columns if c.startswith("channel_")]

    n_total = len(df)
    n_seeded_anomalies = df["txn_id"].str.startswith("BTXNA").sum()
    contamination = n_seeded_anomalies / n_total

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])

    iso = IsolationForest(contamination=contamination, random_state=RANDOM_STATE)
    df["anomaly_pred"] = iso.fit_predict(X_scaled)  # -1 = anomaly, 1 = normal
    df["is_anomaly_predicted"] = (df["anomaly_pred"] == -1).astype(int)
    df["is_seeded_anomaly"] = df["txn_id"].str.startswith("BTXNA").astype(int)

    detected = df.loc[(df["is_seeded_anomaly"] == 1) & (df["is_anomaly_predicted"] == 1)]
    anomaly_recall = len(detected) / n_seeded_anomalies

    false_positives = df.loc[(df["is_seeded_anomaly"] == 0) & (df["is_anomaly_predicted"] == 1)]

    print(f"Total transactions: {n_total}")
    print(f"Seeded anomalies: {n_seeded_anomalies}")
    print(f"Contamination rate used: {contamination:.4f}")
    print(f"Flagged as anomaly by Isolation Forest: {df['is_anomaly_predicted'].sum()}")
    print(f"Seeded anomalies detected: {len(detected)} / {n_seeded_anomalies}")
    print(f"Anomaly recall: {anomaly_recall:.4f}")
    print(f"False positives (flagged but not seeded anomaly): {len(false_positives)}")

    df.to_csv(os.path.join(OUT_DIR, "anomaly_detection_results.csv"), index=False)
    with open(os.path.join(OUT_DIR, "anomaly_detection_summary.json"), "w") as f:
        json.dump({
            "n_total": int(n_total),
            "n_seeded_anomalies": int(n_seeded_anomalies),
            "contamination_used": contamination,
            "n_flagged": int(df["is_anomaly_predicted"].sum()),
            "n_seeded_detected": int(len(detected)),
            "anomaly_recall": anomaly_recall,
            "n_false_positives": int(len(false_positives)),
        }, f, indent=2)

    print(f"\nOutputs written to {OUT_DIR}")
    return df, anomaly_recall


if __name__ == "__main__":
    main()
