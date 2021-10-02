import json
import math

import numpy as np


def get_baseline_curve(curve_name):
    if curve_name == 'joos_2013':
        # parameters from Joos et al., 2013 (Table 5)
        # https://doi.org/10.5194/acp-13-2793-2013
        a = [0.2173, 0.2240, 0.2824, 0.2763]
        tau = [0, 394.4, 36.54, 4.304]
        t_horizon = np.arange(1001)
    elif curve_name == 'ipcc_2007':
        # parameters from IPCC AR4 2007 (Chapter 2, page 213)
        # https://www.ipcc.ch/site/assets/uploads/2018/02/ar4-wg1-chapter2-1.pdf
        a = [0.217, 0.259, 0.338, 0.186]
        tau = [0, 172.9, 18.51, 1.186]
        t_horizon = np.arange(1001)
    elif curve_name == 'ipcc_2000':
        # parameters from IPCC LULUCF Special Report 2000 (Chapter 2.3.6.3, Footnote 4)
        # https://archive.ipcc.ch/ipccreports/sres/land_use/index.php?idp=74
        a = [0.175602, 0.137467, 0.18576, 0.242302, 0.258868]
        tau = [0, 421.093, 70.5965, 21.42165, 3.41537]
        t_horizon = np.arange(1001)
    else:
        raise ValueError('No baseline curve parameters by the name \'' + curve_name + '\'.')

    baseline_curve = [a[0]] * len(t_horizon)
    for t in t_horizon:
        for i in np.arange(1, len(a)):
            baseline_curve[t] = baseline_curve[t] + (a[i] * np.exp(-t / tau[i]))
    return baseline_curve


def get_discounted_curve(discount_rate, curve):
    return [x / math.pow(1 + discount_rate, i) for i, x in enumerate(curve)]


def print_benefit_report(method_output):
    discount = str(round(method_output['parameters']['discount_rate'] * 100, 1))
    delay = str(method_output['parameters']['delay'])
    baseline_atm_cost = str(round(method_output['baseline_atm_cost'], 2))
    benefit = str(round(method_output['benefit'], 2))
    num_needed = str(round(method_output['num_for_equivalence'], 1))

    print()
    print('Discount rate: ' + discount + '%')
    print('Delay: ' + delay + ' year(s)')
    print('Baseline atmospheric cost: ' + baseline_atm_cost + ' ton-years')
    print('Benefit from 1tCO2 with delay: ' + benefit + ' ton-years')
    print('Number needed: ' + num_needed)
    print()


def calculate_tonyears(method, baseline, time_horizon, delay, discount_rate):
    """This function calculates the benefit of a delayed emission according one
    of three ton-year accounting methods.

    Keyword arguments:
        method – string specifying the ton-year accounting method (Moura-Costa: \'mc\',
        Lashof: \'lashof\', or IPCC \'ipcc\')
        baseline – array modeling the residence of an emission in the atmosphere over time,
        i.e. a decay curve / impulse response function
        time_horizon – integer specifying the period over which the impact of an emission
        is considered (years)
        delay – integer specifying the emission delay for which a ton-year benefit will be
        calculated (years)
        discount_rate – float specifying the discount rate to apply time preference to both
        costs and benefits over the time horizon

    Function returns a dictionary with:
        parameters – key parameters used for the calculation
        baseline – array modeling baseline emission curve (discounted if applicable)
        scenario – array modeling the scenario curve (discounted if applicable)
        baseline_atm_cost – the cost of of a baseline emission (ton-years)
        benefit – the benefit of delaying an emission, calculated according to specified
        accounting method (ton-years)
        num_for_equivalence – the ratio between the baseline cost and the benefit
    """

    if delay < 0:
        raise ValueError('Delay cannot be negative.')
    if time_horizon <= 0:
        raise ValueError('Time horizon must be greater than zero.')
    if len(baseline) < time_horizon:
        raise ValueError('Time horizon cannot be longer than length of the baseline array.')
    if method not in ['mc', 'ipcc', 'lashof']:
        raise ValueError('No ton-year accounting method called \'' + method)

    # All methods calculate the baseline cost of emitting 1tCO2 at t=0 as the
    # atmospheric ton-years incurred over the period 0<=t<=time_horizon.
    time_horizon_timesteps = time_horizon + 1
    baseline = baseline[:time_horizon_timesteps]
    baseline_discounted = get_discounted_curve(discount_rate, baseline)
    baseline_atm_cost = np.trapz(baseline_discounted)

    if method == 'mc':
        # The Moura-Costa method calculates the ton-year benefit of a delayed emission
        # as the ton-years of carbon storage outside of the atmosphere over the period
        # 0<=t<=delay. Moura-Costa ignores the atmospheric impact of post-storage re-emission.
        delay_timesteps = delay + 1
        scenario = [-1] * (delay_timesteps) + [0] * (len(baseline) - delay_timesteps)
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = -np.trapz(scenario[:delay_timesteps])

    elif method == 'ipcc':
        # The IPCC method calculates calculates the ton-year benefit of an emission at t=delay
        # as the difference between the baseline atmospheric cost and the scenario atmospheric
        # cost, which is calculated over the period delay<=t<=time_horizon.
        scenario = [0] * delay + baseline
        scenario = scenario[:time_horizon_timesteps]
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = baseline_atm_cost - np.trapz(scenario[delay:])

    elif method == 'lashof':
        # The Lashof method calculates the ton-year benefit of an emission at t=delay
        # as the atmospheric cost that no longer occurs within the time horizon. The
        # benefit calculation is thus focused the period time_horizon<=t<=(time_horizon+delay).
        scenario = [0] * delay + baseline
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = np.trapz(scenario[time_horizon:])

    return {
        'parameters': {
            'method': method,
            'time_horizon': time_horizon,
            'delay': delay,
            'discount_rate': discount_rate,
        },
        'baseline': baseline_discounted,
        'scenario': scenario,
        'baseline_atm_cost': baseline_atm_cost,
        'benefit': benefit,
        'num_for_equivalence': baseline_atm_cost / benefit,
    }


def write_json(collection, output):
    with open(output, "w") as f:
        f.write(json.dumps(collection))
