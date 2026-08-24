"""The 5 required investor profiles for the Portfolio Advisory Agent."""

INVESTOR_PROFILES = [
    {"investor_id": "INV01", "risk_tolerance": "Conservative", "horizon_years": 3, "investment_amount_inr": 200000},
    {"investor_id": "INV02", "risk_tolerance": "Moderate", "horizon_years": 7, "investment_amount_inr": 500000},
    {"investor_id": "INV03", "risk_tolerance": "Aggressive", "horizon_years": 12, "investment_amount_inr": 300000},
    {"investor_id": "INV04", "risk_tolerance": "Moderate", "horizon_years": 5, "investment_amount_inr": 800000},
    {"investor_id": "INV05", "risk_tolerance": "Aggressive", "horizon_years": 2, "investment_amount_inr": 150000},
]

# Prescribed allocations by risk tolerance (equal-weighted across the listed tickers).
PORTFOLIO_ALLOCATIONS = {
    "Conservative": ["PAYBOND", "PAYGOLD", "PAYRETAIL"],
    "Moderate": ["PAYRETAIL", "PAYINFRA", "PAYGOLD"],
    "Aggressive": ["PAYTECH", "PAYFIN", "PAYINFRA"],
}
