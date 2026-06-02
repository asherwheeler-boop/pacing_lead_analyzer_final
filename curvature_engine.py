
import numpy as np
import pandas as pd
from openpyxl import Workbook


def compute_validation_metrics(computed_results, ref_df, patient_id):
    rows = []
    ref_sub = ref_df[ref_df["Patient"] == int(patient_id)]

    for cname, res in computed_results.items():
        ca_comp = res["Ca_cm"]

        for i, (_, ref_row) in enumerate(ref_sub.iterrows()):
            if i >= len(ca_comp):
                break

            rows.append({
                "Wire": cname,
                "Segment": ref_row["Segment_Reindexed"],
                "Computed_Ca": ca_comp[i],
                "DD0102_Ca": ref_row["Ca_cm-1"],
                "Difference": ca_comp[i] - ref_row["Ca_cm-1"]
            })

    df = pd.DataFrame(rows)

    rmse = np.sqrt(np.mean(df["Difference"]**2))
    mean_error = np.mean(df["Difference"])

    ss_res = np.sum((df["DD0102_Ca"] - df["Computed_Ca"])**2)
    ss_tot = np.sum((df["DD0102_Ca"] - np.mean(df["DD0102_Ca"]))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else None

    return df, rmse, mean_error, r2


def export_validation_report(val_df, rmse, mean_error, r2, filename="validation_report.xlsx"):
    wb = Workbook()
    ws = wb.active

    ws.append(list(val_df.columns))
    for _, row in val_df.iterrows():
        ws.append(list(row))

    ws.append([])
    ws.append(["Metric","Value"])
    ws.append(["RMSE", rmse])
    ws.append(["Mean Error", mean_error])
    ws.append(["R2", r2])

    wb.save(filename)
    return filename
