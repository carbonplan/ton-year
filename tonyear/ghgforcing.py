# Module developed from: https://github.com/gschivley/ghgforcing/blob/master/ghgforcing/ghgforcing.py
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


import numpy as np
import scipy as sp
from scipy.interpolate import interp1d
from scipy.signal import fftconvolve
from scipy.integrate import cumtrapz
from scipy.stats import multivariate_normal, norm
import pandas as pd
import random


def CO2_AR5(t, **kwargs):
    """ Returns the IRF for CO2 using parameter values from IPCC AR5/Joos et al (2013)
    Keyword arguments are parameter values.
    """

    a0 = kwargs.get('a0', 0.2173)
    a1 = kwargs.get('a1', 0.224)
    a2 = kwargs.get('a2', 0.2824)
    a3 = kwargs.get('a3', 0.2763)
    tau1 = kwargs.get('tau1', 394.4)
    tau2 = kwargs.get('tau2', 36.54)
    tau3 = kwargs.get('tau3', 4.304)

    IRF = a0 + a1*np.exp(-t/tau1) + a2*np.exp(-t/tau2) + a3*np.exp(-t/tau3)
    return IRF

def CO2(emission, years, tstep=0.01, kind='RF', interpolation='linear', source='AR5',
         runs=1, RS=1, full_output=False, **kwargs):
    """
    a0=0.2173, a1=0.224, a2=0.2824, a3=0.2763, tau1=394.4, tau2=36.54, tau3=4.304,
        RE=1.756E-15,
    Transforms an array of CO2 emissions into radiative forcing, CRF, or temperature
    with user defined time-step.
    Parameters:
        emission: an array of emissions, should be same size as years
        years: an array of years at which the emissions take place
        tstep: time step to be used in the calculations
        kind: RF, CRF, or temp
        interpolation: the type of interpolation to use; can be linear or cubic
        source: the source of parameters for the temperature IRF. default is AR5,
        'Alt', 'Alt_low', and 'Alt_high' are also options.
        runs: Number of runs for monte carlo. A single run will return a numpy array, multiple
        runs will return a pandas dataframe with columns "mean", "+sigma", and "-sigma".
        RS: Random state initiator for continuity between calls
        full_output: When True, outputs the results from all runs as an array in addition to
        the mean and +/- sigma as a DataFrame
    Keyword arguments are used to pass random IRF parameter values for a single run as
    part of a larger monte carlo calculation (currently limited to CH4 decomposing to
    CO2 in the *CH4* function).
    Returns:
        output: When runs=1, deterministic RF, CRF, or temp. When runs > 1 and full_output is
                False, returns a dataframe with 'mean', '+sigma', and '-sigma' columns.
        output, full_output: Only returned when full_output=True. Both the dataframe with
                'mean', '+sigma', and '-sigma' columns, and a numpy array with results
                from all MC runs.
    """

    #Adjust years so that they start at zero
    if min(years) > 0:
        years = years - min(years)

    #Years and emissions to equal-spaced intervals (tstep)
    end = max(years)
    f = interp1d(years, emission, kind=interpolation)
    time = np.linspace(years[0], end, end/tstep + 1)
    inter_emissions = f(time)

    results = np.zeros((len(time), runs))
    slice_step = int(1/tstep)

    #Monte Carlo calculations when runs > 1
    if runs > 1:

        # sigma and x are from Olivie and Peters (2013) Table 5 (J13 values)
        # They are the covariance and mean arrays for CO2 IRF uncertainty
        sigma = np.array([[0.129, -0.058, 0.017,    -0.042,    -0.004,    -0.009],
                        [-0.058, 0.167,    -0.109,    0.072,    -0.015,    0.003],
                        [0.017,    -0.109,    0.148,    -0.043,    0.013,    -0.013],
                        [-0.042, 0.072,    -0.043,    0.090,    0.009,    0.006],
                        [-0.004, -0.015, 0.013,    0.009,    0.082,    0.013],
                        [-0.009, 0.003,    -0.013,    0.006,    0.013,    0.046]])

        x = np.array([5.479, 2.913,    0.496, 0.181, 0.401, -0.472])

        #Generic name (data) for the IRF monte carlo results
        data = multivariate_normal.rvs(x,sigma, runs, random_state=RS)

        #Using a dataframe to make coding easier below
        data_df = pd.DataFrame(data, columns=['t1', 't2', 't3', 'b1','b2','b3'])

        df_exp = np.exp(data_df)

        #All parameter values for the CO2 IRF (tau and a)
        a0 = 1 / (1 + df_exp['b1'] + df_exp['b2'] + df_exp['b3'])
        a1 = df_exp['b1'] / (1 + df_exp['b1'] + df_exp['b2'] + df_exp['b3'])
        a2 = df_exp['b2'] / (1 + df_exp['b1'] + df_exp['b2'] + df_exp['b3'])
        a3 = df_exp['b3'] / (1 + df_exp['b1'] + df_exp['b2'] + df_exp['b3'])

        tau1=df_exp['t1'].values
        tau2=df_exp['t2'].values
        tau3=df_exp['t3'].values

        # 90% CI is +/- 10% of mean. Divide by 1.64 to find sigma
        RE = norm.rvs(1.756e-15, 1.756e-15 * .1 / 1.64, size=runs, random_state=RS+1)


        #Is there a way to do this in parallel?
        #*Should* it be done in parallel here?
        for count in np.arange(runs):
            co2_kwargs = {'a1' : a1[count],
                        'a2' : a2[count],
                        'a3' : a3[count],
                        'tau1' : tau1[count],
                        'tau2' : tau2[count],
                        'tau3' : tau3[count]}
            CO2_re = RE[count]

            atmos = np.resize(fftconvolve(CO2_AR5(time, **co2_kwargs),
                              inter_emissions), time.size) * tstep
            rf = atmos * CO2_re


            #Calculation of temperature from forcing
            if kind == 'temp':
                temp = np.resize(fftconvolve(AR5_GTP(time), rf), time.size) * tstep

                #Store individual run in results matrix
                results[:,count] = temp
                #continue

            else:
                #Store individual run in results matrix
                results[:,count] = rf


        #Return only the mean & +/- 1 sigma values for each year
        if full_output == False:
            output = pd.DataFrame(columns = ['mean', '-sigma', '+sigma'])
            if kind == 'CRF':
                crf = cumtrapz(results, dx = tstep, initial = 0, axis=0)
                output['mean'] = np.mean(crf[0::slice_step], axis=1)
                output['-sigma'] = output['mean'] - np.std(crf[0::slice_step], axis=1)
                output['+sigma'] = output['mean'] + np.std(crf[0::slice_step], axis=1)

            elif kind == 'RF' or 'temp':
                output['mean'] = np.mean(results[0::slice_step], axis=1)
                output['-sigma'] = output['mean'] - np.std(results[0::slice_step], axis=1)
                output['+sigma'] = output['mean'] + np.std(results[0::slice_step], axis=1)

            return output

        #Return both the limited and full outputs
        else:
            output = pd.DataFrame(columns = ['mean', '-sigma', '+sigma'])
            if kind == 'CRF':
                crf = cumtrapz(results, dx = tstep, initial = 0, axis=0)
                output['mean'] = np.mean(crf[0::slice_step], axis=1)
                output['-sigma'] = output['mean'] - np.std(crf[0::slice_step], axis=1)
                output['+sigma'] = output['mean'] + np.std(crf[0::slice_step], axis=1)

                full_output = crf[0::slice_step]

            elif kind == 'RF' or 'temp':
                output['mean'] = np.mean(results[0::slice_step], axis=1)
                output['-sigma'] = output['mean'] - np.std(results[0::slice_step], axis=1)
                output['+sigma'] = output['mean'] + np.std(results[0::slice_step], axis=1)

                full_output = results[0::slice_step]


            return output, full_output


    #Deterministic calculations when runs not > 1
    else:
        CO2_re=1.756E-15
        atmos = np.resize(fftconvolve(CO2_AR5(time, **kwargs),
                            inter_emissions), time.size) * tstep
        rf = atmos * CO2_re

        if kind == 'RF':
            return rf[0::slice_step]
        elif kind == 'CRF':
            crf = cumtrapz(rf, dx = tstep, initial = 0)
            return crf[0::slice_step]
        elif kind == 'temp':
            if source == 'AR5':
                temp = np.resize(fftconvolve(AR5_GTP(time), rf), time.size) * tstep
            elif source == 'Alt':
                temp = np.resize(fftconvolve(Alt_GTP(time), rf), time.size) * tstep
            elif source == 'Alt_low':
                temp = np.resize(fftconvolve(Alt_low_GTP(time), rf),
                                time.size) * tstep
            elif source == 'Alt_high':
                temp = np.resize(fftconvolve(Alt_high_GTP(time), rf),
                                time.size) * tstep
            return temp[0::slice_step]
