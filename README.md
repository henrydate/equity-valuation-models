# Equity Valuation Models

A framework for valuing individual stocks. The core idea: a valuation is only as good as its assumptions, so every assumption in this repo is sourced from a primary document, logged with a rationale, and checked against reasonableness tests before it can count.

This is not a formula library. It is a discipline system — one that forces an analyst to answer *where does this number come from?* at every step.

**Stack:** Python · pandas · numpy · yfinance · openpyxl · pytest · 62 passing tests

## What makes it different

Most valuation tools give you the maths. This one enforces the groundwork that makes the maths defensible.

**Every assumption is sourced.** Before a number enters the model, you specify where it came from — a company filing, a market consensus, your own judgement — and whether you have personally verified it. The tool tracks both dimensions on every entry, so an auto-scraped number that has not been checked is clearly distinguished from one you have verified against the annual report.

**Discretionary inputs are interrogated, not assumed.** For judgement calls — cost of capital, commodity price forecasts, long-run growth rates — the tool runs a structured question-and-answer process that will not accept a number without a written rationale.

**Reasonableness checks run automatically.** The model tests whether inputs make mathematical sense (for instance, the discount rate must exceed the assumed long-run growth rate, otherwise the valuation is infinite). If a check fails it flags a warning, and you can only proceed by logging a written explanation — the same "override with justification" discipline used by investment committees.

