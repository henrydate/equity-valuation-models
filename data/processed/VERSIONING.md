# BHP Valuation Inputs — Version Control

Every time BHP releases results, key inputs change. This file tracks what changed,
why it matters, and what to update in the model.

---

## Input snapshots

| Period | Extraction date | Net debt | ETR (adjusted) | Group EBITDA | Copper EBITDA | D&A | Source doc |
|---|---|---|---|---|---|---|---|
| FY25 (30 Jun 2025) | 2025-08-19 | 12,924 | 37.2% | 25,978 | 12,701 | 5,540 | AR25 (19 Aug 2025 release) |
| HY26 (31 Dec 2025) | 2026-02-17 | 14,686 | 36.6% | ~13,050* | 7,952* | ~2,770* | HY26 (17 Feb 2026 release) |

\* HY26 figures are **half-year only** — not annualised, not comparable to FY25 full-year P&L.

---

## Key changes FY25 → HY26

| Metric | FY25 (full year) | HY26 (half year) | Δ | Valuation impact |
|---|---|---|---|---|
| **Net debt** | 12,924 | 14,686 | +1,762 (+13.6%) | Reduces equity value; flows directly through EV bridge |
| **ETR (adjusted)** | 37.2% | 36.6% | −60 bps | Minor NOPAT benefit; not material at group scale |
| **Copper EBITDA** | 12,701 | 7,952 | −4,749 | **Not comparable** — HY26 is 6 months, FY25 is 12 months |
| **D&A** | 5,540 | ~2,770 | −2,770 | **Not comparable** — same reason |

---

## Why HY26 P&L figures are NOT directly usable in the FY25 model

The SOTP and DCF are both built on **full-year (annualised) EBITDA**:

- FY25 = 12 months (1 Jul 2024 – 30 Jun 2025)
- HY26 = 6 months (1 Jul 2025 – 31 Dec 2025)

**Do not substitute HY26 EBITDA into a FY25 model** — you would halve the EBITDA
and produce a nonsensical valuation. Correct approaches:

1. **Use FY25 as the base** until FY26 full-year results (expected Aug 2026), updating
   only the balance sheet items (net debt, NCI) from HY26.

2. **Annualise HY26 EBITDA** (2× HY figure, then adjust for known seasonality) as a
   forward-run-rate estimate — flag as an analyst estimate, not a reported figure.

3. **Update to FY26 when available** (Aug 2026 release): full replacement of all
   P&L inputs from the new annual report.

---

## What to update quarter-to-quarter

| Cadence | Item to refresh | Source |
|---|---|---|
| Every results release (Feb + Aug) | Net debt, NCI | Balance sheet in results PDF |
| Every results release | Realised prices | Operational review tables |
| Annual (Aug only) | Segment EBITDA (full year) | Segment performance table (AR p.21 equivalent) |
| Annual (Aug only) | D&A, tax expense, ETR | Notes 6, 11, 12 in annual report |
| Live (via yfinance) | Share price, shares outstanding, beta, FX | `data_scaffold.py` / `bhp_sotp_real.py` auto-pull |
| Analyst judgement | Peer multiples (IO/Cu/coal EV/EBITDA) | Update when sector conditions shift significantly |

---

## Staleness check

Before using these inputs in a model, verify:

1. When was the last BHP results release? (Check bhp.com → Investors → Results)
2. Is a newer results PDF available that post-dates the extraction date above?
3. If yes: re-extract the balance sheet items (net debt, NCI) at minimum.

**Rule of thumb:** inputs more than 6 months old should be re-verified. Annual report
inputs are valid for 12 months (until the next FY release); net debt should be
refreshed every 6 months (HY and FY release cadence).

You can also run:

```bash
python src/validate_citations.py \
  --ledger data/ledger/bhp_sources.csv \
  --pdf data/raw/250819_bhpresults_fy25.pdf
```

to re-validate that the page citations still resolve correctly.
