from src.guardrails import run_checks, CheckStatus, worst_status


def only(results, name):
    return next(r for r in results if r.check == name)


def test_within_range_pass_and_warn():
    spec = [{"check": "within_range", "params": {"range": [0.7, 1.3]}}]
    assert run_checks(spec, 0.95)[0].status == CheckStatus.PASS
    assert run_checks(spec, 1.8)[0].status == CheckStatus.WARN


def test_wacc_gt_g():
    assert run_checks(["wacc_gt_g"], context={"wacc": 0.089, "g": 0.025})[0].status == CheckStatus.PASS
    assert run_checks(["wacc_gt_g"], context={"wacc": 0.020, "g": 0.025})[0].status == CheckStatus.FAIL


def test_weights_sum_to_1():
    assert run_checks(["weights_sum_to_1"], context={"weight_equity": 0.85, "weight_debt": 0.15})[0].status == CheckStatus.PASS
    assert run_checks(["weights_sum_to_1"], context={"weight_equity": 0.85, "weight_debt": 0.30})[0].status == CheckStatus.FAIL


def test_cost_of_debt_gt_rf():
    assert run_checks(["cost_of_debt_gt_rf"], context={"cost_of_debt": 0.053, "rf": 0.042})[0].status == CheckStatus.PASS
    assert run_checks(["cost_of_debt_gt_rf"], context={"cost_of_debt": 0.030, "rf": 0.042})[0].status == CheckStatus.WARN


def test_long_run_vs_spot():
    spec = [{"check": "long_run_vs_spot", "params": {"threshold": 0.25}}]
    assert run_checks(spec, {"2027": 95, "long_run": 75}, {"spot": 105})[0].status == CheckStatus.WARN
    assert run_checks(spec, {"long_run": 100}, {"spot": 105})[0].status == CheckStatus.PASS


def test_vs_scaffold_within():
    spec = [{"check": "vs_scaffold_within", "params": {"tol_pct": 0.02}}]
    assert run_checks(spec, 5070, {"scaffold_value": 5068})[0].status == CheckStatus.PASS
    assert run_checks(spec, 5300, {"scaffold_value": 5068})[0].status == CheckStatus.WARN


def test_relever_gearing_matches_weights():
    assert run_checks(["relever_gearing_matches_weights"], context={"relever_gearing": 0.15, "weights_gearing": 0.15})[0].status == CheckStatus.PASS
    assert run_checks(["relever_gearing_matches_weights"], context={"relever_gearing": 0.15, "weights_gearing": 0.30})[0].status == CheckStatus.WARN


def test_unknown_check_warns():
    assert run_checks(["does_not_exist"])[0].status == CheckStatus.WARN


def test_worst_status():
    r = run_checks([{"check": "within_range", "params": {"range": [0, 1]}}], 0.5)
    assert worst_status(r) == CheckStatus.PASS
