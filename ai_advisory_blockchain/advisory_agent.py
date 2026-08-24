"""
Portfolio Advisory Agent -- Think -> Act -> Observe workflow.

    Investor profile
        -> THINK   (determine required portfolio from prescribed allocation)
        -> ACT     (call get_stock_data(ticker) for each holding)
        -> OBSERVE (CAPM expected return, portfolio variance/std dev, risk check)
        -> final recommendation OR human escalation

All financial calculations (CAPM, portfolio variance, standard deviation)
are performed deterministically in Python. The LLM (mock by default) is
used only to phrase the plain-language explanation of numbers already
computed -- never to compute them.

Assumption (undocumented by the spec, stated here explicitly): no
cross-asset covariance matrix is provided, so portfolio variance assumes a
uniform pairwise correlation of rho=0.3 between any two holdings in the
same portfolio (a standard simplifying assumption for same-sector/adjacent
equities), i.e. for holdings i, j with weights w and std devs sigma:
    portfolio_variance = sum_i(w_i^2 * sigma_i^2)
                        + sum_{i != j}(w_i * w_j * sigma_i * sigma_j * rho)
Escalation threshold: portfolio std dev > 20% triggers human escalation.
Under this formula the three prescribed allocations come out to
Conservative ~8.44%, Moderate ~12.57%, Aggressive ~20.58% std dev -- so
Conservative/Moderate finalize automatically and Aggressive escalates,
deterministically exercising both code paths.

Run:
    python advisory_agent.py
"""

import json

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN
from investor_profiles import INVESTOR_PROFILES, PORTFOLIO_ALLOCATIONS
from llm_client import call_llm

RISK_ESCALATION_THRESHOLD_STD = 0.20
PAIRWISE_CORRELATION = 0.3


def get_stock_data(ticker):
    """ACT: fetch stock data for a ticker (beta, expected return, std dev)."""
    if ticker not in STOCK_UNIVERSE:
        raise ValueError(f"Unknown ticker: {ticker}")
    return STOCK_UNIVERSE[ticker]


def capm_expected_return(beta, risk_free=RISK_FREE_RATE, market_return=MARKET_RETURN):
    """CAPM: E[R] = Rf + beta * (Rm - Rf). Uses ONLY beta, per spec."""
    return risk_free + beta * (market_return - risk_free)


def portfolio_variance_and_std(tickers, weights, stock_data, rho=PAIRWISE_CORRELATION):
    n = len(tickers)
    sigmas = [stock_data[t]["std_dev"] for t in tickers]
    variance = sum((weights[i] ** 2) * (sigmas[i] ** 2) for i in range(n))
    for i in range(n):
        for j in range(n):
            if i != j:
                variance += weights[i] * weights[j] * sigmas[i] * sigmas[j] * rho
    return variance, variance ** 0.5


def think(profile):
    """THINK: determine the required portfolio from the investor's risk tolerance."""
    tickers = PORTFOLIO_ALLOCATIONS[profile["risk_tolerance"]]
    weights = [1 / len(tickers)] * len(tickers)  # equal allocation, as prescribed
    return tickers, weights


def act(tickers):
    """ACT: call get_stock_data for every holding in the required portfolio."""
    return {t: get_stock_data(t) for t in tickers}


def observe(tickers, weights, stock_data):
    """OBSERVE: compute CAPM returns, portfolio expected return, variance, std dev."""
    capm_returns = {t: capm_expected_return(stock_data[t]["beta"]) for t in tickers}
    portfolio_expected_return = sum(w * capm_returns[t] for t, w in zip(tickers, weights))
    variance, std = portfolio_variance_and_std(tickers, weights, stock_data)
    return capm_returns, portfolio_expected_return, variance, std


def run_advisory_agent(profile):
    # THINK
    tickers, weights = think(profile)
    # ACT
    stock_data = act(tickers)
    # OBSERVE
    capm_returns, portfolio_expected_return, variance, std = observe(tickers, weights, stock_data)

    escalate = std > RISK_ESCALATION_THRESHOLD_STD
    decision = "ESCALATED_TO_HUMAN_ADVISOR" if escalate else "FINALIZE_RECOMMENDATION"

    mock_summary = (
        f"Investor {profile['investor_id']} ({profile['risk_tolerance']}, "
        f"{profile['horizon_years']}-year horizon, INR {profile['investment_amount_inr']:,} to invest) "
        f"is allocated equally across {', '.join(tickers)}. "
        f"Portfolio CAPM expected return is {portfolio_expected_return:.2%} with an estimated "
        f"annual volatility (std dev) of {std:.2%}, against a {RISK_ESCALATION_THRESHOLD_STD:.0%} "
        f"automated-approval risk threshold. "
        + ("Risk exceeds the threshold, so this recommendation is escalated to a human advisor "
           "for review before execution."
           if escalate else
           "Risk is within the automated-approval threshold, so this recommendation is finalized.")
    )

    explanation = call_llm(
        system_prompt=(
            "You are a portfolio advisory assistant. Explain the given recommendation to the "
            "investor in plain, reassuring language. Do not perform or alter any numeric "
            "calculation -- only explain the numbers you are given."
        ),
        user_prompt=f"Explain this recommendation to the investor: {mock_summary}",
        mock_response=mock_summary,
    )

    return {
        "investor_id": profile["investor_id"],
        "risk_tolerance": profile["risk_tolerance"],
        "horizon_years": profile["horizon_years"],
        "investment_amount_inr": profile["investment_amount_inr"],
        "tickers": tickers,
        "weights": weights,
        "capm_returns": {t: round(r, 4) for t, r in capm_returns.items()},
        "portfolio_expected_return": round(portfolio_expected_return, 4),
        "portfolio_variance": round(variance, 6),
        "portfolio_std_dev": round(std, 4),
        "decision": decision,
        "explanation": explanation,
    }


def main():
    results = [run_advisory_agent(p) for p in INVESTOR_PROFILES]
    for r in results:
        print("=" * 70)
        print(f"{r['investor_id']} ({r['risk_tolerance']}) -> {r['decision']}")
        print(f"  Portfolio: {r['tickers']} (equal weight)")
        print(f"  CAPM returns: {r['capm_returns']}")
        print(f"  Portfolio expected return: {r['portfolio_expected_return']:.2%}")
        print(f"  Portfolio std dev: {r['portfolio_std_dev']:.2%}")
        print(f"  Explanation: {r['explanation']}")
    return results


if __name__ == "__main__":
    main()
