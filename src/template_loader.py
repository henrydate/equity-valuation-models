"""
BHP data-entry template loader
==============================

Reads a filled JSON template (``templates/bhp_template.json``), reports what is
still unfilled, and -- once complete -- builds the ledger + SOTP and emits the
research note and Excel model. The analyst enters primary-source data in one
place and regenerates both deliverables with one command:

    python -m src.template_loader templates/bhp_template.json

Every value starts ``null`` and every citation starts with ``FILL``; the
readiness report lists exactly what remains, so data can be entered
incrementally. See ``docs/DATA_ENTRY.md``.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Optional, Tuple

from .ledger import Ledger
from .question_banks import MINING_BANK, WACC_BANK
from .wizard import build_entry, compute_wacc
from .sotp import AssetValuation, Division, SumOfParts
from .note import write_note
from .excel_model import write_workbook

_WACC_KEYS = ["risk_free", "erp", "equity_beta", "cost_of_debt", "tax_rate", "mv_equity", "mv_debt"]
_DECK_KEY = {"iron ore": "ironore.price_deck", "copper": "copper.price_deck",
             "met coal": "metcoal.price_deck", "potash": "potash.price_deck"}


def load_template(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _citation_ok(c) -> bool:
    return isinstance(c, str) and c.strip() != "" and "FILL" not in c.upper()


def _required_slots(data: dict) -> List[Tuple[str, bool]]:
    """Every required input as (path, is_filled). Drives the readiness report."""
    slots: List[Tuple[str, bool]] = []
    wacc = data.get("wacc", {})
    for k in _WACC_KEYS:
        e = wacc.get(k, {})
        slots.append((f"wacc.{k} value", e.get("value") is not None))
        slots.append((f"wacc.{k} citation", _citation_ok(e.get("citation"))))
    fyears = [str(y) for y in data.get("forecast_years", [])]
    for comm, d in data.get("commodity_decks", {}).items():
        deck = d.get("deck", {})
        slots.append((f"decks[{comm}].spot", d.get("spot") is not None))
        slots.append((f"decks[{comm}].citation", _citation_ok(d.get("citation"))))
        for y in fyears:  # a deck must cover every forecast year, else that year prices to 0
            slots.append((f"decks[{comm}].{y}", deck.get(y) is not None))
        slots.append((f"decks[{comm}].long_run", deck.get("long_run") is not None))
    for div in data.get("divisions", []):
        for a in div.get("assets", []):
            nm = f"{div.get('name')}/{a.get('name')}"
            for fld in ("production", "unit_cash_cost", "sustaining_capex"):
                slots.append((f"{nm}.{fld}", a.get(fld) is not None))
            slots.append((f"{nm}.citation", _citation_ok(a.get("citation"))))
    g = data.get("group", {})
    for k in ("corporate_pv", "net_debt", "minorities", "shares_outstanding"):
        slots.append((f"group.{k}", g.get(k) is not None))
    slots.append(("group.citation", _citation_ok(g.get("citation"))))
    return slots


def collect_missing(data: dict) -> List[str]:
    return [p for p, ok in _required_slots(data) if not ok]


def _norm(v, years) -> Dict[int, float]:
    """Scalar -> flat per-year map; {year: val} map -> int-keyed map."""
    if isinstance(v, dict):
        return {int(k): val for k, val in v.items()}
    return {y: v for y in years}


def build_from_template(data: dict) -> Tuple[Ledger, SumOfParts]:
    missing = collect_missing(data)
    if missing:
        raise ValueError("template is incomplete:\n  - " + "\n  - ".join(missing))

    years = [int(y) for y in data["forecast_years"]]
    base = int(data["valuation_base_year"])
    led = Ledger(data["company"], data["ticker"],
                 reporting_currency=data.get("reporting_currency", "USD"),
                 presentation_currency=data.get("presentation_currency", "AUD"))

    specs = {s["key"]: s for s in WACC_BANK}
    cur = data["wacc"].get("currency_basis", {})
    led.add(build_entry(specs["wacc.currency_basis"],
                        {"value": led.reporting_currency,
                         "citation": cur.get("citation", "reporting currency"),
                         "rationale": "cash-flow currency basis"})[0])
    for k in _WACC_KEYS:
        t = data["wacc"][k]
        led.add(build_entry(specs[f"wacc.{k}"],
                            {"value": t["value"], "citation": t.get("citation", ""),
                             "rationale": t.get("rationale") or t.get("citation"),
                             "method": t.get("method")})[0])
    wacc = compute_wacc(led)

    mining = {s["key"]: s for s in MINING_BANK}
    decks_resolved: Dict[str, Dict[int, float]] = {}
    for comm, d in data["commodity_decks"].items():
        raw = d["deck"]
        bkey = _DECK_KEY.get(comm)
        if bkey:
            led.add(build_entry(mining[bkey],
                                {"value": raw, "citation": d.get("citation", ""),
                                 "rationale": d.get("rationale") or "analyst price deck"},
                                context={"spot": d.get("spot")})[0])
        decks_resolved[comm] = {int(y): v for y, v in raw.items() if y != "long_run"}

    divisions = []
    default_tax = data["wacc"]["tax_rate"]["value"]
    for div in data["divisions"]:
        assets = []
        for a in div["assets"]:
            deck = decks_resolved[a["commodity"]]
            assets.append(AssetValuation(
                name=a["name"], commodity=a["commodity"],
                production=_norm(a["production"], years),
                price={y: deck[y] for y in years if y in deck},
                unit_cash_cost=_norm(a["unit_cash_cost"], years),
                sustaining_capex=_norm(a["sustaining_capex"], years),
                royalty_rate=a.get("royalty_rate", 0.0),
                tax_rate=a.get("tax_rate", default_tax),
                stake=a.get("stake", 1.0),
            ))
        divisions.append(Division(div["name"], assets, overhead_pv=div.get("overhead_pv", 0.0)))

    g = data["group"]
    sotp = SumOfParts(company=data["company"], base_year=base, discount_rate=wacc,
                      divisions=divisions, other_assets=g.get("other_assets", 0.0),
                      corporate_pv=g["corporate_pv"], net_debt=g["net_debt"],
                      minorities=g["minorities"], shares_outstanding=g["shares_outstanding"])
    led.set_result("value_per_share", round(sotp.value_per_share(), 2), unit=led.reporting_currency)
    return led, sotp


def run_template(path, out_dir: Optional[str] = None, recommendation: Optional[str] = None,
                 thesis: Optional[str] = None) -> None:
    data = load_template(path)
    slots = _required_slots(data)
    missing = [p for p, ok in slots if not ok]
    filled = len(slots) - len(missing)
    print(f"{data.get('company', '?')} - template readiness: {filled}/{len(slots)} inputs filled")
    if missing:
        print(f"\nStill to fill ({len(missing)}):")
        for m in missing:
            print(f"  - {m}")
        print("\nFill these values and replace 'FILL' citations, then re-run to build the note + Excel.")
        return

    led, sotp = build_from_template(data)
    out_dir = out_dir or "output"
    os.makedirs(out_dir, exist_ok=True)
    stem = led.ticker.replace(".", "_")
    note_path = os.path.join(out_dir, f"{stem}_note.md")
    xlsx_path = os.path.join(out_dir, f"{stem}_model.xlsx")
    # real, cited data -> not the illustrative banner (verification status still shows per-input)
    write_note(note_path, led, sotp, recommendation=recommendation, thesis=thesis, illustrative=False)
    write_workbook(xlsx_path, led, sotp, recommendation=recommendation)

    wacc = led.results.get("wacc", {}).get("value")
    print(f"\nWACC: {wacc:.2%}" if wacc is not None else "\nWACC: n/a")
    print(f"Per share ({led.reporting_currency}): {sotp.value_per_share():,.2f}")
    a = led.audit_summary()
    print(f"Entries verified: {a['verified']}/{a['entries_total']}  ·  open warnings: {a['warnings_open']}")
    print(f"note  -> {note_path}")
    print(f"excel -> {xlsx_path}")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Build a valuation (note + Excel) from a filled JSON template.")
    p.add_argument("template")
    p.add_argument("--out", default="output")
    p.add_argument("--rating", default=None)
    args = p.parse_args(argv)
    run_template(args.template, out_dir=args.out, recommendation=args.rating)


if __name__ == "__main__":
    main()
