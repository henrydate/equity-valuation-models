from src.ledger import Ledger, LedgerEntry, InputKind, VerificationStatus
from src.financial_statements import SourceOfTruth
from src.sotp import AssetValuation, Division, SumOfParts
from src.note import render_note, write_note


def build_ledger():
    led = Ledger("BHP Group Limited", "BHP.AX")
    led.add(LedgerEntry(
        key="wacc.equity_beta", label="Equity beta", value=0.95, unit="x",
        kind=InputKind.DISCRETIONARY, source_type=SourceOfTruth.ANALYST_ESTIMATE,
        citation="peers re-levered", as_of="2026-06-15",
        verification=VerificationStatus.VERIFIED,
        rationale="bottom-up over raw regression", method="bottom_up", method_default=True))
    led.add(LedgerEntry(
        key="group.share_price", label="Share price", value=41.2, unit="AUD",
        kind=InputKind.HARD_FACT, source_type=SourceOfTruth.EXTERNAL_DATA, citation="yfinance",
        as_of="2026-06-15", verification=VerificationStatus.UNVERIFIED, provenance_method="auto_pull"))
    led.set_result("wacc", 0.089, unit="%")
    led.set_result("cost_of_equity", 0.0876, unit="%")
    return led


def make_sotp():
    a = AssetValuation(name="Mine", commodity="iron ore",
                       production={2027: 100, 2028: 100}, price={2027: 10, 2028: 10},
                       unit_cash_cost={2027: 4, 2028: 4}, tax_rate=0.0)
    return SumOfParts(company="BHP", base_year=2026, discount_rate=0.089,
                      divisions=[Division("Iron Ore", [a])], net_debt=200, shares_outstanding=100)


def test_note_contains_core_sections():
    note = render_note(build_ledger(), make_sotp(), recommendation="HOLD", thesis="Test thesis.")
    for section in ["Equity Research Note", "Recommendation", "Investment thesis",
                    "Valuation — sum of the parts", "Key assumptions & provenance",
                    "Model integrity", "ILLUSTRATIVE"]:
        assert section in note
    assert "HOLD" in note
    assert "Test thesis." in note
    assert "bottom-up over raw regression" in note   # rationale is rendered
    assert "Analyst Estimate" in note                # source label rendered
    assert "8.90%" in note                           # wacc rendered as a percentage


def test_note_renders_sotp_per_share():
    assert "Value per share" in render_note(build_ledger(), make_sotp())


def test_write_note(tmp_path):
    p = tmp_path / "note.md"
    text = write_note(p, build_ledger(), make_sotp(), recommendation="HOLD")
    assert p.read_text(encoding="utf-8").startswith("# BHP Group Limited")
    assert "HOLD" in text


def test_note_surfaces_as_of_dates_and_market_data():
    note = render_note(build_ledger(), make_sotp(), recommendation="HOLD")
    assert "As of" in note                 # every assumption is dated in the table
    assert "2026-06-15" in note            # the as-of date is actually rendered
    assert "Market data (as-of)" in note   # scaffolded hard facts get their own dated table
    assert "yfinance" in note              # the citation string is shown, for verification
