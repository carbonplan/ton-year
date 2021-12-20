from itertools import product

import pandas as pd

import tonyear

TARGET_DIR = '/tmp'

def main():
    methods = ['mc', 'ipcc']
    delay_lengths = [1] + [x for x in range(20, 101, 20)]
    integration_times = [100]

    baseline_curve = tonyear.get_baseline_curve('joos_2013')

    store = []

    for delay_length, method, integration_time in product(delay_lengths, methods, integration_times):
        tonyear_calc = tonyear.calculate_tonyears(method, baseline_curve, 100, delay_length, 0)

        avoided_comparison = tonyear.get_avoided_comparison(tonyear_calc, baseline_curve, integration_time)
        avoided_comparison.update(method=method, integration_time=integration_time)

        store.append(avoided_comparison)

    data = pd.DataFrame(store)
    data['ratio'] = (data['delay_crf'] - data['avoided_crf']) / data['avoided_crf']
    data.to_csv(f'{TARGET_DIR}/equivalency_data.csv', float_format="%.3f", index=False)

if __name__ == '__main__':
    main()