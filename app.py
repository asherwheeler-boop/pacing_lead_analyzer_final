
import pandas as pd
import numpy as np


def compute_curvature(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    return np.abs(dx * ddy - dy * ddx) / np.power(dx**2 + dy**2, 1.5)


def run_analysis(fi, si, fe, se):
    df_fi = pd.read_csv(fi)
    df_fe = pd.read_csv(fe)

    x_i = df_fi.iloc[:,0]
    y_i = df_fi.iloc[:,1]

    x_e = df_fe.iloc[:,0]
    y_e = df_fe.iloc[:,1]

    k_i = compute_curvature(x_i, y_i)
    k_e = compute_curvature(x_e, y_e)

    Ca = np.abs(k_e - k_i) / 2

    return {
        "summary": f"Max Ca: {Ca.max():.4f}",
        "curve": Ca
    }
