"""
DCF valuation for a hypothetical Paytm-style lending/payments business
("PAYFIN" — reuses that ticker's profile from stock_universe.py for its
cost-of-equity beta, but the cash-flow inputs below are separate illustrative
company financials for this valuation exercise).

FCFF = EBIT * (1 - tax) + D&A - CapEx - delta(NWC)

Pipeline:
    5-year FCFF forecast -> WACC -> Terminal Value -> discount to PV -> EV

Also produces a 3x3 sensitivity table (WACC +-1%, terminal growth +-1%) and
compares the DCF enterprise value against an EV/EBITDA-multiple valuation.

All calculations are deterministic Python -- no LLM involved.

Run:
    python dcf_calculator.py
"""

import json
import os

from stock_universe import STOCK_UNIVERSE, RISK_FREE_RATE, MARKET_RETURN

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")

# --- Illustrative base-year financials (INR crore) for the valuation subject ---
BASE_EBIT = 250.0
TAX_RATE = 0.25
BASE_DA = 40.0
BASE_CAPEX = 60.0
BASE_NWC_CHANGE = 15.0
REVENUE_GROWTH = 0.15          # applied to EBIT/D&A/CapEx/NWC each forecast year
TERMINAL_GROWTH = 0.05
FORECAST_YEARS = 5

# --- WACC inputs ---
COST_OF_DEBT = 0.09
DEBT_WEIGHT = 0.35
EQUITY_WEIGHT = 0.65
EQUITY_BETA = STOCK_UNIVERSE["PAYFIN"]["beta"]   # reuse PAYFIN beta as cost-of-equity proxy

# --- comparison multiple ---
EV_EBITDA_MULTIPLE = 14.0
BASE_EBITDA = BASE_EBIT + BASE_DA


def cost_of_equity(beta=EQUITY_BETA, rf=RISK_FREE_RATE, rm=MARKET_RETURN):
    return rf + beta * (rm - rf)


def wacc(cost_of_equity_=None, cost_of_debt=COST_OF_DEBT, tax_rate=TAX_RATE,
         equity_weight=EQUITY_WEIGHT, debt_weight=DEBT_WEIGHT):
    ke = cost_of_equity_ if cost_of_equity_ is not None else cost_of_equity()
    return equity_weight * ke + debt_weight * cost_of_debt * (1 - tax_rate)


def forecast_fcff(years=FORECAST_YEARS, growth=REVENUE_GROWTH):
    fcffs = []
    ebit, da, capex, nwc = BASE_EBIT, BASE_DA, BASE_CAPEX, BASE_NWC_CHANGE
    for _ in range(years):
        ebit *= (1 + growth)
        da *= (1 + growth)
        capex *= (1 + growth)
        nwc *= (1 + growth)
        fcff = ebit * (1 - TAX_RATE) + da - capex - nwc
        fcffs.append(fcff)
    return fcffs


def terminal_value(last_fcff, wacc_rate, terminal_growth=TERMINAL_GROWTH):
    return last_fcff * (1 + terminal_growth) / (wacc_rate - terminal_growth)


def discount_to_pv(cash_flows, wacc_rate):
    return [cf / ((1 + wacc_rate) ** (i + 1)) for i, cf in enumerate(cash_flows)]


def enterprise_value(wacc_rate=None, terminal_growth=TERMINAL_GROWTH, growth=REVENUE_GROWTH):
    wacc_rate = wacc_rate if wacc_rate is not None else wacc()
    fcffs = forecast_fcff(growth=growth)
    pv_fcffs = discount_to_pv(fcffs, wacc_rate)
    tv = terminal_value(fcffs[-1], wacc_rate, terminal_growth)
    pv_tv = tv / ((1 + wacc_rate) ** FORECAST_YEARS)
    ev = sum(pv_fcffs) + pv_tv
    return {
        "fcffs": fcffs,
        "pv_fcffs": pv_fcffs,
        "terminal_value": tv,
        "pv_terminal_value": pv_tv,
        "enterprise_value": ev,
        "wacc": wacc_rate,
        "terminal_growth": terminal_growth,
    }


def sensitivity_table(base_wacc, base_terminal_growth, step=0.01):
    wacc_values = [base_wacc - step, base_wacc, base_wacc + step]
    growth_values = [base_terminal_growth - step, base_terminal_growth, base_terminal_growth + step]

    table = {}
    for w in wacc_values:
        row = {}
        for g in growth_values:
            row[f"g={g:.2%}"] = round(enterprise_value(wacc_rate=w, terminal_growth=g)["enterprise_value"], 2)
        table[f"WACC={w:.2%}"] = row
    return table


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    ke = cost_of_equity()
    w = wacc(ke)
    dcf = enterprise_value(wacc_rate=w)
    ev_multiple = EV_EBITDA_MULTIPLE * BASE_EBITDA

    print(f"Cost of equity (CAPM, beta={EQUITY_BETA}): {ke:.4%}")
    print(f"WACC: {w:.4%}")
    print(f"5-year FCFF forecast (INR cr): {[round(x, 2) for x in dcf['fcffs']]}")
    print(f"Terminal value (INR cr): {dcf['terminal_value']:.2f}")
    print(f"PV of terminal value (INR cr): {dcf['pv_terminal_value']:.2f}")
    print(f"DCF Enterprise Value (INR cr): {dcf['enterprise_value']:.2f}")
    print(f"EV/EBITDA valuation ({EV_EBITDA_MULTIPLE}x base EBITDA {BASE_EBITDA:.1f} cr): {ev_multiple:.2f} cr")
    diff_pct = 100 * (dcf["enterprise_value"] - ev_multiple) / ev_multiple
    print(f"DCF vs EV/EBITDA difference: {diff_pct:+.1f}%")

    sens = sensitivity_table(w, TERMINAL_GROWTH)
    print("\n3x3 Sensitivity Table (Enterprise Value, INR cr) -- rows=WACC, cols=terminal growth:")
    for wacc_label, row in sens.items():
        print(f"  {wacc_label}: {row}")

    output = {
        "cost_of_equity": ke,
        "wacc": w,
        "fcff_forecast": dcf["fcffs"],
        "terminal_value": dcf["terminal_value"],
        "pv_terminal_value": dcf["pv_terminal_value"],
        "dcf_enterprise_value": dcf["enterprise_value"],
        "ev_ebitda_valuation": ev_multiple,
        "dcf_vs_multiple_diff_pct": diff_pct,
        "sensitivity_table": sens,
    }
    with open(os.path.join(OUT_DIR, "dcf_valuation.json"), "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nOutput written to {os.path.join(OUT_DIR, 'dcf_valuation.json')}")
    return output


if __name__ == "__main__":
    main()
