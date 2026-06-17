"""
Elicitation wizard
===================

Runs a question bank: for each input it asks the analyst the right questions,
captures value + source + citation + rationale (+ method), runs the input's
guardrails, logs any override, and writes a :class:`LedgerEntry`.

The pure core (:func:`build_entry`, :func:`compute_wacc`) is separated from the
CLI I/O (:func:`run_bank`) so the logic can be unit-tested with canned answers,
no stdin required.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from .ledger import InputKind, Ledger, LedgerEntry, VerificationStatus
from .financial_statements import SourceOfTruth
from .guardrails import CheckStatus, GuardrailResult, attach, run_checks, worst_status
from .valuation import WACCComponents

_WACC_INPUTS = [
    "wacc.risk_free", "wacc.erp", "wacc.equity_beta",
    "wacc.cost_of_debt", "wacc.tax_rate", "wacc.mv_equity", "wacc.mv_debt",
]


def _resolve_guardrails(spec: dict, method: Optional[str]) -> list:
    specs = list(spec.get("guardrails", []))
    methods = spec.get("methods")
    if method and methods and method in methods:
        specs += methods[method].get("guardrails", [])
    return specs


def build_entry(spec: dict, answers: dict,
                context: Optional[dict] = None) -> Tuple[LedgerEntry, List[GuardrailResult]]:
    """Pure: turn an input spec + analyst answers into a guardrail-checked entry.

    ``answers`` keys: value (required), citation, rationale, source_type,
    method, as_of, verification, override_reason.
    """
    default_method = spec.get("default_method")
    method = answers.get("method") or default_method

    entry = LedgerEntry(
        key=spec["key"],
        label=spec["label"],
        value=answers["value"],
        unit=spec.get("unit", ""),
        kind=spec.get("kind", InputKind.DISCRETIONARY),
        source_type=answers.get("source_type") or spec.get("default_source_type", SourceOfTruth.ANALYST_ESTIMATE),
        citation=answers.get("citation", ""),
        as_of=answers.get("as_of") or date.today().isoformat(),
        verification=answers.get("verification", VerificationStatus.VERIFIED),
        rationale=answers.get("rationale"),
        method=method,
        method_default=(method == default_method) if method is not None else None,
        provenance_method="wizard",
    )
    results = attach(entry, _resolve_guardrails(spec, method), context=context, value=entry.value)
    if entry.has_open_warning and answers.get("override_reason"):
        entry.add_override(answers["override_reason"])
    return entry, results


def compute_wacc(ledger: Ledger) -> float:
    """Assemble WACC from ledger entries, snapshot it, and run cross-checks."""
    missing = [k for k in _WACC_INPUTS if ledger.get(k) is None]
    if missing:
        raise ValueError("compute_wacc missing inputs: " + ", ".join(missing))

    g = ledger.value_of
    comp = WACCComponents(
        risk_free_rate=g("wacc.risk_free"),
        market_risk_premium=g("wacc.erp"),
        equity_beta=g("wacc.equity_beta"),
        cost_of_debt_pre_tax=g("wacc.cost_of_debt"),
        tax_rate=g("wacc.tax_rate"),
        market_value_equity=g("wacc.mv_equity"),
        market_value_debt=g("wacc.mv_debt"),
    )
    wacc = comp.wacc()
    total = comp.market_value_equity + comp.market_value_debt
    weight_equity, weight_debt = comp.market_value_equity / total, comp.market_value_debt / total

    ledger.set_result("cost_of_equity", round(comp.cost_of_equity(), 4), unit="%")
    ledger.set_result("wacc", round(wacc, 4), unit="%", inputs=_WACC_INPUTS)

    cross = run_checks(
        [{"check": "within_range", "params": {"range": [0.08, 0.12]}},
         "cost_of_debt_gt_rf", "weights_sum_to_1"],
        value=wacc,
        context={
            "cost_of_debt": comp.cost_of_debt_pre_tax, "rf": comp.risk_free_rate,
            "weight_equity": weight_equity, "weight_debt": weight_debt,
        },
    )
    ledger.results["wacc"]["cross_checks"] = [r.to_dict() for r in cross]
    return wacc


# --------------------------------------------------------------------------
# CLI I/O (thin wrapper around build_entry; not unit-tested -- uses stdin)
# --------------------------------------------------------------------------
def _ask(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"  {prompt}{suffix}: ").strip() or (default or "")


def run_bank(bank: List[dict], ledger: Ledger, context: Optional[dict] = None) -> Ledger:
    context = context or {}
    print(f"\n=== Eliciting {len(bank)} inputs ===")
    for spec in bank:
        print(f"\n{spec['label']}  ({spec['key']})")
        if spec.get("anchor"):
            print(f"  anchor: {spec['anchor']}")

        method = spec.get("default_method")
        if spec.get("methods"):
            print("  methods: " + ", ".join(spec["methods"].keys()))
            method = _ask("method", method) or method

        raw = _ask("value")
        try:
            value = float(raw)
        except ValueError:
            value = raw
        citation = _ask("citation / source")
        rationale = None
        if spec.get("kind", InputKind.DISCRETIONARY) == InputKind.DISCRETIONARY:
            rationale = _ask("rationale (why this value)")

        answers = {"value": value, "citation": citation, "rationale": rationale, "method": method}
        entry, results = build_entry(spec, answers, context=context)

        for r in results:
            if r.status != CheckStatus.PASS:
                print(f"  [{r.status.value.upper()}] {r.message}")
        if entry.has_open_warning:
            reason = _ask("override reason (leave blank to revise later)")
            if reason:
                entry.add_override(reason)

        try:
            ledger.add(entry)
        except ValueError as exc:
            print(f"  ! not saved -- {exc}")
    return ledger
