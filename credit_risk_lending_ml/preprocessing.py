"""
Reproducible preprocessing pipeline for credit_applicants.csv.

Train/test split happens FIRST. The bureau-score median used for imputation
is computed ONLY from the training split, then applied to both train and
test, to avoid data leakage.
"""

import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "age",
    "monthly_income_inr",
    "existing_loans_count",
    "credit_utilization_ratio",
    "upi_monthly_inflow_inr",
    "bounced_payments_count",
    "credit_bureau_score",
]
CATEGORICAL_FEATURES = ["employment_type"]
TARGET = "default"


def load_raw(path=None):
    path = path or os.path.join(HERE, "credit_applicants.csv")
    return pd.read_csv(path)


def preprocess_data(df=None, test_size=0.25, random_state=RANDOM_STATE):
    """
    Returns X_train, X_test, y_train, y_test (all DataFrames/Series),
    plus the list of final feature column names and the fitted StandardScaler.
    """
    if df is None:
        df = load_raw()
    df = df.copy()

    # is_thin_file flag: applicants with no bureau score at all.
    # Derived purely from missingness, not from the (unknown) score value,
    # so this is safe to compute before the split.
    df["is_thin_file"] = df["credit_bureau_score"].isna().astype(int)

    df = pd.get_dummies(df, columns=CATEGORICAL_FEATURES, drop_first=True)

    dummy_cols = [c for c in df.columns if c.startswith("employment_type_")]
    feature_cols = NUMERIC_FEATURES + ["is_thin_file"] + dummy_cols

    X = df[feature_cols + ["applicant_id"]].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Bureau-score median computed from TRAINING data only.
    train_median = X_train["credit_bureau_score"].median()
    X_train = X_train.copy()
    X_test = X_test.copy()
    X_train["credit_bureau_score"] = X_train["credit_bureau_score"].fillna(train_median)
    X_test["credit_bureau_score"] = X_test["credit_bureau_score"].fillna(train_median)

    applicant_ids_train = X_train.pop("applicant_id")
    applicant_ids_test = X_test.pop("applicant_id")

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train[feature_cols]), columns=feature_cols, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test[feature_cols]), columns=feature_cols, index=X_test.index
    )

    meta = {
        "train_median_bureau_score": train_median,
        "feature_cols": feature_cols,
        "applicant_ids_train": applicant_ids_train,
        "applicant_ids_test": applicant_ids_test,
        "X_train_raw": X_train,
        "X_test_raw": X_test,
    }

    return X_train_scaled, X_test_scaled, y_train.reset_index(drop=True), y_test.reset_index(drop=True), scaler, meta


if __name__ == "__main__":
    X_train, X_test, y_train, y_test, scaler, meta = preprocess_data()
    print(f"Train rows: {len(X_train)}, Test rows: {len(X_test)}")
    print(f"Train default rate: {y_train.mean():.4f}, Test default rate: {y_test.mean():.4f}")
    print(f"Train-only bureau-score median used for imputation: {meta['train_median_bureau_score']:.1f}")
    print(f"Thin-file count -- train: {int(meta['X_train_raw']['is_thin_file'].sum())}, "
          f"test: {int(meta['X_test_raw']['is_thin_file'].sum())}")
    print(f"Feature columns: {meta['feature_cols']}")
