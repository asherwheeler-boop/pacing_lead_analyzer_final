"""
Streamlit front-end for 3D Pacing Lead Curvature Analyzer v2.
All features: safety, trim, batch, fatigue, heatmap, animation,
calculation transparency, configurable thresholds, patient notes, comparison.
"""
import streamlit as st
import io
import re
from curvature_engine import (
    run_web_analysis, run_batch_from_zip, run_comparison,
    MATERIAL_PROPERTIES, DEFAULT_SAFETY, UNIT_LABELS,
    load_dd0102_database, compute_dd0102_alignment,
    generate_stacked_wire_comparison_plot,
)

st.set_page_config(page_title="Pacing Lead Analyzer v2", page_icon="\U0001fac0",
 layout="wide")

STATUS_COLORS = {"PASS": "#009988", "WARNING": "#EE7733", "FAIL": "#FF0000"}

st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e9ecef; border-radius: 10px;
        padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="stMetric"] label { color: #6c757d; font-size: 0.82rem; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.25rem; font-weight: 700; color: #212529;
    }
    div.block-container { padding-top: 2rem; }
    .status-badge { display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-weight: bold; font-size: 0.95em; color: white; }
    .status-PASS { background: #009988; }
    .status-WARNING { background: #EE7733; }
    .status-FAIL { background: #FF0000; }

    .dd0102-banner {padding: 10px 14px; border-radius: 10px; border: 1px solid #cfe2ff; background: #eef6ff; margin: 8px 0 14px 0;}
    .dd0102-chip {display:inline-block; padding:3px 10px; border-radius:999px; font-weight:700; font-size:0.82rem; margin-right:6px;}
    .dd0102-ok {background:#d4edda; color:#155724;}
    .dd0102-warn {background:#fff3cd; color:#856404;}
    .dd0102-fail {background:#f8d7da; color:#721c24;}
</style>
""", unsafe_allow_html=True)

st.title("\U0001fac0 3D Pacing Lead Curvature Amplitude Analyzer v2")
st.caption("Upload biplane X-ray trace files, configure settings, then click Run.")
st.divider()

# ═══════════════ SIDEBAR ═══════════════
with st.sidebar:
    st.header("⚙️ Settings")
    st.divider()
    st.subheader("📚 DD-0102 Dataset Upload")
    dd0102_file = st.file_uploader(
        "Upload DD-0102 Excel or CSV",
        type=["xlsx", "xls", "csv"],
        key="dd0102_upload_main"
    )
    dd0102_preview = None
    dd0102_patients = []
    dd0102_load_error = None
    if dd0102_file is not None:
        try:
            dd0102_preview = load_dd0102_database(dd0102_file)
            dd0102_patients = sorted([int(p) for p in pd.to_numeric(dd0102_preview["Patient"], errors="coerce").dropna().unique().tolist()])
            st.success("✅ DD-0102 dataset loaded")
            st.caption(f"Rows with Re/Ri values: {int(dd0102_preview.dropna(subset=['Re_mm','Ri_mm']).shape[0])}")
            if dd0102_patients:
                st.caption(f"Patients detected: {dd0102_patients}")
            else:
                st.warning("No patient IDs detected in the uploaded DD-0102 file.")
        except Exception as exc:
            dd0102_load_error = str(exc)
            st.error("❌ Failed to read DD-0102 dataset")
            st.caption(str(exc))
    st.divider()
    st.header("⚙️ Settings")
    input_unit = st.selectbox("Input coordinate units",
        options=["um", "mm", "cm"], index=0,
        format_func=lambda u: {"um": "Micrometers (\u00b5m)", "mm": "Millimeters", "cm": "Centimeters"}[u])

    st.divider()
    st.subheader("\U0001f6a6 Safety Thresholds")
    visone_val = st.number_input("VisONE Stimulation (cm\u207b\u00b9)", value=0.88, step=0.01, format="%.2f")
    resp_val = st.number_input("Respiration (cm\u207b\u00b9)", value=0.91, step=0.01, format="%.2f")
    safety_thresholds = {"VisONE Stimulation": visone_val, "Respiration": resp_val}

    st.divider()
    st.subheader("\u2702\ufe0f Data Trimming")
    st.caption("Ignore noisy electrode tips by trimming wire ends.")
    trim_start = st.slider("Trim start (%)", 0, 50, 0, 1)
    trim_end = st.slider("Trim end (%)", 0, 50, 0, 1)

    st.divider()
    st.subheader("\U0001f9ea Fatigue Estimation")
    material = st.selectbox("Wire material", list(MATERIAL_PROPERTIES.keys()))
    wire_od = st.number_input("Wire OD (mm)", value=2.0, step=0.1, format="%.1f")

    st.divider()
    st.subheader("\U0001f4dd Patient Notes")
    patient_notes = st.text_area("Notes (included in report)", placeholder="e.g. Patient 42, RV lead, 6-month follow-up")

    st.divider()
    st.subheader("\U0001f4e6 Mode")
    mode = st.radio("Analysis Mode", ["Single", "Batch (ZIP)", "Comparison (A vs B)"])



def _detect_candidate_patient(notes_text, uploaded_names, patient_options):
    """Try to auto-match a patient ID from notes or uploaded filenames."""
    text = ' '.join([str(notes_text or '')] + [str(n or '') for n in uploaded_names])
    matches = re.findall(r'(?<!\d)(10\d{2}|\d{4})(?!\d)', text)
    for m in matches:
        try:
            val = int(m)
            if val in patient_options:
                return val, f"Matched from notes/filenames ({val})"
        except Exception:
            pass
    if len(patient_options) == 1:
        return patient_options[0], f"Only one patient available ({patient_options[0]})"
    return None, "No automatic patient match found"


def _style_alignment(df):
    def color_row(row):
        status = row.get('Status', '')
        if status == 'PASS':
            return ['background-color:#d4edda']*len(row)
        if status == 'WARNING':
            return ['background-color:#fff3cd']*len(row)
        if status == 'FAIL':
            return ['background-color:#f8d7da']*len(row)
        return ['']*len(row)
    return df.style.apply(color_row, axis=1)

# ═══════════════ SINGLE MODE ═══════════════
if mode == "Single":
    st.subheader("\U0001f4c2 Upload 4 Files")
    col1, col2 = st.columns(2)
    with col1:
        fi = st.file_uploader("\U0001f4c4 Front Inhale", type=["csv", "xlsx", "xls"], key="fi")
        fe = st.file_uploader("\U0001f4c4 Front Exhale", type=["csv", "xlsx", "xls"], key="fe")
    with col2:
        si = st.file_uploader("\U0001f4c4 Side Inhale", type=["csv", "xlsx", "xls"], key="si")
        se = st.file_uploader("\U0001f4c4 Side Exhale", type=["csv", "xlsx", "xls"], key="se")

    if all([fi, si, fe, se]):
        if st.button("\U0001f680 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."):
                output = run_web_analysis(
                    {"front_inhale": io.BytesIO(fi.getvalue()), "side_inhale": io.BytesIO(si.getvalue()),
                     "front_exhale": io.BytesIO(fe.getvalue()), "side_exhale": io.BytesIO(se.getvalue())},
                    input_unit, float(trim_start), float(trim_end),
                    safety_thresholds, patient_notes, wire_od, material)

            ul = output.get("unit_label", "\u00b5m")

            if not output["table"].empty:
                st.success("\u2705 Analysis complete!")
                st.divider()

                # Metric cards
                st.subheader("\U0001f4ca Results")
                for card in output.get("summary_cards", []):
                    status = card["status"]
                    st.markdown(f"#### \U0001f9ec {card['name']} &nbsp; "
                        f"<span class='status-badge status-{status}'>{status}</span>",
                        unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Peak Ca (cm\u207b\u00b9)", f"{card['max_ca']:.4f}")
                    c2.metric("Mean Ca (cm\u207b\u00b9)", f"{card['mean_ca']:.4f}")
                    c3.metric(f"Inhale Length ({ul})", f"{card['inhale_length']:.1f}")
                    c4.metric(f"Exhale Length ({ul})", f"{card['exhale_length']:.1f}")
                    c5, c6, c7, c8 = st.columns(4)
                    c5.metric(f"Arc at Peak ({ul})", f"{card['arc_at_max']:.1f}")
                    c6.metric(f"Total Arc ({ul})", f"{card['total_arc']:.1f}")
                    c7.metric("Peaks Found", f"{card['n_peaks']}")
                    fat = card.get("fatigue")
                    if fat and "estimated_cycles" in fat:
                        cyc = fat["estimated_cycles"]
                        cyc_str = "\u221e" if cyc == float("inf") else f"{int(cyc):,}"
                        c8.metric("Fatigue Life", cyc_str + " cyc")
                        st.caption(f"\U0001f9ea {fat['fatigue_status']} | Strain: {fat['bending_strain']:.4f} | {material}")
                    st.markdown("")

                # Downloads
                dl1, dl2 = st.columns(2)
                dl1.download_button("\u2b07\ufe0f Download CSV", data=output["table"].to_csv(index=False),
                    file_name="curvature_results.csv", mime="text/csv")
                if output.get("html_report"):
                    dl2.download_button("\U0001f4cb Download HTML Report", data=output["html_report"], file_name="curvature_report.html", mime="text/html")
                st.divider()

                # 3D Plot
                st.subheader("\U0001f9ec 3-D Wire Reconstruction")
                st.caption("Solid = Inhale | Semi-transparent = Exhale | Red = Peak Ca locations")
                if output["plot_3d"]:
                    st.plotly_chart(output["plot_3d"], use_container_width=True)

                # Heatmap
                st.subheader("\U0001f525 Curvature Heatmap")
                st.caption("Wire colored by local curvature magnitude (blue=low, red=high)")
                if output.get("plot_heatmap"):
                    st.plotly_chart(output["plot_heatmap"], use_container_width=True)

                # Morph Animation
                st.subheader("\U0001f3ac Inhale \u2194 Exhale Animation")
                st.caption("Press Play to see the wire morph between respiratory states")
                if output.get("plot_morph") and isinstance(output["plot_morph"], dict):
                    for cname, fig in output["plot_morph"].items():
                        st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # Ca Plots
                st.subheader("\U0001f4c8 Curvature Amplitude vs Arc Length")
                st.caption("Red dashed = safety thresholds | Gray = trimmed regions")
                if output["plot_ca"] and isinstance(output["plot_ca"], dict):
                    for cname, fig in output["plot_ca"].items():
                        st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # DD-0102 stacked wire comparison
                st.subheader("📚 DD-0102 Wire Comparison")
                uploaded_names = [getattr(fi, 'name', ''), getattr(si, 'name', ''), getattr(fe, 'name', ''), getattr(se, 'name', '')]
                if dd0102_file is not None and dd0102_preview is not None and not dd0102_preview.empty:
                    candidate_patient, match_reason = _detect_candidate_patient(patient_notes, uploaded_names, dd0102_patients)
                    if dd0102_patients:
                        default_index = dd0102_patients.index(candidate_patient) if candidate_patient in dd0102_patients else 0
                        st.markdown(f"<div class='dd0102-banner'><strong>Validation active.</strong> {match_reason}</div>", unsafe_allow_html=True)
                        selected_patient = st.selectbox(
                            "Select DD-0102 patient",
                            dd0102_patients,
                            index=default_index,
                            key="dd0102_patient_single"
                        )
                        align_df, summary = compute_dd0102_alignment(output["raw_results"], dd0102_preview, selected_patient)
                        c1, c2 = st.columns(2)
                        c1.metric("Valid DD-0102 rows used", str(summary.get("valid_rows", 0)))
                        c2.metric("Curves mapped", str(summary.get("curves_mapped", 0)))
                        if not align_df.empty:
                            # quick status summary chips
                            status_counts = align_df['Status'].value_counts(dropna=False).to_dict() if 'Status' in align_df.columns else {}
                            chip_html = ''.join([
                                f"<span class='dd0102-chip dd0102-ok'>PASS {status_counts.get('PASS', 0)}</span>",
                                f"<span class='dd0102-chip dd0102-warn'>WARNING {status_counts.get('WARNING', 0)}</span>",
                                f"<span class='dd0102-chip dd0102-fail'>FAIL {status_counts.get('FAIL', 0)}</span>",
                            ])
                            st.markdown(chip_html, unsafe_allow_html=True)
                            fig_stack = generate_stacked_wire_comparison_plot(align_df, selected_patient)
                            if fig_stack is not None:
                                st.plotly_chart(fig_stack, use_container_width=True)
                            st.dataframe(_style_alignment(align_df), use_container_width=True)
                        else:
                            st.info("The uploaded DD-0102 file loaded successfully, but there were no overlapping rows with Re_mm/Ri_mm for the selected patient.")
                    else:
                        st.warning("The DD-0102 file loaded, but no valid patient IDs were detected.")
                elif dd0102_file is not None and dd0102_load_error is not None:
                    st.warning(f"DD-0102 validation is unavailable because the dataset could not be read: {dd0102_load_error}")
                else:
                    st.info("Upload a DD-0102 Excel/CSV file in the sidebar to enable auto-matching and stacked wire comparison without changing the rest of your workflow.")

                st.divider()

                # Calculation Breakdown
                st.subheader("\U0001f9ee Calculation Transparency")
                for cname, steps in output.get("calc_breakdowns", {}).items():
                    with st.expander(f"\U0001f4d0 {cname} \u2014 Step-by-Step"):
                        for s in steps:
                            st.markdown(f"**{s['step']}**")
                            st.write(s.get("desc", ""))
                            if "formula" in s:
                                st.code(s["formula"], language="text")
                            if "detail" in s:
                                st.caption(s["detail"])
                            st.markdown("---")

                # Log
                with st.expander("\U0001f4cb Processing Log"):
                    st.code("\n".join(output["log"]), language="text")
            else:
                st.error("\u274c Analysis failed.")
                with st.expander("Log", expanded=True):
                    st.code("\n".join(output["log"]), language="text")
    else:
        st.info("\U0001f446 Upload all 4 files to begin.")

# ═══════════════ BATCH MODE ═══════════════
elif mode == "Batch (ZIP)":
    st.subheader("\U0001f4e6 Batch Processing")
    st.caption("Upload a .zip with subfolders. Each subfolder needs 4 files with front/side + inhale/exhale in filenames.")
    zip_file = st.file_uploader("Upload ZIP", type=["zip"], key="batch_zip")
    if zip_file and st.button("\U0001f680 Run Batch", type="primary", use_container_width=True):
        with st.spinner("Processing batch..."):
            result = run_batch_from_zip(zip_file.getvalue(), input_unit, float(trim_start), float(trim_end),
                                         safety_thresholds, wire_od, material)
        if not result["master_table"].empty:
            st.success(f"\u2705 {len(result['master_table'])} results!")
            st.dataframe(result["master_table"], use_container_width=True)
            st.download_button("\u2b07\ufe0f Master CSV", data=result["master_table"].to_csv(index=False),
                file_name="batch_results.csv", mime="text/csv")
        else:
            st.error("No results.")
        if result["errors"]:
            with st.expander("\u26a0\ufe0f Errors"):
                for e in result["errors"]:
                    st.warning(e)

# ═══════════════ COMPARISON MODE ═══════════════
elif mode == "Comparison (A vs B)":
    st.subheader("\U0001f50d Side-by-Side Comparison")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Lead A")
        a_fi = st.file_uploader("A: Front Inhale", type=["csv","xlsx","xls"], key="a_fi")
        a_si = st.file_uploader("A: Side Inhale", type=["csv","xlsx","xls"], key="a_si")
        a_fe = st.file_uploader("A: Front Exhale", type=["csv","xlsx","xls"], key="a_fe")
        a_se = st.file_uploader("A: Side Exhale", type=["csv","xlsx","xls"], key="a_se")
    with col_b:
        st.markdown("#### Lead B")
        b_fi = st.file_uploader("B: Front Inhale", type=["csv","xlsx","xls"], key="b_fi")
        b_si = st.file_uploader("B: Side Inhale", type=["csv","xlsx","xls"], key="b_si")
        b_fe = st.file_uploader("B: Front Exhale", type=["csv","xlsx","xls"], key="b_fe")
        b_se = st.file_uploader("B: Side Exhale", type=["csv","xlsx","xls"], key="b_se")

    all_a = all([a_fi, a_si, a_fe, a_se])
    all_b = all([b_fi, b_si, b_fe, b_se])

    if all_a and all_b:
        if st.button("\U0001f680 Compare", type="primary", use_container_width=True):
            with st.spinner("Comparing..."):
                files_a = {"front_inhale": io.BytesIO(a_fi.getvalue()), "side_inhale": io.BytesIO(a_si.getvalue()),
                           "front_exhale": io.BytesIO(a_fe.getvalue()), "side_exhale": io.BytesIO(a_se.getvalue())}
                files_b = {"front_inhale": io.BytesIO(b_fi.getvalue()), "side_inhale": io.BytesIO(b_si.getvalue()),
                           "front_exhale": io.BytesIO(b_fe.getvalue()), "side_exhale": io.BytesIO(b_se.getvalue())}
                comp = run_comparison(files_a, files_b, "Lead A", "Lead B",
                    input_unit, float(trim_start), float(trim_end),
                    safety_thresholds, wire_od, material)

            if not comp["comparison_table"].empty:
                st.success("\u2705 Comparison complete!")
                st.dataframe(comp["comparison_table"], use_container_width=True)
                st.download_button("\u2b07\ufe0f Comparison CSV",
                    data=comp["comparison_table"].to_csv(index=False),
                    file_name="comparison.csv", mime="text/csv")

                st.divider()
                ca, cb = st.columns(2)
                with ca:
                    st.markdown("### Lead A")
                    if comp["lead_a"].get("plot_3d"):
                        st.plotly_chart(comp["lead_a"]["plot_3d"], use_container_width=True)
                with cb:
                    st.markdown("### Lead B")
                    if comp["lead_b"].get("plot_3d"):
                        st.plotly_chart(comp["lead_b"]["plot_3d"], use_container_width=True)
            else:
                st.error("Comparison failed.")
    else:
        st.info("\U0001f446 Upload all 8 files (4 per lead) to compare.")
