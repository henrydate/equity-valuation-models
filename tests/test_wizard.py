from src.wizard import build_entry, compute_wacc
from src.question_banks import BETA, WACC_BANK, get_bank
from src.ledger import Ledger, LedgerEntry, InputKind, VerificationStatus
from src.financial_statements import SourceOfTruth
from src.guardrails import CheckStatus, worst_status


def test_build_beta_default_method_passes():
    answers = {
        "value": 0.95,
        "citation": "peers RIO/VALE/Anglo re-levered to 15%",
        "rationale": "bottom-up over raw regression; 5y BHP beta distorted by 2022 spike",
        "as_of": "2026-06-15",
    }
    ctx = {"relever_gearing": 0.15, "weights_gearing": 0.15}
    entry, results = build_entry(BETA, answers, context=ctx)
    assert entry.method == "bottom_up"          # house default applied
    assert entry.method_default is True
    assert entry.provenance_method == "wizard"
    assert worst_status(results) == CheckStatus.PASS
    assert entry.validate() == []


def test_build_beta_out_of_range_warns_then_override_closes_it():
    answers = {
        "value": 1.8,
        "method": "regression",
        "citation": "5y monthly regression, unadjusted",
        "rationale": "single-asset operating leverage",
        "as_of": "2026-06-15",
        "override_reason": "high operating leverage genuinely justifies an above-peer beta",
    }
    entry, results = build_entry(BETA, answers)
    assert entry.method == "regression"
    assert entry.method_default is False         # switched off the house default
    assert worst_status(results) == CheckStatus.WARN
    assert len(entry.overrides) == 1
    assert entry.has_open_warning is False       # the logged override closes the warning


def _disc(key, value, rationale="r"):
    return LedgerEntry(
        key=key, label=key, value=value, unit="%", kind=InputKind.DISCRETIONARY,
        source_type=SourceOfTruth.ANALYST_ESTIMATE, citation="c", as_of="2026-06-15",
        verification=VerificationStatus.VERIFIED, rationale=rationale,
    )


def _fact(key, value):
    return LedgerEntry(
        key=key, label=key, value=value, unit="m", kind=InputKind.HARD_FACT,
        source_type=SourceOfTruth.COMPANY_FILING, citation="FY25", as_of="2026-06-15",
        verification=VerificationStatus.VERIFIED,
    )


def test_compute_wacc_end_to_end():
    led = Ledger("BHP", "BHP.AX")
    led.add(_disc("wacc.risk_free", 0.042))
    led.add(_disc("wacc.erp", 0.055))
    led.add(_disc("wacc.equity_beta", 0.95))
    led.add(_disc("wacc.cost_of_debt", 0.053))
    led.add(_disc("wacc.tax_rate", 0.30))
    led.add(_fact("wacc.mv_equity", 208000))
    led.add(_fact("wacc.mv_debt", 10000))

    wacc = compute_wacc(led)
    # CoE = 4.2% + 0.95*5.5% = 9.425%; CoD post-tax = 5.3%*0.7 = 3.71%; WACC ~ 9.16%
    assert 0.085 <= wacc <= 0.095
    assert led.results["wacc"]["value"] == round(wacc, 4)
    # all three cross-checks should pass at these inputs
    statuses = {c["status"] for c in led.results["wacc"]["cross_checks"]}
    assert statuses == {"pass"}


def test_compute_wacc_flags_missing_inputs():
    led = Ledger("BHP", "BHP.AX")
    led.add(_disc("wacc.risk_free", 0.042))
    try:
        compute_wacc(led)
        assert False, "expected ValueError for missing inputs"
    except ValueError as exc:
        assert "missing inputs" in str(exc)


def test_wacc_bank_shape():
    bank = get_bank("wacc")
    assert [s["key"] for s in bank][:3] == ["wacc.currency_basis", "wacc.risk_free", "wacc.erp"]
    # the multi-method inputs carry a method registry + a house default
    for key in ("wacc.erp", "wacc.equity_beta", "wacc.cost_of_debt"):
        spec = next(s for s in bank if s["key"] == key)
        assert spec["methods"] and spec["default_method"] in spec["methods"]