**Citations are an error-detection mechanism.** Every hard fact requires a page reference before it can be marked verified. During the BHP build, this caught a misread on page 21 of the annual report: the initial entry used the Escondida sub-segment figure (US$8.6bn) instead of the Total Copper line (US$12.7bn) — a 48% understatement that moved the valuation by roughly A$12 per share. The act of writing down the exact page and table made the error visible immediately. See the [methodology note](docs/METHODOLOGY.md#validation--data-quality) and [citation ledger](data/ledger/bhp_sources.csv).

**Fully reproducible.** No AI, no randomness — every run produces the same output from the same inputs.

## Quick start

```bash
pip install -r requirements.txt

python -m pytest tests/ -q                  # 62 passing
python examples/bhp_sotp_real.py            # real BHP valuation: FY25 annual report + live price
python examples/bhp_sotp_demo.py            # illustrative run — no report or internet needed
python value.py BHP.AX --demo               # cost-of-capital calculation only, fully offline
jupyter notebook showcase.ipynb             # end-to-end walkthrough
```

Prefer to read through it first? [`showcase.ipynb`](showcase.ipynb) renders the full pipeline — ledger, checks, cost of capital, sum-of-parts, sensitivity table, and the final research note — directly on GitHub with no installation needed.

## Worked example: BHP valuation from the FY2025 annual report

`python examples/bhp_sotp_real.py` values BHP Group using figures extracted from the FY2025 annual results (released 19 August 2025) and live market data. It runs two independent valuation methods and triangulates between them.

```
BHP Group Limited (BHP.AX) — REAL valuation (FY25 sourced)
Live price: A$59.82   shares: 5,081m   beta: 0.825   FX(USD/AUD): 0.69
Cost of equity: 8.16%   WACC: 7.90%
EV/EBITDA SOTP    -> A$49.08/share
Normalized DCF    -> A$58.35/share
Blended fair value-> A$53.71/share   vs market A$59.82  =>  -10%   (HOLD)
```

The two methods give different answers (A$49 vs A$58). The blended result sits about 10% below the market price — consistent with the market pricing in the value of BHP's copper growth pipeline and the Jansen potash mine, which are still under development and don't yet show up in trailing earnings.

### Every figure is dated and sourced

Below is a sample from the assumption ledger. Hard facts from the filing are marked verified; the EV/EBITDA multiples and discount rates are flagged as analyst judgement calls, each with a written rationale attached.

| Input | Value | Unit | As of | Source |
|---|---|---|---|---|
| Iron Ore underlying EBITDA | 14,396 | US$m | 2025-06-30 | AR25 p.21 |
| Copper underlying EBITDA | 12,701 | US$m | 2025-06-30 | AR25 p.21 |
| Net debt | 12,924 | US$m | 2025-06-30 | AR25 Note 21 |
| Non-controlling interests | 4,553 | US$m | 2025-06-30 | AR25 Note 18 |
| Equity beta | 0.825 | x | live | yfinance 5y (BHP.AX) |
| Copper EV/EBITDA multiple | 8.0 | x | 2026 | analyst — copper growth premium |

*EBITDA is earnings before interest, tax, depreciation and amortisation — the standard measure of operating profit used in mining valuations. Beta measures how much a stock moves relative to the broader market. Full provenance for all inputs is in the generated research note at `output/BHP_real_note.md`.*

### The sum-of-parts bridge

A sum-of-parts values each business segment separately, then adds them up. The bridge below shows how the per-share value is derived: each segment's earnings (EBITDA) is multiplied by a market multiple to get an implied enterprise value (the value of the whole business, debt included), then net debt and minority interests are deducted to reach equity value per share.

| Component | Value (A$m) | % of EV |
|---|---|---|
| Iron Ore | 114,745 | 42% |
| Copper | 147,250 | 54% |
| Coal | 4,179 | 2% |
| Potash / Jansen (invested capital) | 12,353 | 4% |
| Less: corporate overhead (capitalised) | (3,861) | -1% |
| **Enterprise value** | **274,667** | **100%** |
| Less: net debt | (18,729) | |
| Less: minority interests | (6,598) | |
| **Equity value** | **249,339** | |
| **Value per share** | **A$49.08** | |

Data sources: yfinance (BHP.AX, AUDUSD=X) for live market data; BHP *Financial results for the year ended 30 June 2025* for segment earnings p.21, net debt Note 21, minority interests Note 18, and depreciation Notes 11–12.

An **illustrative offline version** (`python examples/bhp_sotp_demo.py`) runs the same machinery with placeholder data — no annual report or internet connection needed.

## How the pipeline works

Data enters from two places. Live market data (share price, market cap, a raw beta figure) is pulled automatically from yfinance. Fundamental data (segment earnings, debt, tax rates) is entered by the analyst from company filings, because automated scraping cannot be trusted for a valuation that will be defended.

1. **Scaffold** — `src/data_scaffold.py` fetches live market data and pre-fills the ledger as unverified entries, clearly marked as such.
2. **Elicit** — `src/wizard.py` walks through a bank of questions for each judgement call. Inputs require a source and a written rationale before they are accepted.
3. **Ledger** — `src/ledger.py` records every input with its source type, verification status, and full provenance. Computed outputs are snapshotted alongside.
4. **Compute** — the WACC (weighted average cost of capital — the discount rate applied to future cash flows) is assembled from the elicited inputs and cross-checked for internal consistency.

## Entering your own data

[`templates/bhp_template.json`](templates/bhp_template.json) is a fill-in skeleton covering cost-of-capital inputs, commodity price forecasts, division-level operating data, and group adjustments. Every value starts as `null` with a `FILL` placeholder. Fill it in from the filings and run:

```bash
python -m src.template_loader templates/bhp_template.json
```

The tool prints a readiness report showing exactly what is still missing (e.g. `1/67 inputs filled`). Once complete it generates a research note and Excel model from your cited data. See [`docs/DATA_ENTRY.md`](docs/DATA_ENTRY.md).

## Repository layout

```
equity-valuation-models/
├── value.py                      # CLI entry point: scaffold -> elicit -> compute -> save
├── showcase.ipynb                # rendered end-to-end walkthrough (readable on GitHub)
├── src/
│   ├── ledger.py                 # the assumption-and-evidence ledger (the spine)
│   ├── guardrails.py             # reasonableness checks
│   ├── wizard.py                 # elicitation engine (structured Q&A + CLI)
│   ├── question_banks.py         # WACC + mining commodity-deck question banks
│   ├── data_scaffold.py          # yfinance market-data scaffold (unverified)
│   ├── sotp.py                   # sum-of-parts valuation engine
│   ├── comps.py                  # EV/EBITDA sum-of-parts + normalised DCF cross-check
│   ├── note.py                   # research note generator (markdown)
│   ├── excel_model.py            # Excel workbook builder (cover, valuation, WACC, assumptions, sensitivity)
│   ├── template_loader.py        # filled JSON template -> ledger + note + Excel
│   ├── validate_citations.py     # checks that ledger citations resolve in the source PDF
│   ├── valuation.py              # WACC, DCF, comparables, precedent transactions
│   ├── sector_models.py          # mining/NAV, SaaS, REIT, banking model templates
│   ├── three_statement.py        # income statement / balance sheet / cash flow model
│   └── financial_statements.py   # P&L builder + provenance types
├── tests/                        # 62 tests across all modules
├── examples/
│   ├── bhp_sotp_real.py          # real BHP valuation: FY25 filing + live market data
│   ├── bhp_sotp_demo.py          # illustrative BHP run (no filing or network needed)
│   └── mining_nav_example.py     # synthetic NAV mechanics walkthrough
├── data/
│   ├── ledger/bhp_sources.csv    # every extracted fact with page citation and exact reference
│   └── processed/VERSIONING.md   # period-by-period input comparison and staleness guide
├── templates/                    # bhp_template.json — fill-in data-entry skeleton
└── docs/
    ├── SCHEMA.md                 # ledger schema reference
    ├── DATA_ENTRY.md             # how to fill the BHP template
    ├── elicitation_design.md     # wizard design, question banks, guardrail catalogue
    ├── METHODOLOGY.md            # valuation philosophy, workflow, data-quality practices
    └── SECTOR_GUIDES.md          # mining / SaaS / REIT / banking sector approaches
```

## What else is planned

The current machinery covers a single name in full depth. Planned additions:

- Terminal-value question bank (exit-multiple and franchise-value alternatives to the perpetuity approach)
- Sector-specific question banks for SaaS, REITs, and banks (the `sector_models.py` scaffold is already built)
- Per-asset discount rates for mining valuations, rather than a single group-level rate

## Disclaimer

Personal project work, shared to demonstrate analytical and technical capability. General information only — not financial advice, and I am not licensed to provide it. Always verify figures against primary disclosures before making any investment decision.

*Fundamental equity research and valuation tooling — part of [henrydate](https://github.com/henrydate).*
