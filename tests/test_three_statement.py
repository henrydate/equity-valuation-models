from src.three_statement import ThreeStatementModel, validate_three_statement_integrity


def make_model():
    return ThreeStatementModel(
        company="DemoCo", base_year=2026, years=[2027, 2028, 2029],
        opening={"cash": 100, "receivables": 50, "inventory": 30,
                 "non_current_assets": 500, "payables": 20, "debt": 200,
                 "share_capital": 300, "retained_earnings": 160},
        revenue={2027: 1000, 2028: 1100, 2029: 1200},
        cogs={2027: 600, 2028: 650, 2029: 700},
        opex={2027: 200, 2028: 210, 2029: 220},
        da={2027: 50, 2028: 55, 2029: 60},
        interest={2027: 15, 2028: 14, 2029: 13},
        capex={2027: 70, 2028: 80, 2029: 90},
        debt={2027: 210, 2028: 205, 2029: 195},
        equity_issuance={2028: 50},
        dividends={2027: 30, 2028: 35, 2029: 40},
        receivables_days=45, inventory_days=30, payables_days=35,
    )


def test_opening_balance_sheet_balances():
    _, bs, _ = make_model().build()
    assert abs(bs.loc["Total Assets", 2026] - bs.loc["Total Liabilities & Equity", 2026]) < 1e-6


def test_balance_sheet_foots_every_year():
    _, bs, _ = make_model().build()
    for y in bs.columns:
        assert abs(bs.loc["Total Assets", y] - bs.loc["Total Liabilities & Equity", y]) < 1e-6


def test_retained_earnings_bridges_to_npat_less_dividends():
    pl, bs, _ = make_model().build()
    cols = list(bs.columns)
    for y in [2027, 2028, 2029]:
        prev = cols[cols.index(y) - 1]
        d_re = bs.loc["Retained Earnings", y] - bs.loc["Retained Earnings", prev]
        assert abs(d_re - (pl.loc["NPAT", y] - pl.loc["Dividends", y])) < 1e-6


def test_cash_flow_reconciles_to_balance_sheet_cash():
    _, bs, cf = make_model().build()
    for y in [2027, 2028, 2029]:
        net = cf.loc["Net Change in Cash", y]
        components = (cf.loc["Operating Cash Flow", y]
                      + cf.loc["Investing Cash Flow", y]
                      + cf.loc["Financing Cash Flow", y])
        assert abs(net - components) < 1e-6
        assert abs(cf.loc["Closing Cash", y] - bs.loc["Cash", y]) < 1e-6


def test_validator_passes_on_articulated_model():
    res = make_model().validate()
    assert res["status"] == "PASS"
    assert res["errors"] == []


def test_validator_catches_a_broken_balance():
    pl, bs, cf = make_model().build()
    bs.loc["Total Assets", 2028] += 999  # deliberately break it
    res = validate_three_statement_integrity(pl, bs, cf)
    assert res["status"] == "FAIL"
    assert any("does not balance" in e for e in res["errors"])
