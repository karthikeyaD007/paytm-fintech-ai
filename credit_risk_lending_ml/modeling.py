"""
Trains the two required credit-risk classifiers (Logistic Regression, Decision
Tree) on the SAME preprocessed train/test split and reports accuracy,
precision, recall, F1, ROC-AUC, confusion matrix and ROC curve for each.

Run:
    python modeling.py
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix,
)

from preprocessing import preprocess_data

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
RANDOM_STATE = 42


def evaluate_model(name, model, X_test, y_test, y_prob):
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n--- {name} ---")
    for k, v in metrics.items():
        print(f"{k:12s}: {v:.4f}")
    print("Confusion matrix [[TN FP][FN TP]]:")
    print(cm)
    return metrics, cm


def plot_roc_curves(results, X_test, y_test):
    plt.figure(figsize=(6, 6))
    for name, r in results.items():
        fpr, tpr, _ = roc_curve(y_test, r["y_prob"])
        plt.plot(fpr, tpr, label=f"{name} (AUC={r['metrics']['roc_auc']:.3f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves -- Logistic Regression vs Decision Tree")
    plt.legend()
    plt.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    plt.savefig(os.path.join(OUT_DIR, "roc_curves.png"), dpi=120)
    plt.close()


def plot_confusion_matrix(name, cm, filename):
    plt.figure(figsize=(4, 4))
    plt.imshow(cm, cmap="Blues")
    plt.title(f"Confusion Matrix -- {name}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.xticks([0, 1], ["No Default", "Default"])
    plt.yticks([0, 1], ["No Default", "Default"])
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, filename), dpi=120)
    plt.close()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    X_train, X_test, y_train, y_test, scaler, meta = preprocess_data()

    log_reg = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
    log_reg.fit(X_train, y_train)
    log_reg_prob = log_reg.predict_proba(X_test)[:, 1]

    dtree = DecisionTreeClassifier(random_state=RANDOM_STATE)
    dtree.fit(X_train, y_train)
    dtree_prob = dtree.predict_proba(X_test)[:, 1]

    results = {}
    for name, model, y_prob in [
        ("Logistic Regression", log_reg, log_reg_prob),
        ("Decision Tree", dtree, dtree_prob),
    ]:
        metrics, cm = evaluate_model(name, model, X_test, y_test, y_prob)
        results[name] = {"metrics": metrics, "cm": cm, "y_prob": y_prob}

    plot_roc_curves(results, X_test, y_test)
    plot_confusion_matrix("Logistic Regression", results["Logistic Regression"]["cm"], "confusion_matrix_logreg.png")
    plot_confusion_matrix("Decision Tree", results["Decision Tree"]["cm"], "confusion_matrix_dtree.png")

    metrics_out = {name: r["metrics"] for name, r in results.items()}
    with open(os.path.join(OUT_DIR, "model_metrics.json"), "w") as f:
        json.dump(metrics_out, f, indent=2)

    print(f"\nOutputs written to {OUT_DIR}")

    return log_reg, dtree, X_train, X_test, y_train, y_test, results, meta


if __name__ == "__main__":
    main()
