from carbonplan_tonyear import calculate_tonyears, get_baseline_curve


def test_calculate_tonyears():
    time_horizon = 100
    delay = 46
    discount_rate = 0
    ipcc_2000 = get_baseline_curve('ipcc_2000')
    m = calculate_tonyears('mc', ipcc_2000, time_horizon, delay, discount_rate)
    assert isinstance(m, dict)
