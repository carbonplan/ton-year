import json

import numpy as np


def get_baseline_curve(curve_name: str, t_horizon: int = 1001) -> np.ndarray:
    """Build the baseline curve

    Parameters
    ----------
    curve_name : str
        Name of baseline curve
    t_horizon : int
        Length of the time horizon (years)

    Returns
    -------
    baseline_curve : np.ndarray
        Baseline curve in the form of an 1D array
    """

    if t_horizon <= 0:
        raise ValueError("t_horizon must be a postive integer")

    if curve_name == "joos_2013":
        # parameters from Joos et al., 2013 (Table 5)
        # https://doi.org/10.5194/acp-13-2793-2013
        a = [0.2173, 0.2240, 0.2824, 0.2763]
        tau = [0, 394.4, 36.54, 4.304]
    elif curve_name == "ipcc_2007":
        # parameters from IPCC AR4 2007 (Chapter 2, page 213)
        # https://www.ipcc.ch/site/assets/uploads/2018/02/ar4-wg1-chapter2-1.pdf
        a = [0.217, 0.259, 0.338, 0.186]
        tau = [0, 172.9, 18.51, 1.186]
    elif curve_name == "ipcc_2000":
        # parameters from IPCC LULUCF Special Report 2000 (Chapter 2.3.6.3, Footnote 4)
        # https://archive.ipcc.ch/ipccreports/sres/land_use/index.php?idp=74
        a = [0.175602, 0.137467, 0.18576, 0.242302, 0.258868]
        tau = [0, 421.093, 70.5965, 21.42165, 3.41537]
    else:
        raise ValueError(f"No baseline curve parameters by the name {curve_name}.")

    baseline_curve = np.full(t_horizon, a[0])
    for t in range(t_horizon):
        for i in np.arange(1, len(a)):
            baseline_curve[t] += a[i] * np.exp(-t / tau[i])
    return baseline_curve


def get_discounted_curve(discount_rate: float, curve: np.ndarray) -> np.ndarray:
    """Get discounted curve

    Parameters
    ----------
    discount_rate : float
        Discount rate expressed as a fraction.
    curve : np.ndarray

    Returns
    -------
    discounted_curve : np.ndarray
        Curve with discount rate applied.
    """
    return curve / np.power(1 + discount_rate, np.arange(len(curve)))


def print_benefit_report(method_output: dict) -> None:
    """print the benefit report"""
    discount = str(round(method_output["parameters"]["discount_rate"] * 100, 1))
    delay = str(method_output["parameters"]["delay"])
    baseline_atm_cost = str(round(method_output["baseline_atm_cost"], 2))
    benefit = str(round(method_output["benefit"], 2))
    num_needed = str(round(method_output["num_for_equivalence"], 1))

    print()
    print("Discount rate: " + discount + "%")
    print("Delay: " + delay + " year(s)")
    print("Baseline atmospheric cost: " + baseline_atm_cost + " ton-years")
    print("Benefit from 1tCO2 with delay: " + benefit + " ton-years")
    print("Number needed: " + num_needed)
    print()


def get_avoided_comparison(
    tonyear_calc: dict,
    baseline_curve: np.array,
    integration_time: int,
) -> dict:
    """
    Compare cumulative radiative forcing of delaying 1 tCO2  against cumulative radiative forcing of permanently
     avoiding the emission of a smaller amount of CO2.
    Parameters
    ----------
    tonyear_calc: dict
        output from `calculate_tonyear`
    baseline_curve: np.array
        CO2 IRF curve
    integration_time: int
        time period to evaluate equivalence claim; does _not_ have to equal time_horizon from IRF curve generation

    Returns
    -------
        dict with cumulative radiative forcing for delay and avoid
    """
    DELAY_SIZE = 1  # tC02
    delay_length = tonyear_calc["parameters"]["delay"]
    avoided_size = DELAY_SIZE / tonyear_calc["num_for_equivalence"]

    baseline_crf = np.trapz(baseline_curve[:integration_time])
    avoid_crf = np.trapz(baseline_curve[:integration_time] * avoided_size)

    integate_to = integration_time - delay_length
    delay_crf = baseline_crf - np.trapz(baseline_curve[:integate_to])
    return {
        "delay_length": delay_length,
        "avoided_crf": avoid_crf,
        "delay_crf": delay_crf,
    }


