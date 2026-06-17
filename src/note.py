"""
Research-note generator
========================

Renders a :class:`~src.ledger.Ledger` (and an optional
:class:`~src.sotp.SumOfParts` result) into a markdown equity-research note.

The note's distinctive section is the **key-assumptions / provenance table**:
every discretionary judgement with its source, verification status, and the
analyst's rationale, plus a model-integrity appendix (audit summary, open
guardrail warnings, logged overrides). That table is what makes the valuation
defensible -- it is the ledger, rendered.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from .ledger import InputKind, Ledger, VerificationStatus


def _fmt(x) -> str:
    if isinstance(x, dict):
        return "; ".join(f"{k}: {v}" for k, v in x.items())
    if isinstance(x, (int, float)):
        return f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.4g}"
    return str(x)


def _md_table(headers: List[str], rows: List[List[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def _source_label(entry) -> str:
    return entry.source_type.name.replace("_", " ").title()


def render_note(ledger: Ledger, sotp=None, *, thesis: Optional[str] = None,
                recommendation: Optional[str] = None, illustrative: bool = True) -> str:
    L: List[str] = []
    L.append(f"# {ledger.company} ({ledger.ticker}) — Equity Research Note")
    L.append("")
    L.append(f"*Prepared {date.today().isoformat()} · valuation basis "
             f"{ledger.reporting_currency}; per-share in {ledger.presentation_currency}*")
    L.append("")
    if illustrative:
        L.append("> **⚠️ ILLUSTRATIVE — NOT INVESTMENT ADVICE.** Figures are placeholders to "
                 "demonstrate the framework. Assumptions are unverified and do **not** reflect "
                 "a real valuation. See the model-integrity appendix for what remains unverified.")
        L.append("")

    # --- Recommendation -------------------------------------------------
    target = None
    if sotp is not None:
        target = sotp.value_per_share()
    elif "value_per_share" in ledger.results:
        target = ledger.results["value_per_share"].get("value")
    current = ledger.value_of("group.share_price")

    L.append("## Recommendation")
    L.append("")
    L.append(f"- **Rating:** {recommendation or '—'}")
    same_ccy = ledger.reporting_currency == ledger.presentation_currency
    if target is not None:
        ccy = ledger.reporting_currency
        L.append(f"- **Target (per share):** {target:,.2f} {ccy}")
    if target is not None and current:
        if same_ccy:
            upside = target / current - 1
            L.append(f"- **Last price:** {current:,.2f} {ledger.presentation_currency}"
                     f"  →  **implied upside {upside:+.0%}**")
        else:
            # Comparing a target in the reporting currency to a price in the listing
            # currency is apples-to-oranges; show both and flag the missing FX step
            # rather than print a misleading percentage.
            L.append(f"- **Last price:** {current:,.2f} {ledger.presentation_currency}  ·  "
                     f"target {target:,.2f} {ledger.reporting_currency} — "
                     f"_FX conversion required before comparing (not applied)_")
    L.append("")

    # --- Thesis ---------------------------------------------------------
    L.append("## Investment thesis")
    L.append("")
    L.append(thesis or "_Thesis to be written by the analyst — the framework supplies the "
                       "valuation and the audit trail; the view is yours._")
    L.append("")

    # --- Valuation ------------------------------------------------------
    L.append("## Valuation — sum of the parts")
    L.append("")
    wacc = ledger.results.get("wacc", {}).get("value")
    coe = ledger.results.get("cost_of_equity", {}).get("value")
    if wacc is not None:
        line = f"Discount rate (WACC): **{wacc:.2%}**"
        if coe is not None:
            line += f"  ·  cost of equity {coe:.2%}"
        L.append(line)
        L.append("")
    if sotp is not None:
        tbl = sotp.summary_table()
        rows = []
        for comp, row in tbl.iterrows():
            pct = row["% of EV"]
            pct_str = f"{pct:.0%}" if pct == pct else ""  # NaN check
            rows.append([comp, _fmt(row["Value"]), pct_str])
        L.append(_md_table([f"Component ({ledger.reporting_currency}m)", "Value", "% of EV"], rows))
        L.append("")

    # --- Key assumptions & provenance (the ledger, rendered) ------------
    L.append("## Key assumptions & provenance")
    L.append("")
    disc = [e for e in ledger.entries.values() if e.kind == InputKind.DISCRETIONARY]
    if disc:
        rows = []
        for e in disc:
            verified = "✓" if e.verification == VerificationStatus.VERIFIED else "—"
            method = f" ({e.method})" if e.method else ""
            rows.append([e.label + method, _fmt(e.value), e.unit,
                         _source_label(e), verified, (e.rationale or "").replace("|", "/")])
        L.append(_md_table(["Input", "Value", "Unit", "Source", "Verified", "Rationale"], rows))
    else:
        L.append("_No discretionary inputs recorded._")
    L.append("")

    # --- Model integrity appendix --------------------------------------
    a = ledger.audit_summary()
    L.append("## Model integrity")
    L.append("")
    L.append(f"- Entries: {a['entries_total']}  ·  verified: {a['verified']}  ·  "
             f"unverified: {a['unverified']}")
    L.append(f"- Open guardrail warnings: {a['warnings_open']}  ·  overrides logged: "
             f"{a['overrides_logged']}")
    if ledger.open_warnings():
        L.append(f"- ⚠️ Unresolved: {', '.join(ledger.open_warnings())}")
    overrides = [(k, ov) for k, e in ledger.entries.items() for ov in e.overrides]
    if overrides:
        L.append("")
        L.append("**Logged overrides** (deviations proceeded past, with reason):")
        for k, ov in overrides:
            L.append(f"- `{k}`: {ov['reason']}")
    L.append("")

    # --- Disclaimer -----------------------------------------------------
    L.append("---")
    L.append("")
    L.append("*General information and educational material only, not financial product advice. "
             "Not licensed to provide financial advice. Verify against primary disclosures before "
             "any investment decision.*")
    L.append("")
    return "\n".join(L)


def write_note(path, ledger: Ledger, sotp=None, **kwargs) -> str:
    text = render_note(ledger, sotp, **kwargs)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text
