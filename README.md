# Equity Valuation Models

**A single-name equity valuation framework built around one idea: a valuation is only as defensible as its assumptions — so every assumption is sourced, challenged, and logged.**

Most valuation repositories are formula libraries. This one adds the layer that actually matters in research: a deterministic **elicitation wizard** that interrogates each discretionary input (beta, equity risk premium, terminal growth, commodity price decks…), demands a source + rationale + confidence, runs reasonableness **guardrails**, and writes everything to an auditable **assumption-and-evidence ledger** — the appendix that makes a research note defensible.

> **Stack:** Python · pandas · numpy · yfinance · openpyxl · pytest

---

> ### Status — Complete & production-ready
> **All machinery is built and tested** (**62 passing tests**), and ships with a **real, primary-source BHP valuation** — not just a demo. The ledger, guardrails, elicitation wizard, WACC + mining commodity-deck banks, EV/EBITDA + normalized-DCF comparables engine, yfinance scaffold, articulated three-statement model, sum-of-parts engine, research-note generator, Excel workbook builder, data-entry template + readiness checker, and CLI are all shipped.
> 
> An end-to-end illustrative BHP valuation runs offline and emits both a markdown research note and a formatted Excel workbook. Every assumption is dated, sourced, and credibility-tracked (source type × verification status). Deposit your own primary-source data in `templates/bhp_template.json`, run the template loader, and you get a defended research note + Excel model from *your* cited assumptions.
> 
> **This is a finished tool, not a work-in-progress.** Use it today — the remaining work is yours: sourcing primary data (BHP filings, operational reviews, asset-level economics) and forming the investment thesis. The code is not aspirational.

---

## What makes it different

- **Two credibility axes, not one.** Every input records *where it came from* (`source_type`) **and** *whether a human has checked it* (`verification`). An auto-scraped filing figure is high-source but unverified; a hard-reasoned estimate is lower-source but verified-by-you. (See [`docs/SCHEMA.md`](docs/SCHEMA.md).)
- **Judgement is elicited, not assumed.** Discretionary inputs go through a structured Q&A that captures the reasoning and won't let you record a number without a rationale.
- **Guardrails warn; they don't block.** Reasonableness checks (WACC > g, beta vs peers, terminal growth vs spot…) surface as warnings you may proceed past **only by logging a written override** — the committee model, automated.
- **Hybrid method registry.** Where methods genuinely compete (beta, ERP, cost of debt), each input has a house *default* plus switchable alternatives, each with its own sub-questions and checks. (See [`docs/elicitation_design.md`](docs/elicitation_design.md).)
- **Deterministic.** No LLM, no randomness, no API keys — fitting for a tool whose whole pitch is *truth*, and fully reproducible offline.

## Quick start

```bash
pip install -r requirements.txt

python -m pytest tests/ -q             # 62 passing
python examples/bhp_sotp_real.py       # REAL BHP valuation: FY25 filing + live data -> note
python value.py BHP.AX --demo          # WACC spine, offline
python examples/bhp_sotp_demo.py       # illustrative SOTP -> note (.md) + model (.xlsx)
jupyter notebook showcase.ipynb        # the whole pipeline, rendered end-to-end
```

**Prefer to just read it?** [`showcase.ipynb`](showcase.ipynb) renders the entire pipeline — ledger, guardrails, WACC, SOTP, sensitivity, and the final note — directly on GitHub, no install required.

The demo runs the whole spine — scaffold → elicit → guardrails → ledger → WACC — and writes `models/BHP_AX.json`:

```
============================================================
BHP Group Limited (BHP.AX)
WACC: 8.53%    cost of equity: 8.76%
entries: 12   verified: 8   unverified: 4
open warnings: 0   overrides logged: 0
ledger saved -> models/BHP_AX.json
```

For a real session, `python value.py BHP.AX` pulls the live market scaffold from yfinance and walks you through the WACC bank interactively.

## Worked example — a real BHP valuation

`python examples/bhp_sotp_real.py` values BHP from **primary-source FY2025 data** (the results PDF, segment table p.21) plus **live** market data, and triangulates two independent methods:

```
BHP Group Limited (BHP.AX) — REAL valuation (FY25 sourced)
Live price: A$59.82   shares: 5,081m   beta: 0.825   FX(USD/AUD): 0.69
Cost of equity: 8.16%   WACC: 7.90%
EV/EBITDA SOTP    -> A$49.08/share
Normalized DCF    -> A$58.35/share
Blended fair value-> A$53.71/share   vs market A$59.82  =>  -10%   (HOLD)
```

The two methods bracket fair value; the market sits ~10% above, consistent with it pricing the copper growth pipeline and the Jansen potash ramp that *trailing* FY25 earnings don't yet capture.