def calculate_tonyears(
    method: str,
    baseline: np.ndarray,
    time_horizon: int,
    delay: int,
    discount_rate: float,
):
    """This function calculates the benefit of a delayed emission according one
    of three ton-year accounting methods.

    Parameters
    ----------
    method : str
        The ton-year accounting method (Moura-Costa: 'mc', Lashof: 'lashof', or IPCC 'ipcc')
    baseline : np.ndarray
        Array modeling the residence of an emission in the atmosphere over time, i.e. a decay
        curve / impulse response function
    time_horizon : int
        Specifies the period over which the impact of an emission is considered (years)
    delay : int
        Specifies the emission delay for which a ton-year benefit will be calculated (years)
    discount_rate : float
        Specifies the discount rate to apply time preference to both costs and benefits over the
        time horizon

    Returns
    -------
    method_dict : dict
        Dictionary with the following keys:
            parameters: key parameters used for the calculation
            baseline: array modeling baseline emission curve (discounted if applicable)
            scenario: array modeling the scenario curve (discounted if applicable)
            baseline_atm_cost: the cost of of a baseline emission (ton-years)
            benefit: the benefit of delaying an emission, calculated according to specified
            accounting method (ton-years)
            num_for_equivalence: the ratio between the baseline cost and the benefit
    """

    if delay < 0:
        raise ValueError("Delay cannot be negative.")
    if time_horizon <= 0:
        raise ValueError("Time horizon must be greater than zero.")
    if len(baseline) < time_horizon:
        raise ValueError(
            "Time horizon cannot be longer than length of the baseline array."
        )

    # All methods calculate the baseline cost of emitting 1tCO2 at t=0 as the
    # atmospheric ton-years incurred over the period 0<=t<=time_horizon.
    time_horizon_timesteps = time_horizon + 1
    baseline = baseline[:time_horizon_timesteps]
    baseline_discounted = get_discounted_curve(discount_rate, baseline)
    baseline_atm_cost = np.trapz(baseline_discounted)

    if method == "mc":
        # The Moura-Costa method calculates the ton-year benefit of a delayed emission
        # as the ton-years of carbon storage outside of the atmosphere over the period
        # 0<=t<=delay. Moura-Costa ignores the atmospheric impact of post-storage re-emission.
        delay_timesteps = delay + 1
        scenario = np.concatenate(
            (np.full(delay_timesteps, -1), np.zeros(len(baseline) - delay_timesteps))
        )
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = -np.trapz(scenario[:delay_timesteps])

    elif method == "ipcc":
        # The IPCC method calculates calculates the ton-year benefit of an emission at t=delay
        # as the difference between the baseline atmospheric cost and the scenario atmospheric
        # cost, which is calculated over the period delay<=t<=time_horizon.
        scenario = np.concatenate((np.zeros(delay), baseline))[:time_horizon_timesteps]
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = baseline_atm_cost - np.trapz(scenario[delay:])

    elif method == "lashof":
        # The Lashof method calculates the ton-year benefit of an emission at t=delay
        # as the atmospheric cost that no longer occurs within the time horizon. The
        # benefit calculation is thus focused the period time_horizon<=t<=(time_horizon+delay).
        scenario = np.concatenate((np.zeros(delay), baseline))
        scenario = get_discounted_curve(discount_rate, scenario)
        benefit = np.trapz(scenario[time_horizon:])

    else:
        raise ValueError(f"No ton-year accounting method called {method}")

    return {
        "parameters": {
            "method": method,
            "time_horizon": time_horizon,
            "delay": delay,
            "discount_rate": discount_rate,
        },
        "baseline": baseline_discounted,
        "scenario": scenario,
        "baseline_atm_cost": baseline_atm_cost,
        "benefit": benefit,
        "num_for_equivalence": baseline_atm_cost / benefit,
    }


def write_json(collection, output):
    """helper function to write collection to a local json file"""
    with open(output, "w") as f:
        f.write(json.dumps(collection))
