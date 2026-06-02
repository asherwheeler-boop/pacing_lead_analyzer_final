
import streamlit as st
import pandas as pd

st.title("Pacing Lead Analyzer with Validation")

uploaded_file = st.file_uploader("Upload DD0102 Excel Database", type=["xlsx"])

if uploaded_file is not None:
    df_excel = pd.read_excel(uploaded_file)
    st.success("Database loaded successfully")
    st.dataframe(df_excel.head())
else:
    st.warning("Please upload DD0102_Full_Database_Template.xlsx")
