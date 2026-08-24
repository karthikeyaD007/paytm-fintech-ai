"""
Multi-agent debate: BULL -> BEAR -> SYNTHESIZER.

    Stock data
        -> Bull Agent        (upside argument)
        -> Bear Agent         (downside / risk argument)
        -> Synthesizer        (balanced conclusion)

All numeric inputs (beta, CAPM expected return, std dev) are computed
deterministically in Python (CAPM reused from advisory_agent.py). The LLM
(mock by default) only phrases the argument text -- it never invents or
recomputes the numbers.

Run:
    python debate.py
"""

from stock_universe import STOCK_UNIVERSE, MARKET_RETURN
from advisory_agent import get_stock_data, capm_expected_return
from llm_client import call_llm


def bull_agent(ticker, data, capm_return):
    upside_note = (
        f"above the {MARKET_RETURN:.0%} market benchmark" if capm_return > MARKET_RETURN
        else f"close to the {MARKET_RETURN:.0%} market benchmark"
    )
    beta_note = (
        "high market sensitivity, so it should capture more than its share of any market rally"
        if data["beta"] > 1
        else "low market sensitivity, giving defensive stability that still compounds steadily"
    )
    mock = (
        f"BULL case for {ticker}: CAPM-implied expected return is {capm_return:.2%}, {upside_note}. "
        f"Its beta of {data['beta']:.2f} reflects {beta_note}."
    )
    return call_llm(
        system_prompt="You are a bullish equity analyst. Argue only from the numbers given -- do not invent figures.",
        user_prompt=f"Ticker {ticker}: beta={data['beta']}, CAPM expected return={capm_return:.4f}, "
                    f"std_dev={data['std_dev']}. Give a concise bull case (2-3 sentences).",
        mock_response=mock,
    )


def bear_agent(ticker, data, capm_return):
    vol_note = (
        "elevated annual volatility, implying meaningful drawdown risk" if data["std_dev"] > 0.20
        else "moderate volatility that is still not negligible"
    )
    beta_note = (
        f"a beta of {data['beta']:.2f} means it will amplify market downturns, not just rallies"
        if data["beta"] > 1
        else f"a beta of {data['beta']:.2f} limits how much upside it captures in a rally"
    )
    mock = (
        f"BEAR case for {ticker}: standard deviation of {data['std_dev']:.2%} reflects {vol_note}. "
        f"Additionally, {beta_note}."
    )
    return call_llm(
        system_prompt="You are a bearish/risk-focused equity analyst. Argue only from the numbers given -- do not invent figures.",
        user_prompt=f"Ticker {ticker}: beta={data['beta']}, CAPM expected return={capm_return:.4f}, "
                    f"std_dev={data['std_dev']}. Give a concise bear case (2-3 sentences).",
        mock_response=mock,
    )


def synthesizer_agent(ticker, data, capm_return, bull_text, bear_text):
    if data["std_dev"] <= 0.12:
        suitability = "conservative and moderate investors"
    elif data["std_dev"] <= 0.25:
        suitability = "moderate investors"
    else:
        suitability = "aggressive, long-horizon investors who can tolerate drawdowns"

    mock = (
        f"SYNTHESIS for {ticker}: The bull case highlights a {capm_return:.2%} CAPM-implied return "
        f"driven by its {data['beta']:.2f} beta; the bear case flags {data['std_dev']:.2%} volatility "
        f"as the corresponding risk. Balancing both, {ticker} is most appropriate for {suitability}, "
        f"and should be sized as part of a diversified allocation rather than held in isolation."
    )
    return call_llm(
        system_prompt=(
            "You are a balanced investment synthesizer. Combine the bull and bear arguments into one "
            "even-handed conclusion using only the numbers already given -- do not invent figures."
        ),
        user_prompt=f"Bull case: {bull_text}\nBear case: {bear_text}\nGive a balanced 2-3 sentence synthesis.",
        mock_response=mock,
    )


def run_debate(ticker):
    data = get_stock_data(ticker)
    capm_return = capm_expected_return(data["beta"])

    bull_text = bull_agent(ticker, data, capm_return)
    bear_text = bear_agent(ticker, data, capm_return)
    synthesis = synthesizer_agent(ticker, data, capm_return, bull_text, bear_text)

    return {
        "ticker": ticker,
        "beta": data["beta"],
        "capm_expected_return": round(capm_return, 4),
        "std_dev": data["std_dev"],
        "bull": bull_text,
        "bear": bear_text,
        "synthesis": synthesis,
    }


def main():
    for ticker in STOCK_UNIVERSE:
        result = run_debate(ticker)
        print("=" * 70)
        print(f"{result['ticker']}  beta={result['beta']}  CAPM={result['capm_expected_return']:.2%}  std={result['std_dev']:.2%}")
        print(f"BULL: {result['bull']}")
        print(f"BEAR: {result['bear']}")
        print(f"SYNTHESIS: {result['synthesis']}")


if __name__ == "__main__":
    main()
