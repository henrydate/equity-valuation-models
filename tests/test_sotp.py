import math

from src.sotp import AssetValuation, Division, SumOfParts


def simple_asset():
    # 2 years, EBITDA = 100*10 - 100*4 = 600/yr, no tax, no capex
    return AssetValuation(
        name="Mine A", commodity="iron ore",
        production={2027: 100, 2028: 100},
        price={2027: 10, 2028: 10},
        unit_cash_cost={2027: 4, 2028: 4},
        tax_rate=0.0,
    )


def test_asset_npv_matches_hand_calc():
    npv = simple_asset().npv(discount_rate=0.10, base_year=2026)
    expected = 600 / 1.10 + 600 / 1.10 ** 2  # 1041.32
    assert math.isclose(npv, expected, rel_tol=1e-9)


def test_tax_and_capex_reduce_fcf():
    taxed = AssetValuation(
        name="Mine B", commodity="copper",
        production={2027: 100}, price={2027: 10}, unit_cash_cost={2027: 4},
        sustaining_capex={2027: 100}, tax_rate=0.30,
    )
    # EBITDA 600; tax = 30% * (600-100) = 150; FCF = 600-150-100 = 350
    assert math.isclose(taxed.fcf_schedule()[2027], 350.0, rel_tol=1e-9)


def test_stake_scales_npv():
    full = simple_asset()
    half = simple_asset()
    half.stake = 0.5
    assert math.isclose(half.npv(0.10, 2026), 0.5 * full.npv(0.10, 2026), rel_tol=1e-9)


def test_sotp_bridge_to_per_share():
    div = Division(name="Iron Ore", assets=[simple_asset()])
    sotp = SumOfParts(
        company="DemoMiner", base_year=2026, discount_rate=0.10,
        divisions=[div], net_debt=200, shares_outstanding=100,
    )
    ev = sotp.enterprise_value()
    assert math.isclose(ev, 600 / 1.10 + 600 / 1.10 ** 2, rel_tol=1e-9)
    assert math.isclose(sotp.equity_value(), ev - 200, rel_tol=1e-9)
    assert math.isclose(sotp.value_per_share(), (ev - 200) / 100, rel_tol=1e-9)


def test_summary_table_shape():
    sotp = SumOfParts(
        company="DemoMiner", base_year=2026, discount_rate=0.10,
        divisions=[Division("Iron Ore", [simple_asset()]),
                   Division("Copper", [simple_asset()])],
        corporate_pv=50, net_debt=200, shares_outstanding=100,
    )
    tbl = sotp.summary_table()
    assert "Enterprise value" in tbl.index
    assert "Value per share" in tbl.index
    # divisions + corporate + EV + net debt + equity + shares + per share
    assert tbl.loc["Value per share", "Value"] == sotp.value_per_share()
