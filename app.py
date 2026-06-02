import streamlit as st
import pandas as pd

from analysis.processing import load_and_prepare
from analysis.segmentation import build_segments
from analysis.threeD_model import build_3d_wire, plot_3d_wire_split
from analysis.animation import plot_animation_multi

st.set_page_config(layout="wide")
st.title("DD-0102 Full Validation System")

fi_file = st.file_uploader("Front Inhale")
fe_file = st.file_uploader("Front Exhale")
ri_file = st.file_uploader("Right Inhale")
re_file = st.file_uploader("Right Exhale")

if st.button("Run Full System"):

    fi, fe = load_and_prepare(fi_file, fe_file)
    ri, re = load_and_prepare(ri_file, re_file)

    front_df, front_segments = build_segments(fi, fe)
    right_df, right_segments = build_segments(ri, re)

    st.subheader("Segment Tables")
    st.dataframe(front_segments)
    st.dataframe(right_segments)

    wire_3d_in = build_3d_wire(front_df, right_df)

    st.subheader("3D Wire Model")
    st.plotly_chart(plot_3d_wire_split(wire_3d_in), use_container_width=True)

    st.subheader("Animation")
    st.plotly_chart(plot_animation_multi(wire_3d_in, wire_3d_in), use_container_width=True)
