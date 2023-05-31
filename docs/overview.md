# Conceptual Overview

## Carbon dioxide impulse response function

Impulse response functions (IRFs) model the long-term change in atmospheric carbon dioxide (`CO₂`) as a result of a `CO₂` emission. IRFs model this change with a curve representing the proportion of an emission remaining in the atmosphere as a function of time.

Our analyses rely on the [Joos et al., 2013](https://doi.org/10.5194/acp-13-2793-2013) carbon dioxide IRF, which used data from fifteen climate models to derive a simplified, empirical function that characterizes the equilibrium response of `CO₂` added to the atmosphere.

We also implemented two additional IRF curves to enable replication of published ton-year accounting results: the IRFs parameterized in the [IPCC AR4 2007 report (Chapter 2, page 213)](https://www.ipcc.ch/site/assets/uploads/2018/02/ar4-wg1-chapter2-1.pdf) and the IPCC [LULUCF Special Report 2000 (Chapter 2.3.6.3, Footnote 4)](https://www.ipcc.ch/site/assets/uploads/2018/02/ar4-wg1-chapter2-1.pdf).

We chose to use the Joos et al., 2013 model over the other implementations because it was more recently modeled and because it’s possible to estimate [uncertainty in the Joos IRF parameters](https://doi.org/10.5194/esd-4-267-2013).

We validated our implementation of the Joos et al., 2013 IRF by replicating it to the time-dependent remaining CO₂` fractions reported in Joos et al., 2013 (Section 4.1). We also replicated the time-integrated IRF mean values for the Joos et al, 2013 curve reported in the [IPCC AR5 Chapter 8 SM report (Table 8.SM.11)](https://www.ipcc.ch/site/assets/uploads/2018/07/WGI_AR5.Chap_.8_SM.pdf). All values were [replicated precisely](https://github.com/carbonplan/ton-year/blob/main/tonyear/tests/test_tonyear.py).

One unintuitive aspect of how the impulse response functions are implemented is that the values in an array representing the curve mark the transition between years rather than the value for a year. The array starts when an emission is released into the atmosphere at t=0, index=0. If you are interested in examining the curve over the 100 years after the emission, you would be interested in the slice of the array from index=0 to index=100, inclusive. In other words, any array representing N years of the curve will have N+1 elements. This can get a little confusing because of Python’s zero-based indexing. In some places, like [`calculate_tonyears`](https://ton-year.readthedocs.io/en/latest/generated/tonyear.calculate_tonyears#tonyear.calculate_tonyears), we handle this logic for you.

## Ton-year Methods

We implemented two prominent ton-year methods: the Moura Costa method and the Lashof method. Both implementations take a common set of parameters and return a dictionary object with key information about the resulting ton-year accounting calculation.

The input parameters include an impulse response function, a time horizon, a delay and a discount rate. These parameters are talked about in more detail below.

### Moura Costa

The Moura Costa method calculates the benefit of carbon storage in the most straightforward way possible: count up the number of tons stored and multiply by the storage duration. In other words, Moura Costa looks at the carbon-storage, but does not does not directly quantify atmospheric outcomes nor consider the potential impact of re-emission after the temporary storage period.

We implemented the Moura Costa method according to the description in [Moura Costa and Wilson, 2000](https://oxfordclimatepolicy.org/sites/default/files/10.1023%252FA_1009697625521.pdf).

We validated our implementation of the Moura Costa method by replicating the values reported in the [IPCC Special Report on Land Use, Land-Use Change and Forestry (2000)](https://archive.ipcc.ch/ipccreports/sres/land_use/index.php?idp=74). We also replicate the results communicated in [NCX’s 2020 Version 0.4 white paper](https://ncx.com/wp-content/uploads/2021/06/Forests-and-Carbon_A-Guide-for-Buyers-and-Policymakers_SilviaTerra2020_v0.4-2-1.pdf).

### Lashof

The Lashof method looks only at the atmospheric outcomes of temporary storage and assumes that the temporarily stored carbon is fully re-emitted at the end of the storage period. Lashof’s benefit calculation asks how many ton-years of atmospheric impact are avoided within the specified time horizon.

We implemented the method as described in [
, Lashof & Moura-Costa, 2000](https://doi.org/10.1023/A:1009625122628).

We validated our implementation of the Lashof method by replicating the values reported in the [IPCC Special Report on Land Use, Land-Use Change and Forestry (2000)](https://archive.ipcc.ch/ipccreports/sres/land_use/index.php?idp=74).

### Climate Action Reserve

The Climate Action Reserve (CAR) ton-year method calculates the benefit of temporary carbon storage
by (1) defining the duration of carbon storage considered equivalent to an emission and (2) awarding
proportional credit linearly over the time horizon for more temporary storage. In essence, the CAR method awards benefit linearly in proportion to the time_horizon of choice.

CAR specifically defines 100 year storage as "completely mitigating an equal GHG emission
elsewhere." In other words, CAR claims that storing 1 tCO2 for 100 years (100 ton-years of storage)
is equivalent to a 1 tCO2 emission. Storing 1 tCO2 for 1 years (1 ton-years) would only provide
1/100th of the benefit needed for equivalence. Similarly, storing 1 tCO2 for 20 years (20 ton-years)
would provide 1/5th of the benefit needed for equivalence.

We implemented the method as described in CAR's Soil Enrichment Protocol (V1) in section 3.5.5:
https://www.climateactionreserve.org/wp-content/uploads/2020/10/Soil-Enrichment-Protocol-V1.0.pdf

### Government of Quebec

The governement of Quebec (specifically the Ministère de l’Environnement et de la Lutte contre les
changements climatiques) has published a draft ton-year accounting method which (as of
February 8 2022) was
[presented](https://www.environnement.gouv.qc.ca/changements/carbone/credits-compensatoires/index-en.htm#developing-regulations-work)
as a work in progress to "allow more offset credit projects to be carried out and to increase the
supply of Québec credits..." The proposed method calculates the benefit of temporary carbon storage
by (1) defining the duration of carbon storage considered equivalent to an emission and (2) awarding
credit over the time horizon in proportion to the shape of the IRF curve.

We implemented the method as described in a slide deck presenting the draft ton-year accounting approach:
https://www.environnement.gouv.qc.ca/changements/carbone/credits-compensatoires/quebec-protocole-foret-en.pdf

## Parameters

### Time horizon

The choice of a time horizon specifies the period (in years) over which costs and benefits are considered. In our implementation of the ton-year accounting methods, a user may specify any time horizon from 1 <= t <= 1000. Though `CO₂` emissions have atmospheric impacts for millennia, the time horizon is capped at 1000 years as this is the time period for which the modeled impulse response function is valid.

While a 100-year time horizon is often used in policy conversations, it’s important to keep in the back of our minds that `CO₂` stays in the atmosphere for significantly longer periods of time.
[Pierrehumbert 2014](https://doi.org/10.1146/annurev-earth-060313-054843) provides an excellent review of this.

### Delay

The delay specifies a temporary storage period (years) for which a ton-year benefit will be calculated. In our implementation, a user may specify any delay that is greater than or equal to zero.

### Discount rate

Specifies the discount rate to which is applied both costs and benefits over the time horizon. It is not particularly clear what the application of a discount rate within ton-year accounting is meant to represent, as financial discounting is designed for valuing monetary payments/damages over time. However, since discount rates are being used in real-world ton-year accounting applications, we include it as a parameter to enable replication and exploration of the implications. For more details, we’ve written a longer [explainer piece](https://carbonplan.org/research/ton-year-explainer) that goes into why we’re uncomfortable with applying discount rates directly to IRFs.
