# The Assumption-and-Evidence Ledger

The ledger is the spine of the framework. Every number a valuation touches —
an auto-pulled fact, an analyst-verified fact, or an elicited discretionary
judgement — is one auditable entry. "Verify a fact" and "elicit a judgement"
are two modes of writing the *same* ledger.

Implemented in [`src/ledger.py`](../src/ledger.py).

## Top-level structure

A ledger is one JSON file per company (`models/<ticker>.json`):

```jsonc
{
  "company": "BHP Group Limited",
  "ticker": "BHP.AX",
  "reporting_currency": "USD",       // functional currency
  "presentation_currency": "AUD",    // listing currency
  "model_created": "2026-06-16",
  "model_last_updated": "2026-06-16",
  "entries": { "<key>": { ...entry... }, ... },   // the inputs (provenance-bearing)
  "results": { "<key>": { ...computed... }, ... },// derived outputs (NOT provenance)
  "audit":   { ...summary... }                    // regenerated on save
}
```

**Inputs are authoritative; results are derived.** The engine computes WACC,
cost of equity, EV, per-share, etc. and snapshots them under `results` flagged
`"computed": true`. Provenance lives only on inputs.

## Entry fields

| Field | Meaning | Required? |
|---|---|---|
| `value` | scalar **or** a per-year map (`{"2027": 95, …, "long_run": 75}`) | always |
| `label` | human-readable name | always |
| `unit` | `%`, `x`, `USD/t`, `m shares`, … | always |
| `kind` | `hard_fact` or `discretionary` — the two modes | always |
| `source_type` | `MANAGEMENT_GUIDANCE` / `COMPANY_FILING` / `BROKER_CONSENSUS` / `ANALYST_ESTIMATE` / `EXTERNAL_DATA` / `ASSUMPTION` | always |
| `citation` | exact locator — `"BHP FY25 Annual Report p.184"`, not `"annual report"` | always |
| `as_of` | ISO date the value is valid as of (critical for price, beta) | always |
| `verification` | `unverified` → `verified` | always |
| `rationale` | the analyst's reasoning | **discretionary + overrides only** |
| `method` / `method_default` | which method path was used; did it stay on the house default | multi-method inputs |
| `guardrail_results` | checks run + `pass`/`warn`/`fail` + message | engine-written |
| `overrides` | logged `{reason, by, at}` when proceeding past a warning | when overridden |
| `provenance_method` | `auto_pull` / `wizard` / `manual_override` / `manual` | engine-written |
| `entered_by`, `entered_at` | who/when recorded the entry | engine-written |
| `scaffold_value` | the auto-pulled value, retained when an analyst overrides it | scaffold/override |

The "Required?" column **is** the tiered field policy: a clean hard fact needs
a citation but no rationale; a discretionary input always needs a rationale;
every override needs a reason. `Ledger.add()` enforces this via
`LedgerEntry.validate()`.

## The two credibility axes

`source_type` and `verification` are **orthogonal**, and keeping them separate
is the point:

- A filing figure *auto-scraped* is **high source-type, unverified**.
- An analyst estimate you reasoned hard about is **lower source-type,
  verified-by-you**.

Collapsing them into a single "confidence" number throws away exactly the
distinction the framework is about.

## Two kinds, one ledger

| `kind` | Discipline applied | Example |
|---|---|---|
| `hard_fact` | provenance (citation) + integrity/scaffold checks | shares outstanding, reported revenue, last close |
| `discretionary` | the elicitation wizard: source + rationale + confidence + guardrails | beta, ERP, terminal growth, commodity price deck |

## History & overrides

Full history is the **git diff** — every save is a commit, so the diff *is* the
audit trail. Only analytically meaningful **overrides** are kept inline
(deviating past a guardrail warning, with a written reason). A method switch is
recorded separately via `method` / `method_default` — a *method choice* and an
*override* are distinct audit concepts.

## Audit summary

Regenerated on every save:

```jsonc
"audit": { "entries_total": 12, "verified": 8, "unverified": 4,
           "warnings_open": 0, "overrides_logged": 0 }
```

`warnings_open` counts entries with an unresolved `warn`/`fail` and no override —
the work-still-to-do list before a model is presentable.
