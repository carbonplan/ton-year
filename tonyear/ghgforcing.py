# Module developed from:
# https://github.com/gschivley/ghgforcing/blob/master/ghgforcing/ghgforcing.py
# The MIT License (MIT)

# Copyright (c) 2016 Greg Schivley

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Tuple

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal


def joos_2013(t_horizon: int, **kwargs) -> np.ndarray:
    """Returns the IRF for CO2 using parameter values from IPCC AR5/Joos et al (2013)
    Keyword arguments are parameter values.

    Parameters
    ----------
    t_horizon : int
        Length of the time horizon (years)

    Returns
    -------
    IRF : np.ndarray
        IRF curve in the form of an 1D array
    """

    a0 = kwargs.get('a0', 0.2173)
    a1 = kwargs.get('a1', 0.224)
    a2 = kwargs.get('a2', 0.2824)
    a3 = kwargs.get('a3', 0.2763)
    tau1 = kwargs.get('tau1', 394.4)
    tau2 = kwargs.get('tau2', 36.54)
    tau3 = kwargs.get('tau3', 4.304)

    t = np.arange(t_horizon)
    IRF = a0 + a1 * np.exp(-t / tau1) + a2 * np.exp(-t / tau2) + a3 * np.exp(-t / tau3)
    return IRF


def joos_2013_monte_carlo(
    runs: int = 100, t_horizon: int = 1001, **kwargs
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Runs a monte carlo simulation for the Joos_2013 baseline IRF curve.

    This function uses uncertainty parameters for the Joos_2013 curve calculated by
    Olivie and Peters (2013): https://esd.copernicus.org/articles/4/267/2013/

    Parameters
    ----------
    runs : int
        Number of runs for Monte Carlo simulation. Must be >1.
    t_horizon : int
        Length of the time horizon over which baseline curve is
        calculated (years)

    Returns
    -------
    summary : pd.DataFrame
        Dataframe with 'mean', '+sigma', and '-sigma' columns summarizing
        results of Monte Carlo simulation.
    results : np.ndarray
        Results from all Monte Carlo runs.
    """

    if runs <= 1:
        raise ValueError('number of runs must be >1')

    results = np.zeros((t_horizon, runs))

    # Monte Carlo simulations

    # sigma and x are from Olivie and Peters (2013) Table 5 (J13 values)
    # They are the covariance and mean arrays for CO2 IRF uncertainty
    sigma = np.array(
        [
            [0.129, -0.058, 0.017, -0.042, -0.004, -0.009],
            [-0.058, 0.167, -0.109, 0.072, -0.015, 0.003],
            [0.017, -0.109, 0.148, -0.043, 0.013, -0.013],
            [-0.042, 0.072, -0.043, 0.090, 0.009, 0.006],
            [-0.004, -0.015, 0.013, 0.009, 0.082, 0.013],
            [-0.009, 0.003, -0.013, 0.006, 0.013, 0.046],
        ]
    )

    x = np.array([5.479, 2.913, 0.496, 0.181, 0.401, -0.472])

    p_samples = multivariate_normal.rvs(x, sigma, runs)
    p_df = pd.DataFrame(p_samples, columns=['t1', 't2', 't3', 'b1', 'b2', 'b3'])

    p_exp = np.exp(p_df)
    a1 = p_exp['b1'] / (1 + p_exp['b1'] + p_exp['b2'] + p_exp['b3'])
    a2 = p_exp['b2'] / (1 + p_exp['b1'] + p_exp['b2'] + p_exp['b3'])
    a3 = p_exp['b3'] / (1 + p_exp['b1'] + p_exp['b2'] + p_exp['b3'])

    tau1 = p_exp['t1']
    tau2 = p_exp['t2']
    tau3 = p_exp['t3']

    for count in np.arange(runs):
        co2_kwargs = {
            'a1': a1[count],
            'a2': a2[count],
            'a3': a3[count],
            'tau1': tau1[count],
            'tau2': tau2[count],
            'tau3': tau3[count],
        }

        irf = joos_2013(t_horizon, **co2_kwargs)
        results[:, count] = irf

    summary = pd.DataFrame(columns=['mean', '-2sigma', '+2sigma', '5th', '95th'])
    summary['mean'] = np.mean(results, axis=1)
    summary['+2sigma'] = summary['mean'] + (1.96 * np.std(results, axis=1))
    summary['-2sigma'] = summary['mean'] - (1.96 * np.std(results, axis=1))
    summary['5th'] = np.percentile(results, 5, axis=1)
    summary['95th'] = np.percentile(results, 95, axis=1)

    return summary, results
