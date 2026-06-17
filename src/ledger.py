"""
Assumption-and-Evidence Ledger
===============================

The spine of the framework. Every number a valuation touches -- an auto-pulled
fact, an analyst-verified fact, or an elicited discretionary judgement -- is
recorded here as a :class:`LedgerEntry` carrying its value, provenance
(source type + citation + as-of date), a verification status, an optional
rationale, the method used, and the results of any guardrail checks.

"Verify a fact" and "elicit a judgement" are two modes of writing the same
ledger. The valuation engine computes derived values (WACC, EV, per-share) and
snapshots them under ``results`` -- those are *outputs*, not provenance-bearing
inputs. Full history is the git diff; only analytically meaningful overrides
are kept inline.

See ``docs/SCHEMA.md`` for the field reference.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .financial_statements import SourceOfTruth


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class InputKind(Enum):
    """The two modes of the ledger."""
    HARD_FACT = "hard_fact"          # a reported/observed number; needs a citation
    DISCRETIONARY = "discretionary"  # an analyst judgement; needs a rationale


class VerificationStatus(Enum):
    """Has a human checked this value against a primary source?"""
    UNVERIFIED = "unverified"  # machine-pulled scaffold, not yet checked
    VERIFIED = "verified"      # checked or overridden against a primary source


@dataclass
class LedgerEntry:
    """One auditable input. ``value`` may be a scalar or a per-year mapping."""

    key: str                      # stable id, e.g. "wacc.equity_beta"
    label: str
    value: Any                    # scalar OR {"2027": 95, ..., "long_run": 75}
    unit: str
    kind: InputKind
    source_type: SourceOfTruth
    citation: str
    as_of: str                    # ISO date the value is valid as of

    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    rationale: Optional[str] = None
    method: Optional[str] = None          # which method path was used
    method_default: Optional[bool] = None  # did the analyst stay on the house default?
    provenance_method: str = "manual"     # auto_pull | manual_override | wizard | manual
    entered_by: str = "henry"
    entered_at: str = field(default_factory=_now)
    guardrail_results: List[dict] = field(default_factory=list)
    overrides: List[dict] = field(default_factory=list)
    scaffold_value: Any = None            # the auto-pulled value, kept when overridden

    # -- validation (the tiered required-field policy) --------------------
    def validate(self) -> List[str]:
        """Return a list of problems; empty means the entry is well-formed."""
        problems: List[str] = []
        if not self.key:
            problems.append("missing key")
        if not self.label:
            problems.append(f"{self.key or '?'}: missing label")
        if self.value is None:
            problems.append(f"{self.key}: value is required")
        if not self.unit:
            problems.append(f"{self.key}: unit is required")
        if not self.citation:
            problems.append(f"{self.key}: citation is required")
        if not self.as_of:
            problems.append(f"{self.key}: as_of date is required")
        if self.kind == InputKind.DISCRETIONARY and not (self.rationale and self.rationale.strip()):
            problems.append(f"{self.key}: discretionary inputs require a rationale")
        for ov in self.overrides:
            if not ov.get("reason"):
                problems.append(f"{self.key}: an override is missing its reason")
        return problems

    def require_valid(self) -> None:
        problems = self.validate()
        if problems:
            raise ValueError("Invalid ledger entry -- " + "; ".join(problems))

    def add_override(self, reason: str, by: str = "henry") -> None:
        """Log proceeding past a guardrail warning (deviation + justification)."""
        if not reason or not reason.strip():
            raise ValueError("an override requires a reason")
        self.overrides.append({"reason": reason.strip(), "by": by, "at": _now()})

    @property
    def has_open_warning(self) -> bool:
        flagged = any(g.get("status") in ("warn", "fail") for g in self.guardrail_results)
        return flagged and not self.overrides

    # -- serialisation -----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "kind": self.kind.value,
            "source_type": self.source_type.name,
            "citation": self.citation,
            "as_of": self.as_of,
            "verification": self.verification.value,
            "rationale": self.rationale,
            "method": self.method,
            "method_default": self.method_default,
            "provenance_method": self.provenance_method,
            "entered_by": self.entered_by,
            "entered_at": self.entered_at,
            "guardrail_results": self.guardrail_results,
            "overrides": self.overrides,
            "scaffold_value": self.scaffold_value,
        }

    @classmethod
    def from_dict(cls, key: str, d: dict) -> "LedgerEntry":
        return cls(
            key=key,
            label=d["label"],
            value=d["value"],
            unit=d["unit"],
            kind=InputKind(d["kind"]),
            source_type=SourceOfTruth[d["source_type"]],
            citation=d["citation"],
            as_of=d["as_of"],
            verification=VerificationStatus(d.get("verification", "unverified")),
            rationale=d.get("rationale"),
            method=d.get("method"),
            method_default=d.get("method_default"),
            provenance_method=d.get("provenance_method", "manual"),
            entered_by=d.get("entered_by", "henry"),
            entered_at=d.get("entered_at", _now()),
            guardrail_results=d.get("guardrail_results", []),
            overrides=d.get("overrides", []),
            scaffold_value=d.get("scaffold_value"),
        )


@dataclass
class Ledger:
    """A company's full assumption-and-evidence ledger."""

    company: str
    ticker: str
    reporting_currency: str = "USD"
    presentation_currency: str = "AUD"
    model_created: str = field(default_factory=lambda: date.today().isoformat())
    model_last_updated: str = field(default_factory=lambda: date.today().isoformat())
    entries: Dict[str, LedgerEntry] = field(default_factory=dict)
    results: Dict[str, dict] = field(default_factory=dict)

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        """Validate (tiered policy) and store an entry, keyed by ``entry.key``."""
        entry.require_valid()
        self.entries[entry.key] = entry
        self.model_last_updated = date.today().isoformat()
        return entry

    def get(self, key: str) -> Optional[LedgerEntry]:
        return self.entries.get(key)

    def value_of(self, key: str, default: Any = None) -> Any:
        e = self.entries.get(key)
        return default if e is None else e.value

    def set_result(self, key: str, value: Any, unit: Optional[str] = None,
                   inputs: Optional[List[str]] = None) -> None:
        """Snapshot a computed output (not provenance-bearing)."""
        res: dict = {"value": value, "computed": True}
        if unit:
            res["unit"] = unit
        if inputs:
            res["inputs"] = inputs
        self.results[key] = res
        self.model_last_updated = date.today().isoformat()

    def open_warnings(self) -> List[str]:
        return [k for k, e in self.entries.items() if e.has_open_warning]

    def audit_summary(self) -> dict:
        total = len(self.entries)
        verified = sum(1 for e in self.entries.values()
                       if e.verification == VerificationStatus.VERIFIED)
        overrides_logged = sum(len(e.overrides) for e in self.entries.values())
        warnings_open = sum(1 for e in self.entries.values() if e.has_open_warning)
        return {
            "entries_total": total,
            "verified": verified,
            "unverified": total - verified,
            "warnings_open": warnings_open,
            "overrides_logged": overrides_logged,
        }

    # -- serialisation -----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "ticker": self.ticker,
            "reporting_currency": self.reporting_currency,
            "presentation_currency": self.presentation_currency,
            "model_created": self.model_created,
            "model_last_updated": self.model_last_updated,
            "entries": {k: e.to_dict() for k, e in self.entries.items()},
            "results": self.results,
            "audit": self.audit_summary(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Ledger":
        led = cls(
            company=d["company"],
            ticker=d["ticker"],
            reporting_currency=d.get("reporting_currency", "USD"),
            presentation_currency=d.get("presentation_currency", "AUD"),
            model_created=d.get("model_created", date.today().isoformat()),
            model_last_updated=d.get("model_last_updated", date.today().isoformat()),
        )
        for k, ed in d.get("entries", {}).items():
            led.entries[k] = LedgerEntry.from_dict(k, ed)
        led.results = d.get("results", {})
        return led

    def save(self, path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path) -> "Ledger":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
