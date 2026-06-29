import math

import pytest

from src.comps import ComparablesValuation, NormalizedDCF, Segment


def make_comps():
    return ComparablesValuation(
        segments=[Segment("Iron Ore", 14396, 5.5), Segment("Copper", 12701, 8.0),
                  Segment("Coal", 721, 4.0)],
        other_assets=8524, corporate_drag_ebitda=-444, corporate_multiple=6.0,
        net_debt=12924, nci=4553, shares_m=5081, usd_per_aud=0.69,
    )


def test_comps_enterprise_value_sums_segments_plus_other_less_corporate():
    c = make_comps()
    expected = 14396 * 5.5 + 12701 * 8.0 + 721 * 4.0 + 8524 + (-444 * 6.0)
    assert c.enterprise_value() == pytest.approx(expected)


def test_comps_equity_bridge_and_per_share():
    c = make_comps()
    equity = c.enterprise_value() - 12924 - 4553
    assert c.equity_value_usd() == pytest.approx(equity)
    # AUD per share = USD per share / FX
    assert c.value_per_share() == pytest.approx(equity / 5081 / 0.69)


def test_comps_summary_table_is_in_aud_and_balances():
    c = make_comps()
    tbl = c.summary_table()
    # EV row, converted to AUD, equals USD EV / FX
    ev_aud = tbl.loc["Enterprise value", "Value"]
    assert ev_aud == pytest.approx(c.enterprise_value() / 0.69)
    # last row is the AUD per-share value
    assert tbl.loc["Value per share", "Value"] == pytest.approx(c.value_per_share())


def test_normalized_dcf_fcf_and_value():
    d = NormalizedDCF(ebitda=25978, da=5540, tax_rate=0.30, sustaining_capex=7000,
                      wacc=0.079, growth=0.02, net_debt=12924, nci=4553,
                      shares_m=5081, usd_per_aud=0.69)
    ebit = 25978 - 5540
    fcf = ebit * 0.70 + 5540 - 7000
    assert d.fcf() == pytest.approx(fcf)
    ev = fcf * 1.02 / (0.079 - 0.02)
    assert d.enterprise_value() == pytest.approx(ev)
    assert d.value_per_share() == pytest.approx((ev - 12924 - 4553) / 5081 / 0.69)


def test_normalized_dcf_requires_wacc_above_growth():
    d = NormalizedDCF(ebitda=100, da=10, tax_rate=0.3, sustaining_capex=5,
                      wacc=0.02, growth=0.02, net_debt=0, nci=0, shares_m=1)
    with pytest.raises(ValueError):
        d.enterprise_value()


def test_normalized_dcf_sensitivity_grid_shape():
    d = NormalizedDCF(ebitda=25978, da=5540, tax_rate=0.30, sustaining_capex=7000,
                      wacc=0.079, growth=0.02, net_debt=12924, nci=4553,
                      shares_m=5081, usd_per_aud=0.69)
    grid = d.sensitivity([-0.005, 0.0, 0.005], [0.015, 0.02, 0.025])
    assert grid.shape == (3, 3)
    # lower WACC -> higher value (down the rows WACC rises, so value falls)
    mid = grid["g=2.0%"]
    assert mid.iloc[0] > mid.iloc[-1]
