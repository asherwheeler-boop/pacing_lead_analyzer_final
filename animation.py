import numpy as np
import pandas as pd

def build_segments(inhale, exhale):
    df = pd.DataFrame()
    df['x'] = inhale['X-Coordinate (um)']
    df['y'] = inhale['Y-Coordinate (um)']

    C_in = inhale['C']
    C_ex = exhale['C']

    df['Ca'] = 0.5 * abs(C_ex - C_in)

    dx = np.diff(df['x'])
    dy = np.diff(df['y'])
    dist = np.sqrt(dx**2 + dy**2)

    wire = np.zeros(len(df))
    w = 1
    for i in range(1, len(df)):
        if dist[i-1] > dist.mean()*5:
            w += 1
        wire[i] = w
    df['wire'] = wire.astype(int)

    seg = np.zeros(len(df))
    s = 0
    for i in range(1, len(df)):
        if abs(df['Ca'].diff().fillna(0)[i]) > df['Ca'].std():
            s += 1
        seg[i] = s
    df['segment'] = seg.astype(int)

    table = df.groupby(['wire','segment']).agg({'Ca':['mean','max','std']})
    table.columns = ['Ca_mean','Ca_max','Ca_std']

    return df, table.reset_index()
