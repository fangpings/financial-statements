#!/usr/bin/env python3
"""Offline accounting bridges for the textbook's explicitly bounded examples."""

import json
from math import isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def equal(label, actual, expected, tolerance=1e-8):
    if not isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise ValueError(f"{label}: calculated {actual}, recorded {expected}")


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def verify_case(case):
    rows = case["years"]
    metrics = []
    for row in rows:
        label = row["year"]
        equal(label + " assets", sum(row[k] for k in
              ("cash", "receivables", "inventory", "ppe_net")), row["assets"])
        equal(label + " balance", row["assets"], sum(row[k] for k in
              ("payables", "accruals", "debt", "equity")))
    for previous, row in zip(rows, rows[1:]):
        label = row["year"]
        change = lambda key: row[key] - previous[key]
        ebit = row["revenue"] - row["cogs"] - row["opex_ex_depreciation"] - row["depreciation"]
        equal(label + " tax", (ebit - row["interest"]) * case["tax_rate"], row["tax"])
        equal(label + " profit", ebit - row["interest"] - row["tax"], row["net_income"])
        indirect = (row["net_income"] + row["depreciation"] - change("receivables")
                    - change("inventory") + change("payables") + change("accruals"))
        # Independently reconstruct the cash receipts and payments from accrual inputs.
        customer_receipts = row["revenue"] - change("receivables")
        purchases = row["cogs"] + change("inventory")
        supplier_payments = purchases - change("payables")
        other_payments = row["opex_ex_depreciation"] - change("accruals")
        direct = customer_receipts - supplier_payments - other_payments - row["interest"] - row["tax"]
        equal(label + " indirect CFO", indirect, row["cfo"])
        equal(label + " direct CFO", direct, row["cfo"])
        financing = row["borrowings"] - row["principal_repaid"] - row["dividends"]
        equal(label + " cash", previous["cash"] + direct - row["capex"] + financing, row["cash"])
        equal(label + " PPE", previous["ppe_net"] + row["capex"] - row["depreciation"], row["ppe_net"])
        equal(label + " debt", previous["debt"] + row["borrowings"] - row["principal_repaid"], row["debt"])
        equal(label + " equity", previous["equity"] + row["net_income"] - row["dividends"], row["equity"])
        metrics.append({"year": label, "ebit": ebit,
                        "gross_margin": (row["revenue"] - row["cogs"]) / row["revenue"],
                        "operating_margin": ebit / row["revenue"],
                        "net_margin": row["net_income"] / row["revenue"],
                        "cash_conversion": direct / row["net_income"],
                        "fcf": direct - row["capex"], "interest_coverage": ebit / row["interest"],
                        "receipts": customer_receipts, "purchases": purchases,
                        "supplier_payments": supplier_payments, "other_payments": other_payments})
    operating = rows[1:]
    equal("three-year CFO", sum(r["cfo"] for r in operating), 53)
    equal("three-year capex", sum(r["capex"] for r in operating), 115)
    equal("three-year net borrowing", sum(r["borrowings"] - r["principal_repaid"] for r in operating), 85)
    equal("three-year dividends", sum(r["dividends"] for r in operating), 30)
    equal("three-year cash change", rows[-1]["cash"] - rows[0]["cash"], -7)
    scenarios = {}
    for name, s in case["scenarios"].items():
        remaining = (s["opening_available_cash"] + s["cfo"] - s["capex"]
                     - s["principal_due"] - s["dividends"] - s["minimum_cash"])
        equal(name + " liquidity", remaining, {"base": -4, "stress": -24}[name])
        scenarios[name] = (remaining, remaining + s["conditional_credit"])
    prior, current = rows[-2:]
    average = lambda k: (prior[k] + current[k]) / 2
    dso = average("receivables") / current["revenue"] * 365
    dio = average("inventory") / current["cogs"] * 365
    dpo = average("payables") / current["cogs"] * 365
    equal("Y3 CCC rounded", round(dso + dio - dpo, 2), 81.69)
    return metrics, scenarios


def verify_real(real):
    current, prior = real["annual"]["current"], real["annual"]["prior"]
    quarter, old_quarter = real["quarter"]["current"], real["quarter"]["prior"]
    equal("annual basic EPS rounded", round(current["net_income"] / current["basic_shares"], 2), 11.86)
    equal("annual diluted EPS rounded", round(current["net_income"] / current["diluted_shares"], 2), 11.80)
    equal("annual revenue growth rounded", round((current["revenue"] / prior["revenue"] - 1) * 100, 2), 15.67)
    equal("annual FCF", current["cfo"] - current["capex"], 74071)
    equal("quarter FCF", quarter["cfo"] - quarter["capex"], 19257)
    equal("previous quarter FCF", old_quarter["cfo"] - old_quarter["capex"], 20666)
    ttm = {k: current[k] + quarter[k] - old_quarter[k] for k in ("revenue", "cfo", "capex")}
    equal("TTM revenue", ttm["revenue"], 254190)
    equal("TTM CFO", ttm["cfo"], 122145)
    equal("TTM capex", ttm["capex"], 49483)
    equal("TTM FCF", ttm["cfo"] - ttm["capex"], 72662)
    retail = real["retail"]
    equal("retail revenue bridge", retail["net_sales"] + retail["membership_fees"], retail["revenue"])
    equal("retail membership percentage", round(retail["membership_fees"] / retail["revenue"] * 100, 2), 1.90)
    bridges = real["annual"]["bridges"]
    equal("expanded annual CFO bridge", current["net_income"] +
          sum(value for _, value in bridges["cfo_adjustments"]), current["cfo"])
    investing = sum(bridges["investing_cash_flows"].values())
    financing = sum(bridges["financing_cash_flows"].values())
    equal("expanded annual investing", investing, -96970)
    equal("expanded annual financing", financing, -37757)
    cash = bridges["cash"]
    equal("expanded annual ending cash", cash["beginning"] + current["cfo"] +
          investing + financing + cash["fx_effect"], cash["ending"])
    for name, row in bridges["equity"].items():
        equal("expanded annual equity " + name, row["beginning"] + sum(row["changes"]), row["ending"])
    equal("expanded annual total equity", sum(row["ending"] for row in bridges["equity"].values()), 268477)
    unearned = bridges["unearned_revenue"]
    equal("expanded unearned revenue bridge", unearned["beginning"] +
          unearned["deferral"] + unearned["recognition"], unearned["ending"])
    return ttm


