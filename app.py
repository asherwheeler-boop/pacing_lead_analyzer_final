import io
import pandas as pd
import streamlit as st
from curvature_engine import (
    load_builtin_dd_dataset,
    load_user_dataset,
    compare_datasets,
    generate_comparison_plot,
    export_comparison_excel,
)

st.set_page_config(page_title="DD-0102 Comparison", page_icon="📊", layout="wide")
st.title("📊 DD-0102 Dataset Comparison")
st.caption("Compare a user dataset against bundled DD-0102 patient reference files.")

with st.sidebar:
    st.header("Reference dataset")
    dataset_label = st.selectbox(
        "DD-0102 patient",
        ["Patient 1011", "Patient 1012"],
        index=0,
        help="These are bundled with the web app and load automatically from the repo."
    )

    try:
        dd_df, dd_file = load_builtin_dd_dataset(dataset_label)
        st.success(f"Loaded {dataset_label}")
        st.caption(f"Source file: {dd_file}")
        st.caption(f"Reference rows: {len(dd_df)}")
    except Exception as exc:
        dd_df, dd_file = None, None
        st.error(f"Could not load reference dataset: {exc}")

    st.divider()
    st.header("User dataset")
    user_file = st.file_uploader(
        "Upload Excel or CSV with Segment/Re/Ri/Ca columns",
        type=["xlsx", "xls", "csv"],
        help="Required: Segment and Ca. Re and Ri are optional but recommended. Column names are matched flexibly."
    )

    run_clicked = st.button("🚀 Run comparison", type="primary", use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Bundled DD-0102 preview")
    if dd_df is not None:
        st.dataframe(dd_df, use_container_width=True, height=280)

with right:
    st.subheader("User dataset preview")
    if user_file is not None:
        try:
            user_preview = load_user_dataset(user_file)
            st.dataframe(user_preview, use_container_width=True, height=280)
        except Exception as exc:
            st.error(f"Could not read uploaded dataset: {exc}")
    else:
        st.info("Upload a user dataset to preview it here.")

if run_clicked:
    if dd_df is None:
        st.error("Reference DD-0102 dataset could not be loaded.")
    elif user_file is None:
        st.warning("Upload a user dataset first.")
    else:
        try:
            user_df = load_user_dataset(user_file)
            compare_df, metrics = compare_datasets(user_df, dd_df, dataset_label)

            if compare_df.empty:
                st.warning("No overlapping segment rows were found between the uploaded dataset and the selected DD-0102 patient file.")
            else:
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Segments compared", metrics["n_segments"])
                m2.metric("Mean absolute error", f"{metrics['mae']:.5f}")
                m3.metric("RMSE", f"{metrics['rmse']:.5f}")
                m4.metric("Largest absolute error", f"{metrics['max_abs_error']:.5f}")

                counts = compare_df["Status"].value_counts(dropna=False).to_dict()
                st.markdown(
                    f"**Status summary** — PASS: {counts.get('PASS', 0)} | WARNING: {counts.get('WARNING', 0)} | FAIL: {counts.get('FAIL', 0)}"
                )

                fig = generate_comparison_plot(compare_df, dataset_label)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)

                def style_rows(row):
                    status = row.get("Status", "")
                    if status == "PASS":
                        return ["background-color:#d4edda"] * len(row)
                    if status == "WARNING":
                        return ["background-color:#fff3cd"] * len(row)
                    if status == "FAIL":
                        return ["background-color:#f8d7da"] * len(row)
                    return [""] * len(row)

                st.subheader("Comparison table")
                st.dataframe(compare_df.style.apply(style_rows, axis=1), use_container_width=True, height=420)

                csv_bytes = compare_df.to_csv(index=False).encode("utf-8")
                xlsx_bytes = export_comparison_excel(compare_df, metrics, dataset_label)
                c1, c2 = st.columns(2)
                c1.download_button(
                    "⬇️ Download comparison CSV",
                    data=csv_bytes,
                    file_name=f"comparison_{dataset_label.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                c2.download_button(
                    "⬇️ Download comparison Excel",
                    data=xlsx_bytes,
                    file_name=f"comparison_{dataset_label.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")
