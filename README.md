# Equity Valuation Models

**A single-name equity valuation framework built around one idea: a valuation is only as defensible as its assumptions — so every assumption is sourced, challenged, and logged.**

Most valuation repositories are formula libraries. This one adds the layer that actually matters in research: a deterministic **elicitation wizard** that interrogates each discretionary input (beta, equity risk premium, terminal growth, commodity price decks…), demands a source + rationale + confidence, runs reasonableness **guardrails**, and writes everything to an auditable **assumption-and-evidence ledger** — the appendix that makes a research note defensible.

> **Stack:** Python · pandas · numpy · yfinance · openpyxl · pytest · 62 passing tests

---

## What makes it different

- **Two credibility axes, not one.** Every input records *where it came from* (`source_type`) **and** *whether a human has checked it* (`verification`). An auto-scraped filing figure is high-source but unverified; a hard-reasoned estimate is lower-source but verified-by-you. (See [`docs/SCHEMA.md`](docs/SCHEMA.md).)
- **Judgement is elicited, not assumed.** Discretionary inputs go through a structured Q&A that captures the reasoning and won't let you record a number without a rationale.
- **Guardrails warn; they don't block.** Reasonableness checks (WACC > g, beta vs peers, terminal growth vs spot…) surface as warnings you may proceed past **only by logging a written override** — the committee model, automated.
- **Citations are an error-detection mechanism.** Every hard fact requires a page citation before it can be marked VERIFIED. During the BHP build, this caught a segment-line vs. total-line misread on AR25 p.21 (Escondida US$8.6bn taken as the copper total instead of US$12.7bn — a 48% understatement, ~A$12/share impact). See the [methodology note](docs/METHODOLOGY.md#validation--data-quality) and [citation ledger](data/ledger/bhp_sources.csv).
- **Deterministic.** No LLM, no randomness, no API keys — fitting for a tool whose whole pitch is *truth*, and fully reproducible offline.

## Quick start

```bash
pip install -r requirements.txt

python -m pytest tests/ -q                  # 62 passing
python examples/bhp_sotp_real.py            # real BHP valuation: FY25 filing + live data
python examples/bhp_sotp_demo.py            # illustrative SOTP offline -> note + Excel
python value.py BHP.AX --demo               # WACC spine only, fully offline
jupyter notebook showcase.ipynb             # end-to-end pipeline, rendered
```

**Prefer to just read it?** [`showcase.ipynb`](showcase.ipynb) renders the entire pipeline — ledger, guardrails, WACC, SOTP, sensitivity, and the final note — directly on GitHub, no install required.

## Worked example — real BHP valuation (FY25)

`python examples/bhp_sotp_real.py` values BHP from **primary-source FY2025 data** (results PDF, segment table p.21) plus live market data, triangulating two independent methods:

```
BHP Group Limited (BHP.AX) — REAL valuation (FY25 sourced)
Live price: A$59.82   shares: 5,081m   beta: 0.825   FX(USD/AUD): 0.69
Cost of equity: 8.16%   WACC: 7.90%
EV/EBITDA SOTP    -> A$49.08/share
Normalized DCF    -> A$58.35/share
Blended fair value-> A$53.71/share   vs market A$59.82  =>  -10%   (HOLD)
```

The two methods bracket fair value; the market sits ~10% above, consistent with pricing the copper growth pipeline and Jansen potash ramp that *trailing* FY25 earnings don't yet capture.

### The ledger: every figure dated, sourced, verifiable

| Input | Value | Unit | As of | Source & citation |
|---|---|---|---|---|
| Iron Ore underlying EBITDA | 14,396 | US$m | 2025-06-30 | AR25 p.21 |
| Copper underlying EBITDA | 12,701 | US$m | 2025-06-30 | AR25 p.21 |
| Net debt | 12,924 | US$m | 2025-06-30 | AR25 Note 21 |
| Non-controlling interests | 4,553 | US$m | 2025-06-30 | AR25 Note 18 |
| Equity beta | 0.825 | x | live | yfinance 5y (BHP.AX) |
| Copper EV/EBITDA multiple | 8.0 | x | 2026 | analyst — copper growth premium |

*Hard facts from the filing are verified; multiples, WACC, and perpetuity growth are flagged **discretionary** calls, each with a written rationale. Full provenance in `output/BHP_real_note.md`.*

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

**Data sources:** market — yfinance (BHP.AX, AUDUSD=X), live; fundamentals — BHP *Financial results for the year ended 30 June 2025* (19 Aug 2025): segment EBITDA p.21, net debt Note 21, NCI Note 18, D&A Notes 11–12.

> An **illustrative**, fully-offline variant (`python examples/bhp_sotp_demo.py`) exercises the same machinery with placeholder data — useful for a quick end-to-end run with no report or network access.

## How it works

```
 yfinance ──► scaffold (UNVERIFIED facts) ─┐
                                           ├─► elicitation wizard ──► guardrails ──► LEDGER ──► compute_wacc ──► results
 analyst (filings + judgement) ────────────┘     (source+rationale)   (warn/override)  (JSON)      (WACCComponents)
```

1. **Scaffold** — `src/data_scaffold.py` pulls live market data (price, shares, cap, beta) and pre-fills the ledger as **unverified** entries. Reported fundamentals are *not* trusted from here — for a deep valuation they come from the filings.
2. **Elicit** — `src/wizard.py` runs a question bank; each discretionary input captures value + source + citation + rationale and runs its guardrails.
3. **Ledger** — `src/ledger.py` validates the tiered field policy and stores every input with full provenance.
4. **Compute** — `compute_wacc()` assembles inputs via `WACCComponents` and runs cross-checks (WACC band, WACC > g, weights sum to 1).

## Entering real data (the template)

[`templates/bhp_template.json`](templates/bhp_template.json) is a fill-in skeleton — WACC inputs, commodity decks, divisions/assets, and group adjustments — every value `null` with a `FILL` citation. Enter primary-source data and run:

```bash
python -m src.template_loader templates/bhp_template.json
```

It prints a readiness report (`1/67 inputs filled`) listing what's still missing; once complete, it writes the note and Excel from your cited data. See [`docs/DATA_ENTRY.md`](docs/DATA_ENTRY.md).

## Repository layout

```
equity-valuation-models/
├── value.py                      # CLI: scaffold -> elicit -> compute -> save ledger
├── showcase.ipynb                # rendered end-to-end walkthrough (read it on GitHub)
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
│   ├── template_loader.py        # filled JSON template -> ledger + note + Excel
│   ├── validate_citations.py     # checks ledger citations resolve in the source PDF
│   ├── valuation.py              # WACC, DCF, comparables, precedent transactions
│   ├── sector_models.py          # mining/NAV, SaaS, REIT, banking models
│   ├── three_statement.py        # articulated 3-statement model + integrity validator
│   └── financial_statements.py   # P&L builder + provenance types
├── tests/                        # 62 tests across all modules
├── examples/
│   ├── bhp_sotp_real.py          # real BHP valuation: FY25 filing + live market data
│   ├── bhp_sotp_demo.py          # illustrative BHP SOTP -> note + Excel (offline)
│   └── mining_nav_example.py     # synthetic NAV mechanics demo
├── data/
│   ├── ledger/bhp_sources.csv    # every extracted fact with page citation + exact reference
│   └── processed/VERSIONING.md   # FY25 vs HY26 input comparison + staleness guide
├── templates/                    # bhp_template.json — fill-in data-entry skeleton
├── docs/
│   ├── SCHEMA.md                 # ledger schema: fields, credibility axes, tiered policy
│   ├── DATA_ENTRY.md             # how to fill the BHP template
│   ├── elicitation_design.md     # wizard, banks, guardrail catalogue
│   ├── METHODOLOGY.md            # valuation philosophy, workflow, data-quality practices
│   └── SECTOR_GUIDES.md          # mining / SaaS / REIT / banking deep-dives
├── models/                       # generated ledgers (gitignored)
└── output/                       # generated notes + workbooks (gitignored)
```

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| **1** | Ledger · guardrails · wizard · WACC bank · scaffold · CLI · 3-statement model · tests | **Complete** |
| **2** | SOTP engine · mining commodity-deck bank · research-note generator · real BHP SOTP + DCF from FY25 filing | **Complete** |
| **3** | Excel model — Cover · Valuation · WACC · Assumptions (colour-coded ledger) · Sensitivity grid | **Complete** |
| Later | Terminal-value bank; SaaS/REIT/bank sector banks; per-asset discount rates | Planned |

## Disclaimer

Personal project work, shared to demonstrate analytical and technical capability. General information and educational material only — not financial product advice, and I am not licensed to provide financial advice. Always verify against primary disclosures before any investment decision.

---

*Fundamental equity research & valuation tooling — part of [henrydate](https://github.com/henrydate).*