def verify_other_examples():
    # Independently expected outputs for sensitive worked examples in chapters 11–34.
    equal("contract allocation", 120 * 100 / 150 + (120 * 50 / 150) / 2, 100)
    equal("FIFO", 10 * 10 + 2 * 12, 124)
    equal("LIFO", 10 * 12 + 2 * 10, 140)
    lease = 11 / 1.1 + 11 / 1.1 ** 2
    equal("lease after first payment", lease * 1.1 - 11, 10)
    equal("lease at maturity", (lease * 1.1 - 11) * 1.1 - 11, 0)
    equal("acquisition goodwill", 150 - (10 + 80 + 50 - 40), 50)
    equal("long-lived asset loss after recoverability failure", 100 - 70, 30)
    equal("goodwill impairment capped", min(200 - 120, 60), 60)
    equal("Non-GAAP tax bridge", 80 + (20 + 15 + 10 - 5) * 0.8, 112)
    equal("bank assets", 100 + 700 - 14 + 200 + 14, 1000)
    equal("bank allowance", 14 + 8 - 6 + 1, 17)
    equal("retirement obligation PV rounded", round(100 / 1.05 ** 10, 2), 61.39)
    # Appendix B: distinguish operating balance changes from acquired/FX balances.
    equal("operating receivables increase excluding acquisition and FX", 150 - 100 - 25 - 5, 20)
    equal("PPE bridge including noncash acquisitions", 200 + 60 + 30 + 40 - 25 - 10 - 5, 290)
    equal("taxed adjustments to net income", 80 + (20 - 5) * (1 - 0.25), 91.25)
    equal("permanently nondeductible expense adjustment", 80 + 20 - 5 * (1 - 0.25), 96.25)
    equal("minimum CFO without new credit", 30 + 50 + 12 + 30 - 93, 29)
    equal("maximum investment without new credit", 93 + 25 - 50 - 12 - 30, 26)
    # Appendix D: profit and cash explanations must reproduce the original case.
    equal("Y3 operating income bridge", 41 + 54 - 43 - 13 - 5, 34)
    equal("Y3 cash shortfall before net financing", 45 + 12 - 13.8, 43.2)
    equal("quarter FCF change bridge", (34180 - 30583) - (14923 - 9917), -1409)
    # Expanded chapters: independent cross-period endpoints for selected examples.
    bond_value = 4 / 1.06 + 104 / 1.06 ** 2
    equal("two-year debt amortized to principal", (bond_value * 1.06 - 4) * 1.06 - 4, 100)
    equal("bad debt net balance after revised estimate and writeoff", 100 - 5 - (2.9 + 3.5 - 5), 93.6)
    equal("contract cumulative catch-up second-period margin", 200 * (80 / 200) - 50 - 40, -10)
    equal("stock issuance and repurchase weighted shares", 100 * 3 / 12 + 112 * 6 / 12 + 92 * 3 / 12, 104)
    equal("if-converted diluted EPS rounded", round((90 + 5 * 0.8) / 120, 4), 0.7833)
    equal("acquisition goodwill including deferred tax", 150 - (100 - 50 * 0.2), 60)
    equal("pension year-end funded deficit", (120 + 5 + 6 + 4 - 8) - (100 + 3 + 7 - 8), 25)
    equal("SBC scenario indirect CFO", 40 + 12 + 15 - 35, 32)
    equal("Northstar Y3 CFO increase bridge", -7.2 + 5 + 11, 8.8)


def main():
    metrics, scenarios = verify_case(load("northstar.json"))
    ttm = verify_real(load("real-extracts.json"))
    verify_other_examples()
    print("PASS: fictional statements, cash receipts/payments, equity and debt bridges")
    print("PASS: sourced arithmetic and selected independent worked examples")
    for m in metrics:
        print(f"{m['year']}: EBIT {m['ebit']:.2f}; margin {m['operating_margin']:.2%}; "
              f"CFO/NI {m['cash_conversion']:.2f}; FCF {m['fcf']:.2f}")
    for name, (before, after) in scenarios.items():
        print(f"{name}: cash buffer surplus {before:.2f}; IF credit available {after:.2f}")
    print(f"Historical Microsoft TTM revenue {ttm['revenue']:,}; "
          f"defined FCF {ttm['cfo'] - ttm['capex']:,} million USD")
    print("These are arithmetic checks, not an audit of issuer reports or forecasts.")


if __name__ == "__main__":
    main()