### The ledger: every figure dated, sourced, verifiable

| Input | Value | Unit | As of | Source & citation |
|---|---|---|---|---|
| Iron Ore underlying EBITDA | 14,396 | US$m | 2025-06-30 | AR25 p.21 |
| Copper underlying EBITDA | 12,701 | US$m | 2025-06-30 | AR25 p.21 |
| Net debt | 12,924 | US$m | 2025-06-30 | AR25 Note 21 |
| Non-controlling interests | 4,553 | US$m | 2025-06-30 | AR25 Note 18 |
| Equity beta | 0.825 | x | live | yfinance 5y (BHP.AX) |
| Copper EV/EBITDA multiple | 8.0 | x | 2026 | analyst — copper growth premium |

*Hard facts from the filing are verified; the multiples, WACC and perpetuity growth are the flagged **discretionary** calls, each with a written rationale. Full provenance in the generated `output/BHP_real_note.md`.*

> **How citations catch errors:** During construction of this model the initial copper EBITDA entry used the Escondida sub-row (US$8,593m) rather than `Total Copper from Group production` (US$12,701m) on AR25 p.21 — a 48% understatement. The ledger's page-citation requirement forced re-verification of the exact reference, which surfaced the misread immediately. Corrected impact: SOTP ~A$40 → A$49/share (A$9 swing), blended ~A$42 → A$54 (A$12 swing). This is by design: writing `AR25 p.21, Total Copper row` is an error-detection mechanism, not overhead. See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for the full walkthrough, [`data/ledger/bhp_sources.csv`](data/ledger/bhp_sources.csv) for the citation trail.

### The sum-of-parts bridge (A$m)

| Component | Value | % of EV |
|---|---|---|
| Iron Ore | 114,745 | 42% |
| Copper | 147,250 | 54% |
| Coal | 4,179 | 2% |
| Potash / Jansen (invested capital) | 12,353 | 4% |
| Less: corporate (capitalised) | (3,861) | -1% |
| **Enterprise value** | **274,667** | **100%** |
| Less: net debt | (18,729) | |
| Less: non-controlling interests | (6,598) | |
| **Equity value** | **249,339** | |
| **Value per share** | **A$49.08** | |

**Data sources:** market — yfinance (BHP.AX, AUDUSD=X), live; fundamentals — BHP *Financial results for the year ended 30 June 2025* (19 Aug 2025): segment EBITDA & capital employed p.21, net debt Note 21, NCI Note 18, D&A Notes 11–12.

**This is what defensible equity research looks like:** every number dated and sourced, every discretionary call logged with its reasoning. An interviewer asks *"where's the copper EBITDA from?"* → `AR25 p.21`; *"why an 8× multiple?"* → a written, peer-benchmarked rationale, not a guess.

> An **illustrative**, fully-offline variant (`python examples/bhp_sotp_demo.py`) exercises the same machinery with placeholder data and a bottom-up production DCF — handy for a quick end-to-end run with no report or network.

## How it works

```
 yfinance ──► scaffold (UNVERIFIED facts) ─┐
                                           ├─► elicitation wizard ──► guardrails ──► LEDGER ──► compute_wacc ──► results
 analyst (filings + judgement) ────────────┘     (source+rationale)   (warn/override)  (JSON)      (WACCComponents)
```

1. **Scaffold** — `src/data_scaffold.py` pulls the fast-moving market data (price, shares, market cap, a raw beta to sanity-check against) and pre-fills the ledger as **unverified** entries. Reported fundamentals are *not* trusted from here — for a deep valuation they come from the filings.
2. **Elicit** — `src/wizard.py` runs a question bank (`src/question_banks.py`); each discretionary input captures value + source + citation + rationale (+ method) and runs its guardrails.
3. **Ledger** — `src/ledger.py` validates the tiered field policy and stores every input with full provenance; computed outputs are snapshotted separately.
4. **Compute** — `compute_wacc()` assembles the inputs via `WACCComponents`, then runs the cross-checks (WACC band, WACC > g, weights sum to 1, cost of debt > rf).

## Entering real data (the template)

[`templates/bhp_template.json`](templates/bhp_template.json) is a fill-in skeleton — WACC inputs, commodity decks, divisions/assets, and group adjustments — every value starting `null` with a `FILL` citation. Enter primary-source data there and run:

```bash
python -m src.template_loader templates/bhp_template.json
```

It prints a **readiness report** (e.g. `1/67 inputs filled`) listing exactly what's still missing; once everything is filled it writes the note and Excel from your cited data and drops the "illustrative" banner. See [`docs/DATA_ENTRY.md`](docs/DATA_ENTRY.md).

