import numpy as np
import pytest

from tonyear import (
    calculate_tonyears,
    get_baseline_curve,
    joos_2013,
    joos_2013_monte_carlo,
    print_benefit_report,
)


@pytest.mark.parametrize('curve_name', ['joos_2013', 'ipcc_2007', 'ipcc_2000'])
@pytest.mark.parametrize('t_horizon', [1, 100, 1001])
def test_get_baseline_curve(curve_name, t_horizon) -> None:
    curve = get_baseline_curve(curve_name, t_horizon=t_horizon)
    assert len(curve) == t_horizon
    assert np.issubdtype(curve.dtype, np.floating)


def test_get_baseline_curve_raises_invalid_args() -> None:
    with pytest.raises(ValueError, match='t_horizon must be a postive integer'):
        _ = get_baseline_curve('joos_2013', t_horizon=-1)

    with pytest.raises(ValueError, match='No baseline curve parameters by the name foo.'):
        _ = get_baseline_curve('foo')


def test_baseline_curve_values() -> None:
    """
    Test values taken from Joos 2013, Table 4, Best estimates for time-integrated IRF
    https://doi.org/10.5194/acp-13-2793-2013
    """
    curve = get_baseline_curve('joos_2013')
    assert round(np.trapz(curve[:21]), 1) == 14.2
    assert round(np.trapz(curve[:51]), 1) == 30.3
    assert round(np.trapz(curve[:101]), 1) == 52.4
    assert round(np.trapz(curve[:501])) == 184
    assert round(np.trapz(curve[:1001])) == 310


@pytest.mark.parametrize('curve_name', ['joos_2013', 'ipcc_2007', 'ipcc_2000'])
@pytest.mark.parametrize('method', ['mc', 'lashof'])
@pytest.mark.parametrize('time_horizon', [1, 100, 1001])
@pytest.mark.parametrize('delay', [0, 1, 46])
@pytest.mark.parametrize('discount_rate', [0, 0.1])
def test_calculate_tonyears(curve_name, method, time_horizon, delay, discount_rate) -> None:
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


def test_ipcc_tonyear_values() -> None:
    """
    Test values taken from IPCC 2000
    https://archive.ipcc.ch/ipccreports/sres/land_use/index.php?idp=74
    """
    curve = get_baseline_curve('ipcc_2000')
    mc = calculate_tonyears('mc', curve, 100, 46, 0)
    assert round(mc['baseline_atm_cost']) == 46
    assert round(mc['benefit']) == 46

    lashof = calculate_tonyears('lashof', curve, 100, 46, 0)
    assert round(lashof['baseline_atm_cost']) == 46
    assert round(lashof['benefit']) == 17


def test_ncx_tonyear_values() -> None:
    """
    Test taken from NCX methodology 2020, Forests and Carbon: A Guide for Buyers and Policymakers
    """
    curve = get_baseline_curve('ipcc_2007')
    m = calculate_tonyears('mc', curve, 100, 1, 0)
    m_discounted = calculate_tonyears('mc', curve, 100, 1, 0.033)
    assert round(m['baseline_atm_cost']) == 48
    assert round(m_discounted['baseline_atm_cost']) == 17
    assert round(m_discounted['baseline_atm_cost'] / m['benefit']) == 17


def test_calculate_tonyears_raises_invalid_args() -> None:
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


def test_print_benefit_report() -> None:
    method_dict = {
        'parameters': {'method': 'mc', 'time_horizon': 100, 'delay': 46, 'discount_rate': 0},
        'baseline': np.array([0.999999, 0.9203021, 0.85782477, 0.80831021]),
        'scenario': np.array([-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]),
        'baseline_atm_cost': 45.76289499601616,
        'benefit': 46.0,
        'num_for_equivalence': 0.9948455433916557,
    }
    print_benefit_report(method_dict)


@pytest.mark.parametrize('t_horizon', [1, 100, 1001])
def test_joos_2013(t_horizon) -> None:
    """
    Test the the values returned from the Joos 2013 IRF curve creation in the ghgfocing
    module match the values returned by get_baseline_curve.
    """
    curve = joos_2013(t_horizon)
    assert len(curve) == t_horizon
    assert np.issubdtype(curve.dtype, np.floating)
    assert curve.all() == get_baseline_curve('joos_2013', t_horizon=t_horizon).all()


def test_joos_2013_monte_carlo_raises_invalid_args() -> None:
    with pytest.raises(ValueError, match='number of runs must be >1'):
        _ = joos_2013_monte_carlo(1, 1001)


@pytest.mark.parametrize('runs', [100, 500])
@pytest.mark.parametrize('t_horizon', [1, 500, 1001])
def test_joos_2013_monte_carlo(runs, t_horizon) -> None:
    summary, results = joos_2013_monte_carlo(runs=runs, t_horizon=t_horizon)
    assert results.shape == (t_horizon, runs)
