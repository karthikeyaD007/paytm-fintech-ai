# Part 3 — AI Advisory + Valuation + Blockchain Risk

Component overview, plus recorded example run transcripts for every script.
**All transcripts below were recorded with `MOCK_LLM` left at its default
(`1` / mock)** — no API key was used or required to produce this output,
per the project spec ("the evaluator must be able to run the project
without a paid API key"). Optional real-LLM (Groq) mode is described in the
root `README.md`; it only changes the phrasing of narrative text, never the
underlying numbers, which are always computed in plain Python.

## Components

| File | Role |
|---|---|
| `stock_universe.py` | Fictional 6-ticker stock universe + `RISK_FREE_RATE` / `MARKET_RETURN` (exact seed data from spec) |
| `investor_profiles.py` | 5 required investor profiles + prescribed risk-tier allocations |
| `disclosure_snippets.py` | 6 required disclosure snippets (exact text from spec) |
| `llm_client.py` | Shared MOCK_LLM / Groq switch used by the agent scripts |
| `advisory_agent.py` | **Portfolio Advisory Agent** — Think → Act → Observe |
| `extract_disclosure.py` | Structured disclosure-extraction utility (deterministic regex/keyword logic — **not** a 5th agent) |
| `debate.py` | **Bull Agent → Bear Agent → Synthesizer Agent** |
| `dcf_calculator.py` | FCFF / WACC / terminal value / DCF enterprise value / 3×3 sensitivity / EV-EBITDA comparison |
| `blockchain_risk_note.md` | Written analysis: stablecoins, DeFi/DAO risk, crypto allocation, T.A.N.G. framework |

There are exactly **4 agent roles** in this part (Portfolio Advisory,
Bull, Bear, Synthesizer) and exactly **3 ML models** in the whole project
(Logistic Regression, Decision Tree, Isolation Forest — all in Part 2).
`extract_disclosure.py` is a supporting structured-extraction component,
not an autonomous agent.

---

## Recorded run: `python advisory_agent.py`

Think → Act → Observe for all 5 investor profiles. CAPM, portfolio
variance, and standard deviation are computed deterministically in Python
(see `advisory_agent.py`'s `capm_expected_return` /
`portfolio_variance_and_std`). Portfolio variance assumes a uniform
pairwise correlation of rho=0.3 between holdings (documented assumption,
no covariance matrix given in the spec). The escalation threshold
(portfolio std dev > 20%) is applied in Python, and only the
plain-language explanation is routed through `llm_client.call_llm` (mock
template below).

```
======================================================================
INV01 (Conservative) -> FINALIZE_RECOMMENDATION
  Portfolio: ['PAYBOND', 'PAYGOLD', 'PAYRETAIL'] (equal weight)
  CAPM returns: {'PAYBOND': 0.073, 'PAYGOLD': 0.082, 'PAYRETAIL': 0.121}
  Portfolio expected return: 9.20%
  Portfolio std dev: 8.44%
  Explanation: Investor INV01 (Conservative, 3-year horizon, INR 200,000 to invest) is allocated equally across PAYBOND, PAYGOLD, PAYRETAIL. Portfolio CAPM expected return is 9.20% with an estimated annual volatility (std dev) of 8.44%, against a 20% automated-approval risk threshold. Risk is within the automated-approval threshold, so this recommendation is finalized.
======================================================================
INV02 (Moderate) -> FINALIZE_RECOMMENDATION
  Portfolio: ['PAYRETAIL', 'PAYINFRA', 'PAYGOLD'] (equal weight)
  CAPM returns: {'PAYRETAIL': 0.121, 'PAYINFRA': 0.136, 'PAYGOLD': 0.082}
  Portfolio expected return: 11.30%
  Portfolio std dev: 12.57%
  Explanation: Investor INV02 (Moderate, 7-year horizon, INR 500,000 to invest) is allocated equally across PAYRETAIL, PAYINFRA, PAYGOLD. Portfolio CAPM expected return is 11.30% with an estimated annual volatility (std dev) of 12.57%, against a 20% automated-approval risk threshold. Risk is within the automated-approval threshold, so this recommendation is finalized.
======================================================================
INV03 (Aggressive) -> ESCALATED_TO_HUMAN_ADVISOR
  Portfolio: ['PAYTECH', 'PAYFIN', 'PAYINFRA'] (equal weight)
  CAPM returns: {'PAYTECH': 0.163, 'PAYFIN': 0.151, 'PAYINFRA': 0.136}
  Portfolio expected return: 15.00%
  Portfolio std dev: 20.58%
  Explanation: Investor INV03 (Aggressive, 12-year horizon, INR 300,000 to invest) is allocated equally across PAYTECH, PAYFIN, PAYINFRA. Portfolio CAPM expected return is 15.00% with an estimated annual volatility (std dev) of 20.58%, against a 20% automated-approval risk threshold. Risk exceeds the threshold, so this recommendation is escalated to a human advisor for review before execution.
======================================================================
INV04 (Moderate) -> FINALIZE_RECOMMENDATION
  Portfolio: ['PAYRETAIL', 'PAYINFRA', 'PAYGOLD'] (equal weight)
  CAPM returns: {'PAYRETAIL': 0.121, 'PAYINFRA': 0.136, 'PAYGOLD': 0.082}
  Portfolio expected return: 11.30%
  Portfolio std dev: 12.57%
  Explanation: Investor INV04 (Moderate, 5-year horizon, INR 800,000 to invest) is allocated equally across PAYRETAIL, PAYINFRA, PAYGOLD. Portfolio CAPM expected return is 11.30% with an estimated annual volatility (std dev) of 12.57%, against a 20% automated-approval risk threshold. Risk is within the automated-approval threshold, so this recommendation is finalized.
======================================================================
INV05 (Aggressive) -> ESCALATED_TO_HUMAN_ADVISOR
  Portfolio: ['PAYTECH', 'PAYFIN', 'PAYINFRA'] (equal weight)
  CAPM returns: {'PAYTECH': 0.163, 'PAYFIN': 0.151, 'PAYINFRA': 0.136}
  Portfolio expected return: 15.00%
  Portfolio std dev: 20.58%
  Explanation: Investor INV05 (Aggressive, 2-year horizon, INR 150,000 to invest) is allocated equally across PAYTECH, PAYFIN, PAYINFRA. Portfolio CAPM expected return is 15.00% with an estimated annual volatility (std dev) of 20.58%, against a 20% automated-approval risk threshold. Risk exceeds the threshold, so this recommendation is escalated to a human advisor for review before execution.
```

Both the `FINALIZE_RECOMMENDATION` and `ESCALATED_TO_HUMAN_ADVISOR` code paths are
exercised deterministically: Conservative (8.44%) and Moderate (12.57%
for both INV02 and INV04) finalize automatically; Aggressive (20.58% for
both INV03 and INV05) exceeds the 20% threshold and escalates.

---

## Recorded run: `python extract_disclosure.py`

Deterministic keyword/regex extraction, no LLM involved, over all 6
required snippets. Mock-mode rule (matches the spec literally):
`hedging_detected` is True iff the snippet contains "assuming",
"cautiously", or "visibility"; `sentiment` is "confident" if it contains
"confident"/"approved", "cautious" if `hedging_detected` is True, else
"neutral".

```
----------------------------------------------------------------------
doc_01: Assuming input costs remain stable through the next two quarters, we expect margins to hold at current levels.
{'risk_flags': [], 'hedging_detected': True, 'sentiment': 'cautious'}
----------------------------------------------------------------------
doc_02: The company faces an ongoing litigation matter related to a former vendor contract; management believes the exposure is not material.
{'risk_flags': ['litigation'], 'hedging_detected': False, 'sentiment': 'neutral'}
----------------------------------------------------------------------
doc_03: Our top three customers together account for approximately 42 percent of total revenue this year.
{'risk_flags': ['customer_concentration'], 'hedging_detected': False, 'sentiment': 'neutral'}
----------------------------------------------------------------------
doc_04: We remain cautiously optimistic about demand recovery, though visibility beyond the next quarter is limited given macro uncertainty.
{'risk_flags': [], 'hedging_detected': True, 'sentiment': 'cautious'}
----------------------------------------------------------------------
doc_05: The board is confident in the long-term strategy and has approved an expanded capital expenditure plan for the coming year.
{'risk_flags': [], 'hedging_detected': False, 'sentiment': 'confident'}
----------------------------------------------------------------------
doc_06: A recent regulatory notice has been received regarding data-localization compliance; the company is in active dialogue with the regulator.
{'risk_flags': ['regulatory'], 'hedging_detected': False, 'sentiment': 'neutral'}
```

`doc_02` correctly flags the `litigation` risk; `doc_01` and `doc_04`
detect hedging language; `doc_05`'s board-approval language is correctly
classified as `confident`.

---

## Recorded run: `python debate.py`

Bull → Bear → Synthesizer for every ticker in `STOCK_UNIVERSE`. CAPM
expected return is computed in Python (reused from `advisory_agent.py`);
each agent's argument text is the mock template (LLM not required).

```
======================================================================
PAYFIN  beta=1.35  CAPM=15.10%  std=28.00%
BULL: BULL case for PAYFIN: CAPM-implied expected return is 15.10%, above the 13% market benchmark. Its beta of 1.35 reflects high market sensitivity, so it should capture more than its share of any market rally.
BEAR: BEAR case for PAYFIN: standard deviation of 28.00% reflects elevated annual volatility, implying meaningful drawdown risk. Additionally, a beta of 1.35 means it will amplify market downturns, not just rallies.
SYNTHESIS: SYNTHESIS for PAYFIN: The bull case highlights a 15.10% CAPM-implied return driven by its 1.35 beta; the bear case flags 28.00% volatility as the corresponding risk. Balancing both, PAYFIN is most appropriate for aggressive, long-horizon investors who can tolerate drawdowns, and should be sized as part of a diversified allocation rather than held in isolation.
======================================================================
PAYRETAIL  beta=0.85  CAPM=12.10%  std=17.00%
BULL: BULL case for PAYRETAIL: CAPM-implied expected return is 12.10%, close to the 13% market benchmark. Its beta of 0.85 reflects low market sensitivity, giving defensive stability that still compounds steadily.
BEAR: BEAR case for PAYRETAIL: standard deviation of 17.00% reflects moderate volatility that is still not negligible. Additionally, a beta of 0.85 limits how much upside it captures in a rally.
SYNTHESIS: SYNTHESIS for PAYRETAIL: The bull case highlights a 12.10% CAPM-implied return driven by its 0.85 beta; the bear case flags 17.00% volatility as the corresponding risk. Balancing both, PAYRETAIL is most appropriate for moderate investors, and should be sized as part of a diversified allocation rather than held in isolation.
======================================================================
PAYINFRA  beta=1.1  CAPM=13.60%  std=22.00%
BULL: BULL case for PAYINFRA: CAPM-implied expected return is 13.60%, above the 13% market benchmark. Its beta of 1.10 reflects high market sensitivity, so it should capture more than its share of any market rally.
BEAR: BEAR case for PAYINFRA: standard deviation of 22.00% reflects elevated annual volatility, implying meaningful drawdown risk. Additionally, a beta of 1.10 means it will amplify market downturns, not just rallies.
SYNTHESIS: SYNTHESIS for PAYINFRA: The bull case highlights a 13.60% CAPM-implied return driven by its 1.10 beta; the bear case flags 22.00% volatility as the corresponding risk. Balancing both, PAYINFRA is most appropriate for moderate investors, and should be sized as part of a diversified allocation rather than held in isolation.
======================================================================
PAYGOLD  beta=0.2  CAPM=8.20%  std=12.00%
BULL: BULL case for PAYGOLD: CAPM-implied expected return is 8.20%, close to the 13% market benchmark. Its beta of 0.20 reflects low market sensitivity, giving defensive stability that still compounds steadily.
BEAR: BEAR case for PAYGOLD: standard deviation of 12.00% reflects moderate volatility that is still not negligible. Additionally, a beta of 0.20 limits how much upside it captures in a rally.
SYNTHESIS: SYNTHESIS for PAYGOLD: The bull case highlights a 8.20% CAPM-implied return driven by its 0.20 beta; the bear case flags 12.00% volatility as the corresponding risk. Balancing both, PAYGOLD is most appropriate for conservative and moderate investors, and should be sized as part of a diversified allocation rather than held in isolation.
======================================================================
PAYBOND  beta=0.05  CAPM=7.30%  std=4.00%
BULL: BULL case for PAYBOND: CAPM-implied expected return is 7.30%, close to the 13% market benchmark. Its beta of 0.05 reflects low market sensitivity, giving defensive stability that still compounds steadily.
BEAR: BEAR case for PAYBOND: standard deviation of 4.00% reflects moderate volatility that is still not negligible. Additionally, a beta of 0.05 limits how much upside it captures in a rally.
SYNTHESIS: SYNTHESIS for PAYBOND: The bull case highlights a 7.30% CAPM-implied return driven by its 0.05 beta; the bear case flags 4.00% volatility as the corresponding risk. Balancing both, PAYBOND is most appropriate for conservative and moderate investors, and should be sized as part of a diversified allocation rather than held in isolation.
======================================================================
PAYTECH  beta=1.55  CAPM=16.30%  std=34.00%
BULL: BULL case for PAYTECH: CAPM-implied expected return is 16.30%, above the 13% market benchmark. Its beta of 1.55 reflects high market sensitivity, so it should capture more than its share of any market rally.
BEAR: BEAR case for PAYTECH: standard deviation of 34.00% reflects elevated annual volatility, implying meaningful drawdown risk. Additionally, a beta of 1.55 means it will amplify market downturns, not just rallies.
SYNTHESIS: SYNTHESIS for PAYTECH: The bull case highlights a 16.30% CAPM-implied return driven by its 1.55 beta; the bear case flags 34.00% volatility as the corresponding risk. Balancing both, PAYTECH is most appropriate for aggressive, long-horizon investors who can tolerate drawdowns, and should be sized as part of a diversified allocation rather than held in isolation.
```

---

## Recorded run: `python dcf_calculator.py`

FCFF = EBIT × (1 − tax) + D&A − CapEx − ΔNWC, forecast over 5 years,
discounted at WACC, plus a Gordon-growth terminal value, all in plain
Python. Cost of equity reuses `PAYFIN`'s beta (1.35) via CAPM.

**Chosen inputs and why** (illustrative, stated here since the spec asks
for inputs "you choose and state in writing"): base-year EBIT = INR 250 cr,
D&A = INR 40 cr, CapEx = INR 60 cr, ΔNWC = INR 15 cr, tax rate = 25%, and
15% annual growth applied to each of those four lines across the 5-year
forecast, for a hypothetical Paytm Postpaid-scale lending business line.
Cost of debt = 9% pre-tax, capital structure = 65% equity / 35% debt
(illustrative, typical of a lending-adjacent fintech with some leverage but
not a pure-play bank). Terminal growth = 5%, chosen specifically to sit
**7.18 percentage points below** the base-case WACC (12.18%) — comfortably
past the required 3pp minimum gap — so that even after the ±1pp sensitivity
swing on both axes, WACC exceeds terminal growth in every one of the 9
grid cells (worst case: WACC 11.18% vs. growth 6.00%, a 5.18pp gap, well
above the required 1pp minimum). EV/EBITDA multiple = 14×, an illustrative
mid-range multiple for a growth-stage fintech lending business.

```
Cost of equity (CAPM, beta=1.35): 15.1000%
WACC: 12.1775%
5-year FCFF forecast (INR cr): [175.38, 201.68, 231.93, 266.72, 306.73]
Terminal value (INR cr): 4487.20
PV of terminal value (INR cr): 2526.08
DCF Enterprise Value (INR cr): 3348.10
EV/EBITDA valuation (14.0x base EBITDA 290.0 cr): 4060.00 cr
DCF vs EV/EBITDA difference: -17.5%

3x3 Sensitivity Table (Enterprise Value, INR cr) -- rows=WACC, cols=terminal growth:
  WACC=11.18%: {'g=4.00%': 3461.43, 'g=5.00%': 3914.23, 'g=6.00%': 4541.94}
  WACC=12.18%: {'g=4.00%': 3018.08, 'g=5.00%': 3348.10, 'g=6.00%': 3784.97}
  WACC=13.18%: {'g=4.00%': 2671.97, 'g=5.00%': 2921.07, 'g=6.00%': 3239.58}

Output written to ai_advisory_blockchain/outputs/dcf_valuation.json
```

**3×3 sensitivity table** (Enterprise Value, INR crore):

| WACC \ Terminal growth | g = 4.00% | g = 5.00% (base) | g = 6.00% |
|---|---|---|---|
| **WACC = 11.18%** (base − 1%) | 3,461.43 | 3,914.23 | 4,541.94 |
| **WACC = 12.18%** (base) | 3,018.08 | **3,348.10** | 3,784.97 |
| **WACC = 13.18%** (base + 1%) | 2,671.97 | 2,921.07 | 3,239.58 |

The DCF enterprise value (₹3,348.10 cr) comes in **17.5% below** the
comparable EV/EBITDA valuation (14× base EBITDA of ₹290 cr = ₹4,060 cr) —
a plausible spread reflecting the DCF's more conservative embedded growth
and discount assumptions versus the market-multiple approach; both are
reported side by side rather than reconciled to a single "correct" number,
consistent with standard cross-checking practice.
