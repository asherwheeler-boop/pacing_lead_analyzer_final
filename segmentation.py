import numpy as np
import pandas as pd

def build_segments(inhale, exhale):

    df = pd.DataFrame()

    df["x"] = inhale["X-Coordinate (um)"]
    df["y"] = inhale["Y-Coordinate (um)"]

    df["Ca"] = 0.5 * abs(exhale["C"] - inhale["C"])

    dx = np.diff(df["x"])
    dy = np.diff(df["y"])
    dist = np.sqrt(dx**2 + dy**2)

    wire = np.zeros(len(df))
    current_wire = 1

    for i in range(1, len(df)):
        if dist[i-1] > dist.mean() * 5:
            current_wire += 1
        wire[i] = current_wire

    df["wire"] = wire.astype(int)

    seg = np.zeros(len(df))
    current_seg = 0

    dCa = df["Ca"].diff().fillna(0)

    for i in range(1, len(df)):
        if abs(dCa[i]) > df["Ca"].std():
            current_seg += 1
        seg[i] = current_seg

    df["segment"] = seg.astype(int)

    seg_table = df.groupby(["wire", "segment"]).agg({"Ca": ["mean", "max", "std"]})
    seg_table.columns = ["Ca_mean", "Ca_max", "Ca_std"]

    return df, seg_table.reset_index()
