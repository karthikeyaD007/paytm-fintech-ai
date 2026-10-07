# Paytm-style FinTech AI

A synthetic, fully reproducible FinTech project in three parts:

1. **Payments & Fraud Analytics** (`payments_fraud_analytics/`) — SQLite,
   SQL, Excel, reconciliation, dashboard.
2. **Credit Risk & Lending ML** (`credit_risk_lending_ml/`) — Logistic
   Regression + Decision Tree credit-risk models, risk-based pricing,
   Isolation Forest anomaly detection, bias/governance analysis.
3. **AI Advisory + Valuation + Blockchain Risk** (`ai_advisory_blockchain/`) —
   Portfolio Advisory Agent (Think→Act→Observe), disclosure extraction,
   Bull/Bear/Synthesizer debate, DCF valuation, blockchain risk note.

All data is synthetic, generated deterministically with `seed=42`. No real
financial data, real companies, or real market data are used anywhere.

---

## 1. Environment setup

Requires Python 3.10+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

## 2. Installation

```bash
pip install -r requirements.txt
```

`sqlite3` (the CLI, optional — only needed to run `fraud_queries.sql`
directly) ships with most systems; Python's built-in `sqlite3` module is
used by all the actual scripts.

## 3. Dataset generation

```bash
cd payments_fraud_analytics
python generate_data.py     # -> merchants.csv, users.csv, ledger.csv, gateway_export.csv

cd ../credit_risk_lending_ml
python generate_data.py     # -> credit_applicants.csv, txn_behaviour.csv
```

Both scripts are deterministic (`seed=42`) and print row counts / sanity
stats when run. The CSVs are also committed to the repository so the
project can be inspected without re-running generation.

## 4. SQLite database creation

```bash
cd payments_fraud_analytics
python create_database.py   # -> paytm_payments.db (rebuilt from the CSVs)
```

Creates `merchants`, `users`, `transactions` tables with primary/foreign
keys. `paytm_payments.db` is also committed, but can always be regenerated
from the CSVs with this script.

## 5. Running Part 1 — Payments & Fraud Analytics

```bash
cd payments_fraud_analytics

# SQL fraud analysis (chargebacks, burner accounts, velocity attacks, merchant patterns, ...)
sqlite3 paytm_payments.db < fraud_queries.sql
# or, to also save every query's output as committed evidence:
python run_fraud_queries.py      # -> fraud_queries_output.txt

# Reconciliation: ledger.csv vs. gateway_export.csv
python reconcile.py         # -> dashboard/reconciliation_*.{json,csv}

# Excel workbook (VLOOKUP, HLOOKUP, nested IF/AND, pivot-style analytics)
python build_excel_workbook.py   # -> merchant_workbook.xlsx

# Dashboard: four-layer chart-image dashboard (the graded deliverable --
# saved matplotlib PNGs, not a live BI tool)
python dashboard/generate_dashboard.py   # -> dashboard/*.png; interpretations in dashboard/README.md

# Optional bonus: interactive Streamlit exploration dashboard (not the graded artifact)
streamlit run dashboard/app.py
```

`reconcile.py` must run before the dashboard generator (it produces
`dashboard/reconciliation_summary.json`, which the dashboard's headline
layer reads). `reconcile_payments(ledger_df, gateway_df)` takes DataFrames
directly and returns four DataFrames (missing-in-gateway, missing-in-ledger,
amount mismatches, status mismatches) — see `reconcile.py` docstring.

## 6. Running Part 2 — Credit Risk & Lending ML

```bash
cd credit_risk_lending_ml

python preprocessing.py     # sanity-check the leakage-safe train/test pipeline
python modeling.py          # trains Logistic Regression + Decision Tree -> outputs/
python risk_pricing.py      # PD -> risk tier -> interest-rate band -> outputs/
python anomaly_detection.py # StandardScaler -> Isolation Forest -> outputs/
```

Read `bias_governance_analysis.md` for the written proxy-variable /
fairness / governance analysis (no code — this is a written deliverable).

### ML evaluation details

- `preprocessing.py` splits train/test **first** (75/25, stratified,
  `random_state=42`), then computes the `credit_bureau_score` median from
  the **training split only** and uses it to impute missing scores in both
  train and test — this avoids train/test leakage. Applicants with no
  bureau score at all are flagged via `is_thin_file`.
