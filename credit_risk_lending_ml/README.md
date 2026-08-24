# Part 2 — Credit Risk & Lending ML

## Setup / run

```bash
cd credit_risk_lending_ml
python generate_data.py      # -> credit_applicants.csv, txn_behaviour.csv
python preprocessing.py      # prints EDA stats + leakage-safe split sanity check
python modeling.py           # trains both classifiers -> outputs/
python risk_pricing.py       # PD -> risk tier -> rate band -> outputs/
python anomaly_detection.py  # Isolation Forest -> outputs/
```

## EDA summary (measured, from the committed `credit_applicants.csv`)

- 400 applicant rows; measured default rate **20.25%** (within the required
  15–25% range).
- Exactly **80 rows (20.00%)** have a missing `credit_bureau_score`
  (thin-file / new-to-credit applicants).
- `txn_behaviour.csv`: 265 rows, 15 of them (`txn_id` starting `BTXNA`) are
  the seeded anomalies.

## Design decisions

- **`is_thin_file`** is engineered directly from `credit_bureau_score`
  missingness in `preprocessing.py` *before* any imputation — it's a raw
  not-missing/missing indicator, safe to compute pre-split since it depends
  on no fitted statistic. Rows are never dropped for missing scores, since
  dropping would discard every new-to-credit applicant, exactly the
  population the alternate-data features (`upi_monthly_inflow_inr`,
  `bounced_payments_count`) are meant to serve.
- **Stratified 75/25 split, `random_state=42`.** Stratification on
  `default` keeps the ~20% minority class proportionally represented in
  both splits — with only 400 rows, an unstratified split risks a test set
  with a meaningfully different default rate than train, distorting metric
  comparisons.
- **Leakage-safe imputation order**: split first, then compute the
  `credit_bureau_score` median from the **training split only**, then use
  that exact value to fill missing scores in *both* train and test — never
  computed from the full (train+test) dataset. Verified independently: the
  full-dataset median is 610.5, but the train-only median actually used is
  612.0 (re-derived from `applicant_ids_train` and confirmed to match).
- **`employment_type`**: one-hot encoded (drop-first), fit implicitly via
  `pandas.get_dummies` on the full frame before the split (safe — the
  category *set* is fixed, not a fitted statistic).
- **`StandardScaler`** fit only on the training split, applied to both.

## Model comparison (identical train/test split, `random_state=42`)

| Metric | Logistic Regression | Decision Tree |
|---|---|---|
| Accuracy | 0.760 | 0.650 |
| Precision | 0.389 | 0.222 |
| Recall | 0.350 | 0.300 |
| F1 | 0.368 | 0.255 |
| ROC-AUC | 0.719 | 0.519 |

(`DecisionTreeClassifier(random_state=42)` — no other hyperparameters, per
spec. Full confusion matrices and ROC curves: `outputs/confusion_matrix_*.png`,
`outputs/roc_curves.png`, `outputs/model_metrics.json`.)

**Isolation Forest anomaly recall** (`outputs/anomaly_detection_summary.json`):
contamination = 15/265 ≈ 5.66%; **5 of the 15** seeded anomalies detected
(recall = 33.3%), with 10 false positives among the flagged set.

## Risk-based pricing (quartiles of predicted PD, test set)

| Tier | Applicants | Avg. predicted PD | Actual default rate | Rate band |
|---|---|---|---|---|
| Q1 – Low Risk | 25 | 2.0% | 8% | 10%–14% |
| Q2 – Moderate Risk | 25 | 7.3% | 12% | 14%–18% |
| Q3 – Elevated Risk | 25 | 23.4% | 20% | 18%–24% |
| Q4 – High Risk | 25 | 58.7% | 40% | 24%–32% |

Actual default rate increases monotonically from Q1 to Q4, confirming the
Logistic Regression's predicted probabilities rank-order real risk on this
test set.

## Bias / governance note

See [`bias_governance_analysis.md`](bias_governance_analysis.md).

## Final recommendation

**Deploy Logistic Regression, not the Decision Tree.** Logistic Regression
achieves higher accuracy (76.0% vs. 65.0%), higher precision (38.9% vs.
22.2%), and materially better ranking quality (ROC-AUC 0.719 vs. 0.519 —
the unconstrained tree is barely better than random ranking on this
300-row training set). The Decision Tree's ROC-AUC of 0.519 indicates
severe overfitting given only 300 training rows and 10 features — it
memorizes training-set noise rather than learning a generalizable
boundary. Logistic Regression's probability outputs are also directly
usable for the risk-based pricing tiers above (which showed clean monotonic
separation), whereas the Decision Tree's near-random AUC makes its
probabilities unreliable for that purpose. If tree-based modeling is
wanted in production, the fix would be depth/leaf regularization or an
ensemble (out of scope here, since only these two classifiers are
required) rather than the unconstrained single tree evaluated above.
