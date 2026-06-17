"""
Guardrail engine
================

Deterministic sanity checks on ledger inputs and on derived results. A check
returns PASS, WARN or FAIL with a human-readable message. Per the locked
design *nothing hard-blocks*: a WARN/FAIL is surfaced and may be proceeded past
only by logging an override on the ledger entry (the committee model -- deviate
if you must, but justify it in writing).

Checks are registered by name so the question bank can attach the right checks
to each input, parametrised via ``params`` (e.g. a peer range for beta).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class GuardrailResult:
    check: str
    status: CheckStatus
    message: str = ""
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"check": self.check, "status": self.status.value, "message": self.message}
        if self.detail:
            d["detail"] = self.detail
        return d


# A check is a function (value, context) -> GuardrailResult.
CheckFn = Callable[[Any, Dict[str, Any]], GuardrailResult]


def _name(ctx: Dict[str, Any], default: str) -> str:
    return ctx.get("check_name", default)


def check_within_range(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    """WARN if a scalar falls outside an expected ``range`` = (lo, hi)."""
    name = _name(ctx, "within_range")
    lo, hi = ctx["range"]
    if value is None:
        return GuardrailResult(name, CheckStatus.WARN, "no value to range-check")
    if lo <= value <= hi:
        return GuardrailResult(name, CheckStatus.PASS, f"{value} within [{lo}, {hi}]")
    return GuardrailResult(name, CheckStatus.WARN,
                           f"{value} is outside the expected range [{lo}, {hi}] -- justify or revise")


def check_wacc_gt_g(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    """FAIL if WACC <= terminal growth (the DCF diverges -- a hard error)."""
    wacc, g = ctx["wacc"], ctx["g"]
    if wacc > g:
        return GuardrailResult("wacc_gt_g", CheckStatus.PASS, f"WACC {wacc:.2%} > g {g:.2%}")
    return GuardrailResult("wacc_gt_g", CheckStatus.FAIL,
                           f"WACC {wacc:.2%} must exceed terminal growth {g:.2%} -- DCF diverges")


def check_cost_of_debt_gt_rf(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    cod, rf = ctx["cost_of_debt"], ctx["rf"]
    if cod > rf:
        return GuardrailResult("cost_of_debt_gt_rf", CheckStatus.PASS,
                               f"cost of debt {cod:.2%} > risk-free {rf:.2%}")
    return GuardrailResult("cost_of_debt_gt_rf", CheckStatus.WARN,
                           f"cost of debt {cod:.2%} is not above the risk-free rate {rf:.2%}")


def check_weights_sum_to_1(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    we, wd = ctx["weight_equity"], ctx["weight_debt"]
    tol = ctx.get("tol", 1e-6)
    total = we + wd
    if abs(total - 1.0) <= tol:
        return GuardrailResult("weights_sum_to_1", CheckStatus.PASS, "capital-structure weights sum to 1.0")
    return GuardrailResult("weights_sum_to_1", CheckStatus.FAIL,
                           f"weights sum to {total:.4f}, must be 1.0")


def check_long_run_vs_spot(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    """WARN if a price deck's long-run level deviates materially from spot."""
    name = _name(ctx, "long_run_vs_spot")
    spot = ctx.get("spot")
    threshold = ctx.get("threshold", 0.25)
    long_run = value.get("long_run") if isinstance(value, dict) else value
    if long_run is None or not spot:
        return GuardrailResult(name, CheckStatus.WARN, "cannot compare long-run to spot")
    dev = (long_run - spot) / spot
    if abs(dev) <= threshold:
        return GuardrailResult(name, CheckStatus.PASS,
                               f"long-run {long_run} within {threshold:.0%} of spot {spot}")
    return GuardrailResult(name, CheckStatus.WARN,
                           f"long-run {long_run} is {dev:+.0%} vs spot {spot} -- confirm intentional")


def check_vs_scaffold_within(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    """WARN if a verified value diverges from the auto-pulled scaffold value."""
    name = _name(ctx, "vs_scaffold_within")
    scaffold = ctx.get("scaffold_value")
    tol = ctx.get("tol_pct", 0.02)
    if not scaffold:
        return GuardrailResult(name, CheckStatus.PASS, "no scaffold value to compare")
    dev = abs(value - scaffold) / abs(scaffold)
    if dev <= tol:
        return GuardrailResult(name, CheckStatus.PASS,
                               f"{value} within {tol:.0%} of scaffold {scaffold}")
    return GuardrailResult(name, CheckStatus.WARN,
                           f"{value} differs {dev:.0%} from scaffold {scaffold} -- verify source")


def check_relever_gearing_matches_weights(value: Any, ctx: Dict[str, Any]) -> GuardrailResult:
    """WARN if beta was re-levered at a gearing that differs from the WACC weights.

    Cross-input: at beta-elicitation time the capital-structure weights may not
    be set yet, so the check defers (PASS) until both gearings are known.
    """
    if "relever_gearing" not in ctx or "weights_gearing" not in ctx:
        return GuardrailResult("relever_gearing_matches_weights", CheckStatus.PASS,
                               "re-lever consistency deferred until capital structure is set")
    rg, wg = ctx["relever_gearing"], ctx["weights_gearing"]
    tol = ctx.get("tol", 0.02)
    if abs(rg - wg) <= tol:
        return GuardrailResult("relever_gearing_matches_weights", CheckStatus.PASS,
                               f"beta re-levered at {rg:.0%} gearing, consistent with weights")
    return GuardrailResult("relever_gearing_matches_weights", CheckStatus.WARN,
                           f"beta re-levered at {rg:.0%} gearing but capital structure uses {wg:.0%}")


REGISTRY: Dict[str, CheckFn] = {
    "within_range": check_within_range,
    "wacc_gt_g": check_wacc_gt_g,
    "cost_of_debt_gt_rf": check_cost_of_debt_gt_rf,
    "weights_sum_to_1": check_weights_sum_to_1,
    "long_run_vs_spot": check_long_run_vs_spot,
    "vs_scaffold_within": check_vs_scaffold_within,
    "relever_gearing_matches_weights": check_relever_gearing_matches_weights,
}

# A spec is either a check name, or {"check": name, "params": {...}}.
CheckSpec = Union[str, Dict[str, Any]]


def run_checks(specs: List[CheckSpec], value: Any = None,
               context: Optional[Dict[str, Any]] = None) -> List[GuardrailResult]:
    context = context or {}
    results: List[GuardrailResult] = []
    for spec in specs:
        if isinstance(spec, str):
            spec = {"check": spec}
        name = spec["check"]
        fn = REGISTRY.get(name)
        if fn is None:
            results.append(GuardrailResult(name, CheckStatus.WARN, "unknown check"))
            continue
        ctx = {**context, **spec.get("params", {}), "check_name": name}
        results.append(fn(value, ctx))
    return results


def attach(entry, specs: List[CheckSpec], context: Optional[Dict[str, Any]] = None,
           value: Any = None) -> List[GuardrailResult]:
    """Run checks for a ledger entry and store the results on it."""
    value = entry.value if value is None else value
    results = run_checks(specs, value, context)
    entry.guardrail_results = [r.to_dict() for r in results]
    return results


def worst_status(results: List[GuardrailResult]) -> CheckStatus:
    if any(r.status == CheckStatus.FAIL for r in results):
        return CheckStatus.FAIL
    if any(r.status == CheckStatus.WARN for r in results):
        return CheckStatus.WARN
    return CheckStatus.PASS