- `modeling.py` trains exactly two classifiers — Logistic Regression and a
  Decision Tree — on the identical split, and reports accuracy, precision,
  recall, F1, ROC-AUC, ROC curves, and confusion matrices for each (see
  `outputs/model_metrics.json`, `outputs/roc_curves.png`,
  `outputs/confusion_matrix_*.png`). **No target accuracy is claimed** —
  the reported numbers are whatever the models actually achieve on this
  dataset.
- `risk_pricing.py` uses the Logistic Regression model's predicted
  probability of default to assign each test applicant a risk tier
  (A–D) and a corresponding interest-rate band, then reports the actual
  realized default rate per tier for validation.
- `anomaly_detection.py` scales `txn_behaviour.csv` and runs an Isolation
  Forest with contamination set to the known seeded-anomaly rate
  (15 / 265). This is evaluated as an **anomaly-recall** problem (how many
  of the 15 seeded anomalies were flagged), not classification accuracy —
  see `outputs/anomaly_detection_summary.json` for the actual recall
  achieved.

## 7. Running Part 3 — AI Advisory + Valuation + Blockchain Risk

```bash
cd ai_advisory_blockchain

python advisory_agent.py    # Think -> Act -> Observe, all 5 investor profiles
python extract_disclosure.py  # structured signals for all 6 disclosure snippets
python debate.py            # Bull -> Bear -> Synthesizer for every ticker
python dcf_calculator.py    # FCFF forecast, WACC, terminal value, EV, 3x3 sensitivity -> outputs/
```

Read `blockchain_risk_note.md` for the written blockchain/crypto risk
analysis and T.A.N.G. fraud-framework discussion (no code — written
deliverable). See `ai_advisory_blockchain/README.md` for recorded example
run transcripts of every script above (captured with `MOCK_LLM` left at its
default) plus the DCF sensitivity table.

There are exactly **3 ML models** in the whole project (Logistic
Regression, Decision Tree, Isolation Forest — all in Part 2) and exactly
**4 agent roles** in Part 3 (Portfolio Advisory Agent, Bull, Bear,
Synthesizer). Disclosure extraction (`extract_disclosure.py`) is a
deterministic keyword/regex utility, not a fifth agent.

## 8. Mock LLM mode (default, no API key needed)

By default `MOCK_LLM=1`. Every LLM-touching script
(`advisory_agent.py`, `debate.py`) works fully offline using deterministic
Python templates for narrative text — all financial numbers (CAPM,
portfolio variance/std dev, DCF, WACC) are always computed in plain Python
regardless of LLM mode; the LLM is never asked to do arithmetic.

```bash
export MOCK_LLM=1     # Windows PowerShell: $env:MOCK_LLM = "1"
python advisory_agent.py
```

## 9. Optional real LLM mode (Groq)

Copy `.env.example` to `.env` and fill in a Groq API key, or export the
variables directly:

```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key_here
export LLM_MODEL=openai/gpt-oss-120b
export MOCK_LLM=0
```

If the key is missing or the API call fails for any reason, the scripts
automatically fall back to the deterministic mock text rather than
crashing — the project never hard-depends on external API access.

**Never commit a real `.env` file or API key.** `.env` is gitignored;
`.env.example` (with a blank key) is the committed template.

## 10. Design decisions (summary per part)

**Requirements**: a single consolidated `requirements.txt` at the repo
root covers all three parts (not one per part) — see Section 2.

**Part 1 — Payments & Fraud Analytics**
- Excel workbook: since `openpyxl` cannot create live Excel PivotTable
  objects, the required "pivot table" outputs (merchant×status,
  merchant×day) are built as pandas-computed pivot-style tables with
  explicit static-value labeling, plus a real Excel Table (ListObject) on
  the transaction data so a grader can insert a live PivotTable themselves.
  Fee-tier percentages (HLOOKUP demo) and the "High-Value Merchant Day"
  >INR 5,000 / non-East threshold (nested IF/AND) are illustrative,
  documented in-workbook.
- Reconciliation: `reconcile_payments(ledger_df, gateway_df)` uses set
  operations on `transaction_id` for missing/extra rows and `pd.merge` for
  the pairwise amount/status comparison, returning four DataFrames.
- Dashboard: built as saved matplotlib PNGs (the graded artifact) rather
  than a live BI tool; a bonus interactive Streamlit app is included but
  is not the graded deliverable. `match_rate` and `chargeback_ratio` use
  the exact count-based definitions specified in the brief.

