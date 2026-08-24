"""Fictional stock universe for the Portfolio Advisory Agent and Bull/Bear debate.

These are illustrative fictional tickers for this exercise, not real listed
securities. `analyst_expected_return` is a separate illustrative reference
figure (e.g. representing an outside analyst's view) and is intentionally
NOT used in the CAPM computation -- the agent's CAPM expected return uses
ONLY `beta` via the CAPM formula, so it is expected to differ from
`analyst_expected_return`.
"""

STOCK_UNIVERSE = {
    "PAYFIN":    {"beta": 1.35, "analyst_expected_return": 0.16, "std_dev": 0.28},
    "PAYRETAIL": {"beta": 0.85, "analyst_expected_return": 0.11, "std_dev": 0.17},
    "PAYINFRA":  {"beta": 1.10, "analyst_expected_return": 0.135, "std_dev": 0.22},
    "PAYGOLD":   {"beta": 0.20, "analyst_expected_return": 0.08, "std_dev": 0.12},
    "PAYBOND":   {"beta": 0.05, "analyst_expected_return": 0.065, "std_dev": 0.04},
    "PAYTECH":   {"beta": 1.55, "analyst_expected_return": 0.19, "std_dev": 0.34},
}

RISK_FREE_RATE = 0.07
MARKET_RETURN = 0.13
