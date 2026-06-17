from src.question_banks import get_bank, MINING_BANK
from src.wizard import build_entry
from src.guardrails import CheckStatus, worst_status


def _iron_ore_spec():
    return next(s for s in MINING_BANK if s["key"] == "ironore.price_deck")


def test_mining_bank_registered():
    keys = [s["key"] for s in get_bank("mining")]
    assert "ironore.price_deck" in keys
    assert "potash.price_deck" in keys


def test_deck_value_is_a_per_year_map():
    spec = _iron_ore_spec()
    answers = {"value": {2027: 95, 2028: 90, "long_run": 78},
               "citation": "consensus + cost support", "rationale": "taper to support"}
    entry, _ = build_entry(spec, answers, context={"spot": 105})
    assert entry.value["long_run"] == 78
    assert entry.validate() == []


def test_deck_long_run_far_below_spot_warns():
    answers = {"value": {2027: 95, "long_run": 60}, "citation": "x", "rationale": "aggressive"}
    _, results = build_entry(_iron_ore_spec(), answers, context={"spot": 105})
    assert worst_status(results) == CheckStatus.WARN  # 60 is ~43% below 105 (> 30% threshold)


def test_deck_modest_taper_passes():
    answers = {"value": {2027: 100, "long_run": 95}, "citation": "x", "rationale": "modest"}
    _, results = build_entry(_iron_ore_spec(), answers, context={"spot": 105})
    assert worst_status(results) == CheckStatus.PASS  # 95 vs 105 = ~9% (< 30%)