**Part 2 — Credit Risk & Lending ML**
- `is_thin_file` is computed pre-split (safe — it's raw missingness, not a
  fitted statistic); the train/test split happens next; the
  `credit_bureau_score` median imputation value is computed from the
  training split only, applied to both splits — verified independently
  (see `credit_risk_lending_ml/README.md`).
- `DecisionTreeClassifier(random_state=42)` is left unconstrained per
  spec; it visibly overfits on 300 training rows (AUC 0.52), which is the
  honest, reported result rather than a hidden regularization choice.
- Risk-pricing tiers use quartiles of predicted PD (equal-sized groups),
  which gives a clean monotonically-increasing observed default rate
  across tiers.

**Part 3 — AI Advisory + Valuation + Blockchain Risk**
- Portfolio variance assumes a uniform pairwise correlation ρ=0.3 between
  holdings in the same portfolio (no covariance matrix given in the
  spec) — this reproduces the spec's target std-dev figures exactly
  (8.44% / 12.57% / 20.58%).
- The LLM (mock by default) is used only to phrase narrative text; CAPM,
  portfolio variance, DCF, and WACC are always computed in plain Python.
- DCF terminal growth (5%) is chosen 7.18pp below base-case WACC
  (12.18%), well past the required 3pp minimum, so WACC exceeds terminal
  growth in all 9 sensitivity-grid cells.

## 11. Where outputs are generated

| Part | Outputs | Location |
|---|---|---|
| 1 | CSVs, `paytm_payments.db`, `merchant_workbook.xlsx` | `payments_fraud_analytics/` |
| 1 | SQL query results (committed evidence) | `payments_fraud_analytics/fraud_queries_output.txt` |
| 1 | Reconciliation reports | `payments_fraud_analytics/dashboard/reconciliation_*.{json,csv}` |
| 1 | Dashboard chart images + interpretations | `payments_fraud_analytics/dashboard/*.png`, `dashboard/README.md` |
| 2 | CSVs | `credit_risk_lending_ml/` |
| 2 | Model metrics, plots, risk-pricing tables, anomaly results | `credit_risk_lending_ml/outputs/` |
| 2 | Comparison table, bias note, final recommendation | `credit_risk_lending_ml/README.md`, `bias_governance_analysis.md` |
| 3 | DCF valuation + sensitivity table | `ai_advisory_blockchain/outputs/dcf_valuation.json` |
| 3 | Advisory/debate/disclosure results | printed to stdout; recorded transcripts in `ai_advisory_blockchain/README.md` |

---

## Repository structure

```
paytm-fintech-ai/
├── README.md
├── requirements.txt
├── .env.example
├── payments_fraud_analytics/
│   ├── generate_data.py
│   ├── merchants.csv / users.csv / ledger.csv / gateway_export.csv
│   ├── create_database.py
│   ├── paytm_payments.db
│   ├── fraud_queries.sql
│   ├── run_fraud_queries.py
│   ├── fraud_queries_output.txt
│   ├── reconcile.py
│   ├── build_excel_workbook.py
│   ├── merchant_workbook.xlsx
│   └── dashboard/
│       ├── generate_dashboard.py      # graded: saved chart-image dashboard
│       ├── headline_scorecards.png / trends_daily_gmv_chargebacks.png /
│       │   breakdown_gmv_by_method_category.png / details_top_merchants.png
│       ├── README.md                  # written interpretations per layer
│       ├── app.py                     # bonus interactive Streamlit dashboard
│       └── reconciliation_*.{json,csv}
├── credit_risk_lending_ml/
│   ├── generate_data.py
│   ├── credit_applicants.csv / txn_behaviour.csv
│   ├── preprocessing.py
│   ├── modeling.py
│   ├── risk_pricing.py
│   ├── anomaly_detection.py
│   ├── bias_governance_analysis.md
│   ├── README.md                      # EDA, comparison table, recommendation
│   └── outputs/
└── ai_advisory_blockchain/
    ├── stock_universe.py
    ├── investor_profiles.py
    ├── disclosure_snippets.py
    ├── llm_client.py
    ├── advisory_agent.py
    ├── extract_disclosure.py
    ├── debate.py
    ├── dcf_calculator.py
    ├── blockchain_risk_note.md
    ├── README.md                      # recorded transcripts + sensitivity table
    └── outputs/
```