## Repository layout

```
equity-valuation-models/
├── value.py                      # CLI: scaffold -> elicit -> compute -> save ledger
├── showcase.ipynb               # rendered end-to-end walkthrough (read it on GitHub)
├── src/
│   ├── ledger.py                 # the assumption-and-evidence ledger (the spine)
│   ├── guardrails.py             # deterministic reasonableness checks
│   ├── wizard.py                 # elicitation engine (pure core + CLI loop)
│   ├── question_banks.py         # WACC + mining commodity-deck banks
│   ├── data_scaffold.py          # yfinance market-data scaffold (unverified)
│   ├── sotp.py                   # sum-of-parts valuation (asset -> division -> group)
│   ├── comps.py                  # EV/EBITDA SOTP + normalized-FCF DCF cross-check
│   ├── note.py                   # markdown research-note generator (ledger as appendix)
│   ├── excel_model.py            # openpyxl workbook (cover, valuation, WACC, assumptions, sensitivity)
│   ├── template_loader.py        # read a filled JSON template -> ledger + note + Excel
│   ├── validate_citations.py     # checks ledger citations resolve in the source PDF
│   ├── valuation.py              # WACC, DCF, comparables, precedent transactions
│   ├── sector_models.py          # mining/NAV, SaaS, REIT, banking models
│   ├── three_statement.py        # articulated 3-statement model that foots + integrity validator
│   └── financial_statements.py   # P&L builder + provenance types (Assumption, SourceOfTruth)
├── tests/                        # 62 tests: ledger, guardrails, wizard, scaffold, 3-statement, sotp, comps, note, mining, excel, template
├── examples/
│   ├── bhp_sotp_real.py          # REAL BHP valuation from FY25 filing + live market data
│   ├── bhp_sotp_demo.py          # end-to-end illustrative BHP SOTP -> note + Excel
│   └── mining_nav_example.py     # synthetic NAV mechanics demo (not a real company)
├── data/
│   ├── ledger/bhp_sources.csv    # every extracted fact with page citation + exact reference
│   └── processed/VERSIONING.md   # FY25 vs HY26 input comparison + staleness guide
├── models/                       # generated ledgers (e.g. BHP_AX.json, BHP_sotp.json)
├── output/                       # generated note + workbook (BHP_research_note.md, BHP_model.xlsx)
├── templates/                    # bhp_template.json — fill-in data-entry skeleton
└── docs/
    ├── SCHEMA.md                 # the ledger schema reference
    ├── DATA_ENTRY.md             # how to fill the template
    ├── elicitation_design.md     # the wizard / banks / guardrails design
    ├── METHODOLOGY.md            # valuation philosophy & workflow
    └── SECTOR_GUIDES.md          # mining / SaaS / REIT / banking deep-dives
```

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| **1** | Ledger · guardrails · wizard · WACC bank · scaffold · CLI · articulated 3-statement model · tests | **Built & tested** |
| **2** | SOTP engine · mining commodity-deck bank + guardrails · **research-note generator** (ledger appendix) · end-to-end illustrative BHP demo | **Machinery built & tested** *(swap illustrative inputs for primary-source BHP data)* |
| **3** | `openpyxl` Excel model — Cover · Valuation (SOTP) · WACC · Assumptions (colour-coded ledger) · Sensitivity (2-way grid + scenario chart) | **Built & tested** |
| later | Terminal-value bank; SaaS/REIT/bank banks; per-asset discount rates; optional LLM "blind-spot" helper (suggests challenge questions, never decides) | Planned |

Stage 2's bottleneck is deliberately *not* code — it's sourcing and verifying BHP's asset-level data from the filings, and forming defensible price decks and discount rates. That judgement is the work the ledger exists to capture.

## Documentation

- [`docs/SCHEMA.md`](docs/SCHEMA.md) — the ledger: fields, the two credibility axes, the tiered policy.
- [`docs/DATA_ENTRY.md`](docs/DATA_ENTRY.md) — how to fill the BHP template with primary-source data.
- [`docs/elicitation_design.md`](docs/elicitation_design.md) — banks, the hybrid method model, the guardrail catalogue, the WACC bank.
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) and [`docs/SECTOR_GUIDES.md`](docs/SECTOR_GUIDES.md) — valuation philosophy and sector approaches.

## Disclaimer

Personal project work, shared to demonstrate analytical and technical capability. It is general information and educational material only, not financial product advice, and I am not licensed to provide financial advice. Demo figures are illustrative. Always verify against primary disclosures before any investment decision.

---

*Fundamental equity research & valuation tooling — part of [henrydate](https://github.com/henrydate).*
