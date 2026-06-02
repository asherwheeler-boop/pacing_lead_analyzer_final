
import pandas as pd

def load_and_prepare(file1, file2):

    f1 = pd.read_csv(file1) if file1.name.endswith('.csv') else pd.read_excel(file1)
    f2 = pd.read_csv(file2) if file2.name.endswith('.csv') else pd.read_excel(file2)

    f1['C'] = f1['Point Curvature (um-1)'] * 1e4
    f2['C'] = f2['Point Curvature (um-1)'] * 1e4

    return f1, f2
