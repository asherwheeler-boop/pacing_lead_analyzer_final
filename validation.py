
import pandas as pd
import numpy as np


def compare_to_dd0102(calc, reference):

    ref = reference.copy()

    if 'Ca' not in ref.columns:
        return pd.DataFrame({'Error':['Reference missing Ca column']})

    calc_vals = calc['Ca_mean'].values
    ref_vals = ref['Ca'].values[:len(calc_vals)]

    rmse = np.sqrt(((calc_vals - ref_vals)**2).mean())

    df = pd.DataFrame({
        'Calculated': calc_vals,
        'Reference': ref_vals,
        'Difference': calc_vals - ref_vals
    })

    df['RMSE'] = rmse

    return df
