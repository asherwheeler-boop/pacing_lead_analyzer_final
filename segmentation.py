
import numpy as np
import pandas as pd


def build_segments(inhale, exhale):
    df = pd.DataFrame()
    df['x'] = inhale['X-Coordinate (um)']
    df['Ca'] = 0.5 * abs(exhale['C'] - inhale['C'])
    return df, df


# LOCK TO DD-0102 STRUCTURE

def enforce_dd0102_segments(df):

    total_points = len(df)

    wire1_points = int(total_points * 0.6)
    wire2_points = total_points - wire1_points

    df['wire'] = [1 if i < wire1_points else 2 for i in range(total_points)]

    segments = []

    seg_counts = {1: 19, 2: 15}

    for wire in [1,2]:
        sub_idx = df[df['wire']==wire].index
        n = len(sub_idx)
        bins = np.linspace(0, n, seg_counts[wire]+1, dtype=int)

        seg_id = []
        for i in range(seg_counts[wire]):
            seg_id.extend([i]*(bins[i+1]-bins[i]))

        df.loc[sub_idx, 'segment'] = seg_id[:n]

    df['segment'] = df['segment'].astype(int)

    table = df.groupby(['wire','segment']).agg({
        'Ca':['mean','max','std']
    })

    table.columns = ['Ca_mean','Ca_max','Ca_std']

    return table.reset_index()
