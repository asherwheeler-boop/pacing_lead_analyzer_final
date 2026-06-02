import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Pacing Lead Analyzer", layout="wide")

st.title("Pacing Lead Analyzer")

# ================= SIDEBAR =================
with st.sidebar:
    st.subheader("📚 DD-0102 Dataset Upload")

    dd0102_file = st.file_uploader(
        "Upload DD-0102 Excel or CSV",
        type=["xlsx","xls","csv"]
    )

    ref_df = None
    patients = []

    if dd0102_file is not None:
        try:
            if dd0102_file.name.endswith(("xlsx","xls")):
                ref_df = pd.read_excel(dd0102_file)
            else:
                ref_df = pd.read_csv(dd0102_file)

            st.success("✅ Dataset loaded successfully")

            if "Patient" in ref_df.columns:
                patients = sorted(pd.to_numeric(ref_df["Patient"], errors="coerce").dropna().unique())
                st.write("Patients:", patients)

        except Exception as e:
            st.error(f"❌ Failed to load dataset: {e}")

    st.divider()
    st.header("Settings")

# ================= MAIN =================

st.subheader("Upload Analysis Files")
col1, col2 = st.columns(2)

with col1:
    fi = st.file_uploader("Front Inhale", type=["csv","xlsx"])
    fe = st.file_uploader("Front Exhale", type=["csv","xlsx"])

with col2:
    si = st.file_uploader("Side Inhale", type=["csv","xlsx"])
    se = st.file_uploader("Side Exhale", type=["csv","xlsx"])

if all([fi, fe, si, se]):
    st.success("✅ Files uploaded successfully")

    st.subheader("Results Placeholder")
    st.write("Your analysis engine output will appear here.")

    if ref_df is not None:
        st.subheader("📊 DD-0102 Validation Ready")
        st.write("Dataset is connected. Ready to compare.")
