from src.data_scaffold import scaffold_entries
from src.ledger import InputKind, VerificationStatus
from src.financial_statements import SourceOfTruth


FAKE_INFO = {
    "currentPrice": 41.20,
    "sharesOutstanding": 5_068_000_000,
    "marketCap": 208_000_000_000,
    "beta": 0.61,
}


def test_scaffold_builds_unverified_hard_facts():
    ents = scaffold_entries(FAKE_INFO, "BHP.AX", as_of="2026-06-15", price_currency="AUD")
    px = ents["group.share_price"]
    assert px.verification == VerificationStatus.UNVERIFIED
    assert px.kind == InputKind.HARD_FACT
    assert px.source_type == SourceOfTruth.EXTERNAL_DATA
    assert px.provenance_method == "auto_pull"
    assert px.unit == "AUD"


def test_scaffold_scales_shares_and_marketcap_to_millions():
    ents = scaffold_entries(FAKE_INFO, "BHP.AX")
    assert ents["group.shares_outstanding"].value == 5068.0
    assert ents["group.market_cap"].value == 208000.0
    assert ents["wacc.equity_beta_raw"].value == 0.61


def test_scaffold_entries_are_valid_without_rationale():
    # hard facts need a citation but not a rationale (tiered policy)
    for e in scaffold_entries(FAKE_INFO, "BHP.AX").values():
        assert e.validate() == []
        assert e.scaffold_value is not None


def test_scaffold_skips_missing_fields():
    ents = scaffold_entries({"currentPrice": 41.2}, "BHP.AX")
    assert set(ents.keys()) == {"group.share_price"}


def test_scaffold_market_cap_carries_currency():
    # market cap must not be a bare "m" -- it carries the listing currency
    ents = scaffold_entries(FAKE_INFO, "BHP.AX", price_currency="AUD")
    assert ents["group.market_cap"].unit == "AUD m"


def test_scaffold_live_false_marks_illustrative():
    # an offline/demo scaffold must never masquerade as a live pull
    ents = scaffold_entries(FAKE_INFO, "BHP.AX", as_of="2026-06-15", live=False)
    cite = ents["group.share_price"].citation
    assert "ILLUSTRATIVE" in cite
    assert "yfinance" not in cite
