import pytest

from src.template_loader import build_from_template, collect_missing


def filled_template():
    return {
        "company": "TestCo", "ticker": "TST.AX",
        "reporting_currency": "USD", "presentation_currency": "AUD",
        "valuation_base_year": 2026, "forecast_years": [2027, 2028],
        "wacc": {
            "risk_free": {"value": 0.042, "citation": "US 10Y, FRED 2026-06-15"},
            "erp": {"value": 0.048, "method": "implied", "citation": "Damodaran Jun-2026"},
            "equity_beta": {"value": 0.95, "method": "bottom_up", "rationale": "peers re-levered", "citation": "RIO/VALE peers"},
            "cost_of_debt": {"value": 0.053, "method": "rating_implied", "citation": "A-rated, rf+1.1%"},
            "tax_rate": {"value": 0.30, "citation": "AUS statutory"},
            "mv_equity": {"value": 208000, "citation": "price x shares"},
            "mv_debt": {"value": 10000, "citation": "FY25 net debt"},
            "currency_basis": {"citation": "USD functional currency"},
        },
        "commodity_decks": {
            "iron ore": {"unit": "USD/t", "spot": 105, "citation": "consensus + cost support",
                         "deck": {"2027": 95, "2028": 90, "long_run": 75}},
        },
        "divisions": [
            {"name": "Iron Ore", "overhead_pv": 0, "assets": [
                {"name": "WAIO", "commodity": "iron ore", "production": 280, "unit_cash_cost": 20,
                 "sustaining_capex": 1500, "royalty_rate": 0.075, "stake": 1.0,
                 "citation": "FY operational review"}]},
        ],
        "group": {"other_assets": 0, "corporate_pv": 8000, "net_debt": 11000,
                  "minorities": 3000, "shares_outstanding": 5068, "citation": "FY25 balance sheet"},
    }


def test_filled_template_has_no_missing():
    assert collect_missing(filled_template()) == []


def test_build_from_template_produces_a_valuation():
    led, sotp = build_from_template(filled_template())
    assert led.get("wacc.equity_beta").value == 0.95
    assert led.get("ironore.price_deck").value["long_run"] == 75
    assert led.results.get("wacc", {}).get("value") is not None
    ps = sotp.value_per_share()
    assert isinstance(ps, float)
    assert led.results["value_per_share"]["value"] == round(ps, 2)


def test_missing_values_and_fill_citations_are_reported():
    data = filled_template()
    data["group"]["net_debt"] = None
    data["wacc"]["risk_free"]["citation"] = "FILL - todo"
    missing = collect_missing(data)
    assert "group.net_debt" in missing
    assert any("risk_free citation" in m for m in missing)


def test_build_raises_when_incomplete():
    data = filled_template()
    data["commodity_decks"]["iron ore"]["spot"] = None
    with pytest.raises(ValueError):
        build_from_template(data)


def test_blank_template_file_reports_many_missing():
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "templates", "bhp_template.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    missing = collect_missing(data)
    assert len(missing) > 20  # the shipped template is intentionally unfilled


def test_deck_must_cover_every_forecast_year():
    data = filled_template()
    data["forecast_years"] = [2027, 2028, 2029]  # deck only carries 2027, 2028, long_run
    assert "decks[iron ore].2029" in collect_missing(data)
