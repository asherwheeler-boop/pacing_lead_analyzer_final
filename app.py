
import streamlit as st
import pandas as pd
from curvature_engine import compute_validation_metrics, export_validation_report

st.title("Pacing Lead Analysis - Validation Enabled")

ref_df = pd.read_csv("dd0102_segment_database.csv")
patient_id = st.selectbox("Select Patient", sorted(ref_df["Patient"].unique()))

st.subheader("DD-0102 Validation Dashboard")

if "computed_results" not in st.session_state:
    st.warning("Run analysis first.")
else:
    computed_results = st.session_state["computed_results"]

    val_df, rmse, mean_error, r2 = compute_validation_metrics(
        computed_results, ref_df, patient_id
    )

    st.write(f"RMSE: {rmse:.5f}")
    st.write(f"Mean Error: {mean_error:.5f}")
    if r2 is not None:
        st.write(f"R²: {r2:.5f}")

    st.dataframe(val_df)

    if st.button("Export Report"):
        file_path = export_validation_report(val_df, rmse, mean_error, r2)
        with open(file_path, "rb") as f:
            st.download_button("Download Excel", f, file_name="DD0102_Validation_Report.xlsx")
