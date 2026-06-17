from src.ledger import Ledger, LedgerEntry, InputKind, VerificationStatus
from src.financial_statements import SourceOfTruth

import pytest


def make_beta(rationale="bottom-up over raw regression"):
    return LedgerEntry(
        key="wacc.equity_beta", label="Equity beta", value=0.95, unit="x",
        kind=InputKind.DISCRETIONARY, source_type=SourceOfTruth.ANALYST_ESTIMATE,
        citation="peers RIO/VALE/Anglo re-levered to 15% target gearing",
        as_of="2026-06-15", verification=VerificationStatus.VERIFIED,
        rationale=rationale, method="bottom_up", method_default=True,
    )


def make_share_price():
    return LedgerEntry(
        key="group.share_price", label="Share price", value=41.20, unit="AUD",
        kind=InputKind.HARD_FACT, source_type=SourceOfTruth.EXTERNAL_DATA,
        citation="yfinance BHP.AX", as_of="2026-06-15",
        verification=VerificationStatus.UNVERIFIED, provenance_method="auto_pull",
        entered_by="system",
    )


def test_discretionary_requires_rationale():
    e = make_beta(rationale=None)
    with pytest.raises(ValueError):
        Ledger("BHP", "BHP.AX").add(e)


def test_hard_fact_needs_no_rationale():
    e = LedgerEntry(
        key="group.shares", label="Shares outstanding", value=5070, unit="m shares",
        kind=InputKind.HARD_FACT, source_type=SourceOfTruth.COMPANY_FILING,
        citation="BHP FY25 Annual Report p.184", as_of="2025-06-30",
        verification=VerificationStatus.VERIFIED,
    )
    led = Ledger("BHP", "BHP.AX")
    led.add(e)
    assert led.value_of("group.shares") == 5070


def test_missing_citation_rejected():
    e = make_beta()
    e.citation = ""
    with pytest.raises(ValueError):
        Ledger("BHP", "BHP.AX").add(e)


def test_per_year_value_roundtrips(tmp_path):
    led = Ledger("BHP", "BHP.AX")
    deck = LedgerEntry(
        key="ironore.price_deck", label="Iron ore 62% Fe",
        value={"2027": 95, "2028": 90, "long_run": 75}, unit="USD/t",
        kind=InputKind.DISCRETIONARY, source_type=SourceOfTruth.ANALYST_ESTIMATE,
        citation="consensus front years; cost support long-run", as_of="2026-06-15",
        verification=VerificationStatus.VERIFIED, rationale="taper to cost support",
    )
    led.add(deck)
    path = tmp_path / "BHP.json"
    led.save(path)

    back = Ledger.load(path)
    e = back.get("ironore.price_deck")
    assert e.value["long_run"] == 75
    assert e.kind == InputKind.DISCRETIONARY
    assert e.source_type == SourceOfTruth.ANALYST_ESTIMATE
    assert e.verification == VerificationStatus.VERIFIED


def test_audit_summary_counts_verification():
    led = Ledger("BHP", "BHP.AX")
    led.add(make_beta())
    led.add(make_share_price())
    a = led.audit_summary()
    assert a["entries_total"] == 2
    assert a["verified"] == 1
    assert a["unverified"] == 1


def test_open_warning_closed_by_override():
    led = Ledger("BHP", "BHP.AX")
    e = make_beta()
    e.guardrail_results = [{"check": "within_range", "status": "warn", "message": "x"}]
    led.add(e)
    assert led.audit_summary()["warnings_open"] == 1
    assert led.open_warnings() == ["wacc.equity_beta"]

    e.add_override("single-asset leverage justifies higher beta")
    assert led.audit_summary()["warnings_open"] == 0
    assert led.audit_summary()["overrides_logged"] == 1


def test_results_snapshot():
    led = Ledger("BHP", "BHP.AX")
    led.set_result("wacc", 0.089, unit="%", inputs=["wacc.risk_free", "wacc.equity_beta"])
    assert led.to_dict()["results"]["wacc"]["value"] == 0.089
    assert led.to_dict()["results"]["wacc"]["computed"] is True
