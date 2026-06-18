#!/usr/bin/env python
"""
value.py -- CLI entry point for a single-name valuation.

    python value.py BHP.AX --company "BHP Group Limited"   # interactive elicitation
    python value.py BHP.AX --demo                          # offline, illustrative BHP inputs
    python value.py BHP.AX --no-fetch                      # skip the yfinance scaffold

Flow: scaffold (yfinance, unverified) -> elicit (WACC bank) -> compute WACC ->
save the assumption-and-evidence ledger. Stages 2-3 (full sum-of-parts DCF,
research note, Excel) build on this spine.
"""

from __future__ import annotations

import argparse
import os

from src.ledger import Ledger
from src.data_scaffold import fetch_info, scaffold_entries
from src.question_banks import WACC_BANK
from src.wizard import build_entry, compute_wacc, run_bank

# Illustrative live wrapper + WACC inputs for --demo. NOT a real valuation;
# this exists to show the end-to-end flow offline and deterministically.
DEMO_INFO = {
    "currentPrice": 41.20, "sharesOutstanding": 5_068_000_000,
    "marketCap": 208_000_000_000, "beta": 0.61,
}
# The demo scaffold is a frozen, illustrative AUD-listing snapshot -- NOT a live
# pull. Stamp it with a fixed as-of so the note never implies it is today's price.
DEMO_AS_OF = "2026-06-15"
DEMO_ANSWERS = {
    "wacc.currency_basis": {"value": "USD", "citation": "BHP functional currency",
                            "rationale": "commodities USD-priced; convert final $/share to AUD at spot"},
    "wacc.risk_free": {"value": 0.042, "citation": "US 10Y Treasury, FRED 2026-06-15",
                       "rationale": "matches the USD cash-flow basis"},
    "wacc.erp": {"value": 0.048, "method": "implied", "citation": "Damodaran implied ERP, Jun-2026",
                 "rationale": "forward-looking implied preferred over backward historical"},
    "wacc.equity_beta": {"value": 0.95, "method": "bottom_up",
                         "citation": "peers RIO/VALE/Anglo unlevered, re-levered to 15% target gearing",
                         "rationale": "raw 5y beta distorted by the 2022 commodity spike"},
    "wacc.cost_of_debt": {"value": 0.053, "method": "rating_implied",
                          "citation": "A-rated; rf + ~1.1% spread", "rationale": "rating-implied"},
    "wacc.tax_rate": {"value": 0.30, "citation": "AUS statutory rate",
                      "rationale": "statutory; royalties captured in opex, not in the tax rate"},
    "wacc.mv_equity": {"value": 208000, "citation": "approx AUD price x shares, ~208,800m (illustrative; AUD basis)"},
    "wacc.mv_debt": {"value": 10000, "citation": "BHP FY25 net debt (illustrative; USD ~10,000m)"},
}


def _context_for(key: str, ledger: Ledger) -> dict:
    """Per-input guardrail context that depends on other entries."""
    if key == "wacc.equity_beta":
        return {"relever_gearing": 0.15, "weights_gearing": 0.15}
    if key == "wacc.mv_equity":
        return {"scaffold_value": ledger.value_of("group.market_cap")}
    return {}


def _load_scaffold(ledger: Ledger, info: dict, ticker: str,
                   as_of=None, live: bool = True) -> None:
    for entry in scaffold_entries(info, ticker, as_of=as_of,
                                  price_currency=ledger.presentation_currency, live=live).values():
        ledger.add(entry)


def run_demo(ticker: str, company: str, out_path: str) -> None:
    led = Ledger(company=company, ticker=ticker)
    _load_scaffold(led, DEMO_INFO, ticker, as_of=DEMO_AS_OF, live=False)
    for spec in WACC_BANK:
        entry, _ = build_entry(spec, DEMO_ANSWERS[spec["key"]], context=_context_for(spec["key"], led))
        led.add(entry)
    wacc = compute_wacc(led)
    _save_and_report(led, out_path, wacc)


def run_interactive(ticker: str, company: str, out_path: str, fetch: bool) -> None:
    led = Ledger(company=company, ticker=ticker)
    if fetch:
        try:
            _load_scaffold(led, fetch_info(ticker), ticker)
            print(f"Scaffold loaded: {led.audit_summary()['unverified']} unverified entries from yfinance.")
        except Exception as exc:  # network/ticker problems shouldn't abort the session
            print(f"(scaffold skipped -- {exc})")
    run_bank(WACC_BANK, led)
    try:
        wacc = compute_wacc(led)
    except ValueError as exc:
        wacc = None
        print(f"WACC not computed -- {exc}")
    _save_and_report(led, out_path, wacc)


def _save_and_report(led: Ledger, out_path: str, wacc) -> None:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    led.save(out_path)
    a = led.audit_summary()
    coe = led.results.get("cost_of_equity", {}).get("value")
    print("\n" + "=" * 60)
    print(f"{led.company} ({led.ticker})")
    if wacc is not None:
        coe_str = f"{coe:.2%}" if coe is not None else "n/a"
        print(f"WACC: {wacc:.2%}    cost of equity: {coe_str}")
    print(f"entries: {a['entries_total']}   verified: {a['verified']}   unverified: {a['unverified']}")
    print(f"open warnings: {a['warnings_open']}   overrides logged: {a['overrides_logged']}")
    if led.open_warnings():
        print("  ! open: " + ", ".join(led.open_warnings()))
    print(f"ledger saved -> {out_path}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Single-name valuation (Stage 1: WACC spine).")
    p.add_argument("ticker")
    p.add_argument("--company", default=None)
    p.add_argument("--out", default=None, help="ledger output path (default models/<ticker>.json)")
    p.add_argument("--demo", action="store_true", help="run offline with illustrative BHP inputs")
    p.add_argument("--no-fetch", action="store_true", help="skip the yfinance scaffold")
    args = p.parse_args(argv)

    company = args.company or args.ticker
    out_path = args.out or os.path.join("models", f"{args.ticker.replace('.', '_')}.json")

    if args.demo:
        run_demo(args.ticker, company, out_path)
    else:
        run_interactive(args.ticker, company, out_path, fetch=not args.no_fetch)


if __name__ == "__main__":
    main()
