import numpy as np
import pytest

from tonyear import calculate_tonyears, get_baseline_curve, print_benefit_report


@pytest.mark.parametrize('curve_name', ['joos_2013', 'ipcc_2007', 'ipcc_2000'])
@pytest.mark.parametrize('t_horizon', [1, 100, 1001])
def test_get_baseline_curve(curve_name, t_horizon):
    curve = get_baseline_curve(curve_name, t_horizon=t_horizon)
    assert len(curve) == t_horizon
    assert np.issubdtype(curve.dtype, np.floating)


def test_get_baseline_curve_raises_invalid_args():
    with pytest.raises(ValueError, match='t_horizon must be a postive integer'):
        _ = get_baseline_curve('joos_2013', t_horizon=-1)

    with pytest.raises(ValueError, match='No baseline curve parameters by the name foo.'):
        _ = get_baseline_curve('foo')


@pytest.mark.parametrize('curve_name', ['joos_2013', 'ipcc_2007', 'ipcc_2000'])
@pytest.mark.parametrize('method', ['mc', 'lashof', 'ipcc'])
@pytest.mark.parametrize('time_horizon', [1, 100, 1001])
@pytest.mark.parametrize('delay', [0, 1, 46])
@pytest.mark.parametrize('discount_rate', [0, 0.1])
def test_calculate_tonyears(curve_name, method, time_horizon, delay, discount_rate):
    if delay > time_horizon:
        pytest.skip('Invalid option set')
    curve = get_baseline_curve(curve_name)
    m = calculate_tonyears(method, curve, time_horizon, delay, discount_rate)
    assert isinstance(m, dict)
    for k, t in [
        ('parameters', dict),
        ('baseline', np.ndarray),
        ('scenario', np.ndarray),
        ('baseline_atm_cost', float),
        ('benefit', float),
        ('num_for_equivalence', float),
    ]:
        assert isinstance(m[k], t)


def test_calculate_tonyears_raises_invalid_args():
    with pytest.raises(ValueError, match='No ton-year accounting method called foo'):
        _ = calculate_tonyears('foo', np.arange(20), 10, 5, 0.1)

    with pytest.raises(ValueError, match='Delay cannot be negative.'):
        _ = calculate_tonyears('foo', np.arange(20), 10, -1, 0.1)

    with pytest.raises(ValueError, match='Time horizon must be greater than zero.'):
        _ = calculate_tonyears('foo', np.arange(20), -1, 5, 0.1)

    with pytest.raises(
        ValueError, match='Time horizon cannot be longer than length of the baseline array.'
    ):
        _ = calculate_tonyears('foo', np.arange(20), 30, 5, 0.1)


def test_print_benefit_report():
    method_dict = {
        'parameters': {'method': 'mc', 'time_horizon': 100, 'delay': 46, 'discount_rate': 0},
        'baseline': np.array([0.999999, 0.9203021, 0.85782477, 0.80831021]),
        'scenario': np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]),
        'baseline_atm_cost': 45.76289499601616,
        'benefit': 46.0,
        'num_for_equivalence': 0.9948455433916557,
    }
    ret_val = print_benefit_report(method_dict)
    assert ret_val is None
