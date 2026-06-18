"""
ILLUSTRATIVE BHP Sum-of-Parts demo
==================================

Ties the whole pipeline together end-to-end and OFFLINE:

    scaffold -> WACC bank -> compute WACC -> commodity decks (mining bank)
             -> per-division SOTP -> research note (with the ledger appendix)

EVERY NUMBER HERE IS A PLACEHOLDER. Production, costs, decks, net debt and the
division structure are invented to exercise the machinery -- this is NOT a real
valuation of BHP. Replace the decks and asset economics with primary-source
data (annual report, operational reviews, reserves & resources) before drawing
any conclusion. Units are chosen so production (Mt) x price (US$/t) = US$m.
"""

from __future__ import annotations

import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

from src.ledger import Ledger
from src.data_scaffold import scaffold_entries
from src.question_banks import WACC_BANK, MINING_BANK
from src.wizard import build_entry, compute_wacc
from src.sotp import AssetValuation, Division, SumOfParts
from src.note import write_note
from src.excel_model import write_workbook
import value as wacc_demo  # reuse the illustrative WACC inputs from the CLI demo

BASE = 2026
YEARS = [2027, 2028, 2029, 2030, 2031]

# Illustrative commodity price decks (US$/t) -- placeholders.
DECKS = {
    "ironore.price_deck": {2027: 95, 2028: 90, 2029: 85, 2030: 80, 2031: 78, "long_run": 75},
    "copper.price_deck": {2027: 9500, 2028: 9300, 2029: 9200, 2030: 9100, 2031: 9000, "long_run": 9000},
    "metcoal.price_deck": {2027: 210, 2028: 195, 2029: 185, 2030: 180, 2031: 175, "long_run": 170},
    "potash.price_deck": {2027: 300, 2028: 310, 2029: 320, 2030: 330, 2031: 340, "long_run": 350},
}
SPOTS = {"ironore.price_deck": 105, "copper.price_deck": 9600, "metcoal.price_deck": 205, "potash.price_deck": 295}


def build_ledger():
    led = Ledger("BHP Group Limited  (ILLUSTRATIVE)", "BHP.AX")
    for entry in scaffold_entries(wacc_demo.DEMO_INFO, "BHP.AX", as_of=wacc_demo.DEMO_AS_OF,
                                  price_currency="AUD", live=False).values():
        led.add(entry)
    for spec in WACC_BANK:
        entry, _ = build_entry(spec, wacc_demo.DEMO_ANSWERS[spec["key"]],
                               context=wacc_demo._context_for(spec["key"], led))
        led.add(entry)
    wacc = compute_wacc(led)
    for spec in MINING_BANK:
        answers = {"value": DECKS[spec["key"]],
                   "citation": "ILLUSTRATIVE; consensus front years + cost-support long-run",
                   "rationale": "placeholder deck -- verify against consensus / cost curves"}
        entry, _ = build_entry(spec, answers, context={"spot": SPOTS[spec["key"]]})
        led.add(entry)
    return led, wacc


def build_sotp(wacc: float) -> SumOfParts:
    def asset(name, commodity, deck, prod, cost, sus):
        return AssetValuation(
            name=name, commodity=commodity,
            production={y: prod for y in YEARS},
            price={y: deck[y] for y in YEARS},
            unit_cash_cost={y: cost for y in YEARS},
            sustaining_capex={y: sus for y in YEARS},
            royalty_rate=0.05, tax_rate=0.30,
        )
    divisions = [
        Division("Iron Ore (WAIO)", [asset("WAIO", "iron ore", DECKS["ironore.price_deck"], 280, 20, 1500)]),
        Division("Copper", [asset("Escondida + Cu SA", "copper", DECKS["copper.price_deck"], 1.9, 6000, 1200)]),
        Division("Coal (met)", [asset("BMA", "met coal", DECKS["metcoal.price_deck"], 30, 120, 300)]),
        Division("Potash", [asset("Jansen", "potash", DECKS["potash.price_deck"], 4, 150, 200)]),
    ]
    return SumOfParts(
        company="BHP", base_year=BASE, discount_rate=wacc, divisions=divisions,
        other_assets=2000, corporate_pv=8000, net_debt=11000, minorities=3000,
        shares_outstanding=5068,
    )


def main():
    led, wacc = build_ledger()
    sotp = build_sotp(wacc)
    led.set_result("value_per_share", round(sotp.value_per_share(), 2), unit="USD")

    os.makedirs(os.path.join(_REPO, "output"), exist_ok=True)
    os.makedirs(os.path.join(_REPO, "models"), exist_ok=True)
    note_path = os.path.join(_REPO, "output", "BHP_research_note.md")
    write_note(
        note_path, led, sotp,
        recommendation="HOLD  (ILLUSTRATIVE)",
        thesis="_Placeholder thesis._ The framework supplies the valuation bridge and the audit "
               "trail; the actual view, and the verified inputs behind it, are the analyst's work.",
        illustrative=True,
    )
    led.save(os.path.join(_REPO, "models", "BHP_sotp.json"))

    xlsx_path = os.path.join(_REPO, "output", "BHP_model.xlsx")
    write_workbook(xlsx_path, led, sotp, recommendation="HOLD  (ILLUSTRATIVE)")

    print(f"WACC: {wacc:.2%}")
    print(f"Enterprise value: US${sotp.enterprise_value():,.0f}m")
    print(f"Equity value:     US${sotp.equity_value():,.0f}m")
    print(f"Per share (model US$): {sotp.value_per_share():,.2f}")
    print(f"note  -> {note_path}")
    print(f"excel -> {xlsx_path}")


if __name__ == "__main__":
    main()
