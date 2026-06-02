
import streamlit as st

from processing import load_and_prepare
from segmentation import build_segments, enforce_dd0102_segments
from validation import compare_to_dd0102
from export_report import build_excel_report

st.set_page_config(layout='wide')
st.title("DD-0102 Exact Validation System")

fi = st.file_uploader("Front Inhale")
fe = st.file_uploader("Front Exhale")
ri = st.file_uploader("Right Inhale")
re = st.file_uploader("Right Exhale")
dd_file = st.file_uploader("DD-0102 Reference Excel (optional)")

if st.button("Run Validation"):

    if None in [fi, fe, ri, re]:
        st.error("Upload all required files")
    else:
        fi_df, fe_df = load_and_prepare(fi, fe)
        ri_df, re_df = load_and_prepare(ri, re)

        front_df, front_seg = build_segments(fi_df, fe_df)
        right_df, right_seg = build_segments(ri_df, re_df)

        front_locked = enforce_dd0102_segments(front_df)
        right_locked = enforce_dd0102_segments(right_df)

        st.subheader("Locked Segment Tables")
        st.dataframe(front_locked)
        st.dataframe(right_locked)

        if dd_file:
            dd_ref = load_and_prepare(dd_file, dd_file)[0]
            comparison = compare_to_dd0102(front_locked, dd_ref)
            st.subheader("Validation vs DD-0102")
            st.dataframe(comparison)

        excel = build_excel_report(front_locked, right_locked)

        st.download_button(
            "Download Validation Report",
            excel,
            file_name="DD0102_validation.xlsx"
        )
