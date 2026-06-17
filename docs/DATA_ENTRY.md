# Filling the BHP valuation template

[`templates/bhp_template.json`](../templates/bhp_template.json) is the single
place you enter primary-source data. Fill every `null`, replace every
`FILL ...` citation with the exact reference, then run:

```bash
python -m src.template_loader templates/bhp_template.json
```

It prints a **readiness report** — how many inputs are filled and exactly what's
left — and once everything is filled it writes the research note and Excel model
to `output/`. Run it as often as you like; enter data incrementally.

## Units (important)

Production in **million tonnes (Mt)** and prices in **US$/tonne**, so
`production × price = US$ million`. Costs in US$/t. Capex, net debt, corporate,
and other assets in **US$ million**. Shares in **millions**.

## What goes where

| Section | Field | Primary source |
|---|---|---|
| `wacc` | `risk_free` | 10Y government bond yield (FRED / RBA), date-stamped |
| `wacc` | `erp` | Damodaran implied ERP, or a stated historical average |
| `wacc` | `equity_beta` | peer regression / bottom-up; record the peer set + the re-lever gearing |
| `wacc` | `cost_of_debt` | credit rating + spread, or weighted-average from the debt note |
| `wacc` | `tax_rate` | statutory (AUS 30%) or effective — **royalties go in `royalty_rate`, not here** |
| `wacc` | `mv_equity` / `mv_debt` | share price × shares; net debt from the FY balance sheet |
| `commodity_decks` | `spot` + per-year + `long_run` | consensus (broker median) front years; cost-curve support for the long run |
| `divisions[].assets[]` | `production` / `unit_cash_cost` / `sustaining_capex` | FY operational review / production report |
| `divisions[].assets[]` | `stake` | ownership % (e.g. Escondida 57.5%) — verify each |
| `group` | `net_debt` / `minorities` / `shares_outstanding` / `corporate_pv` | FY annual report; `corporate_pv` = PV of unallocated corporate costs |

## Single number vs per-year

`production`, `unit_cash_cost` and `sustaining_capex` accept **either** a single
number (held flat across the forecast years) **or** a `{ "2027": .., "2028": .. }`
map when you want a profile (decline, or a ramp like Jansen). Commodity decks are
always per-year plus a `long_run` level.

## Horizon & mine life

`forecast_years` is the explicit horizon, and asset NPV runs over those years
only. To capture a longer reserve life, extend `forecast_years` (e.g. to 2040).
A reserve-tail terminal value is a roadmap item, not yet modelled.

## The discipline

Nothing counts as done until it's entered from a primary source **and** its
`FILL` citation is replaced. The readiness report and the ledger's `verified`
count are your checklist; the note's provenance table is the payoff. When the
report shows everything filled, the note drops its "illustrative" banner — but
each input still carries its own source and verification status.
