# The Elicitation Wizard

The signature feature. A deterministic wizard that, when you set a discretionary
input, asks you the right questions, demands a source + rationale + confidence,
runs reasonableness **guardrails**, and writes a fully-provenanced
[ledger](SCHEMA.md) entry. No LLM, no network, no randomness — fitting for a
tool whose whole pitch is *truth*.

Implemented in [`src/wizard.py`](../src/wizard.py) (engine),
[`src/question_banks.py`](../src/question_banks.py) (the banks), and
[`src/guardrails.py`](../src/guardrails.py) (the checks).

## Banks and input specs

A **bank** is an ordered list of **input specs**. Each spec is plain data:

```python
{
  "key": "wacc.equity_beta",          # ledger key
  "label": "Equity beta",
  "unit": "x",
  "kind": InputKind.DISCRETIONARY,
  "prompt": "Equity beta?",
  "anchor": "Diversified-miner peers unlevered ~0.8-1.0; Damodaran sector ~0.9.",
  "default_source_type": SourceOfTruth.ANALYST_ESTIMATE,
  "default_method": "bottom_up",
  "methods": { "bottom_up": {...}, "regression": {...}, "comparable": {...} },
  "guardrails": [ ... ],              # input-level checks
}
```

The **anchor** is shown to the analyst to orient judgement (here's what's
normal, here's the current level) — it is *not* the answer. Adding a new input
is data, not code.

## The hybrid method model

Where methods genuinely compete, an input carries a **method registry**: a
house **default** plus alternatives, each with its own sub-questions and
guardrails. Switching method is a first-class choice (recorded as
`method` + `method_default: false`), distinct from overriding a warning.

Of the seven WACC inputs, four have real method plurality; the rest are
single-method with only a *source* choice:

| Input | Methods |
|---|---|
| beta | bottom-up *(default)* · regression · comparable |
| ERP | implied *(default)* · historical |
| cost of debt | rating-implied *(default)* · actual-from-debt-note |
| capital structure | current market · target through-cycle *(roadmap)* |
| risk-free, tax, currency | single-method (source choice only) |

## Tiered fields (the friction dial)

The wizard forces only what rigour requires (see [SCHEMA.md](SCHEMA.md)):
always `value · unit · source_type · citation · as_of · verification`;
`rationale` only for discretionary inputs and overrides; engine-written fields
(guardrails, provenance, timestamps) never prompt. This keeps the wizard usable
on a 10-year price deck or a per-mine schedule.

## Guardrails: warn, don't block

A check returns **PASS / WARN / FAIL** with a message. Per the committee model,
*nothing hard-blocks* — a WARN/FAIL is surfaced and may be proceeded past only
by **logging an override with a written reason**. Deviate if you must, but
justify it, and the justification is captured forever.

Checks are registered by name and parametrised via `params`:

| Check | Fires | Severity |
|---|---|---|
| `within_range` | scalar outside an expected band (beta, ERP, rf, tax) | WARN |
| `wacc_gt_g` | WACC ≤ terminal growth (DCF diverges) | FAIL |
| `weights_sum_to_1` | capital-structure weights ≠ 1 | FAIL |
| `cost_of_debt_gt_rf` | cost of debt ≤ risk-free | WARN |
| `long_run_vs_spot` | price-deck long-run far from spot | WARN |
| `vs_scaffold_within` | verified value diverges from the auto-pulled scaffold | WARN |
| `relever_gearing_matches_weights` | beta re-levered at a gearing ≠ the WACC weights | WARN |

**Input-level** checks run at elicitation time; **cross-input** checks
(`wacc_gt_g`, `weights_sum_to_1`, the WACC band) run at assembly, when the full
context exists. A cross-input check defers (PASS) if its context isn't set yet.

## The WACC bank — the template

`python value.py BHP.AX` runs the WACC bank, currency-gated:

| # | Input | Anchor (illustrative) | Guardrail |
|---|---|---|---|
| 0 | currency basis | USD functional; convert /share to AUD at spot | rf/ERP must match |
| 1 | risk-free | US 10Y ~4.2% · AU 10Y ~4.3% | band 1–8% |
| 2 | ERP | implied ~4.8% · historical ~6% | band 3.5–7.5% |
| 3 | beta | peers unlevered ~0.8–1.0 | band 0.7–1.3; re-lever = weights |
| 4 | cost of debt | A-rated → rf + ~1.1% → ~5.3% | > rf |
| 5 | tax | AUS statutory 30% | band 0–50% |
| 6 | mv equity | scaffold market cap | within 5% of scaffold |
| 7 | mv (net) debt | BHP net debt ~US$10bn | — |

Then `compute_wacc()` assembles these via `WACCComponents`, snapshots WACC +
cost of equity to `results`, and runs the cross-checks.

## Extending

A new bank (terminal value, the commodity price deck, a SaaS/REIT/bank input
set) is a new list of specs in `question_banks.py` plus any new named checks in
`guardrails.py`. The WACC bank is the pattern every other one copies.
