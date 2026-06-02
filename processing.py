import pandas as pd

def load_and_prepare(inhale_file, exhale_file):

    inhale = pd.read_csv(inhale_file) if inhale_file.name.endswith('.csv') else pd.read_excel(inhale_file)
    exhale = pd.read_csv(exhale_file) if exhale_file.name.endswith('.csv') else pd.read_excel(exhale_file)

    inhale["C"] = inhale["Point Curvature (um-1)"] * 1e4
    exhale["C"] = exhale["Point Curvature (um-1)"] * 1e4

    return inhale, exhale
