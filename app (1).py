"""
Streamlit front-end for 3D Pacing Lead Curvature Analyzer v2.
All features: safety, trim, batch, fatigue, heatmap, animation,
calculation transparency, configurable thresholds, patient notes, comparison.
"""
import streamlit as st
import io
from pacing_lead_curvature_webapp import (
    run_web_analysis, run_batch_from_zip, run_comparison,
    MATERIAL_PROPERTIES, DEFAULT_SAFETY, UNIT_LABELS,
)

st.set_page_config(
    page_title="Pacing Lead Analyzer v2",
    page_icon="\U0001fac0",
    layout="wide",
)

# ═══════════════ GLOBAL CSS ═══════════════
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
    div.block-container { padding-top: 1.5rem; }
    .status-badge {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        font-weight: bold; font-size: 0.95em; color: white;
    }
    .status-PASS    { background: #009988; }
    .status-WARNING { background: #EE7733; }
    .status-FAIL    { background: #FF0000; }
    /* tighten sidebar spacing */
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ═══════════════ HEADER ═══════════════
st.title("\U0001fac0 3D Pacing Lead Curvature Amplitude Analyzer v2")
st.caption("Upload biplane X-ray trace files, configure settings, then click Run.")

# ═══════════════ SIDEBAR ═══════════════
with st.sidebar:
    st.header("\u2699\ufe0f Settings")

    input_unit = st.selectbox(
        "Input coordinate units",
        options=["um", "mm", "cm"],
        index=0,
        format_func=lambda u: {
            "um": "Micrometers (\u00b5m)",
            "mm": "Millimeters",
            "cm": "Centimeters",
        }[u],
    )

    st.divider()
    st.subheader("\U0001f6a6 Safety Thresholds (cm\u207b\u00b9)")
    visone_val = st.number_input(
        "VisONE Stimulation", value=0.88, step=0.01, format="%.2f",
        help="Lower threshold — triggers WARNING when exceeded.",
    )
    resp_val = st.number_input(
        "Respiration", value=0.91, step=0.01, format="%.2f",
        help="Upper threshold — triggers FAIL when exceeded.",
    )
    safety_thresholds = {"VisONE Stimulation": visone_val, "Respiration": resp_val}

    st.divider()
    st.subheader("\u2702\ufe0f Data Trimming")
    st.caption("Ignore noisy electrode tips by trimming wire ends.")
    trim_start = st.slider("Trim start (%)", 0, 50, 0, 1)
    trim_end   = st.slider("Trim end (%)",   0, 50, 0, 1)

    st.divider()
    st.subheader("\U0001f9ea Fatigue Estimation")
    material = st.selectbox("Wire material", list(MATERIAL_PROPERTIES.keys()),
        help="\n".join(f"**{k}**: {v['description']}" for k, v in MATERIAL_PROPERTIES.items()))
    wire_od = st.number_input("Wire OD (mm)", value=2.0, step=0.1, format="%.1f",
        help="Outer diameter used to estimate bending strain.")

    st.divider()
    st.subheader("\U0001f4dd Patient Notes")
    patient_notes = st.text_area(
        "Notes (included in report)",
        placeholder="e.g. Patient 42, RV lead, 6-month follow-up",
    )

    st.divider()
    st.subheader("\U0001f4e6 Analysis Mode")
    mode = st.radio(
        "Mode",
        ["Single", "Batch (ZIP)", "Comparison (A vs B)"],
        label_visibility="collapsed",
    )

st.divider()

# ═══════════════ SINGLE MODE ═══════════════
if mode == "Single":
    st.subheader("\U0001f4c2 Upload 4 Trace Files")
    col1, col2 = st.columns(2)
    with col1:
        fi = st.file_uploader("\U0001f4c4 Front — Inhale", type=["csv", "xlsx", "xls"], key="fi")
        fe = st.file_uploader("\U0001f4c4 Front — Exhale", type=["csv", "xlsx", "xls"], key="fe")
    with col2:
        si = st.file_uploader("\U0001f4c4 Side — Inhale",  type=["csv", "xlsx", "xls"], key="si")
        se = st.file_uploader("\U0001f4c4 Side — Exhale",  type=["csv", "xlsx", "xls"], key="se")

    ready = all([fi, si, fe, se])
    if ready:
        if st.button("\U0001f680 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Reconstructing 3D wire and computing curvature…"):
                output = run_web_analysis(
                    {
                        "front_inhale": io.BytesIO(fi.getvalue()),
                        "side_inhale":  io.BytesIO(si.getvalue()),
                        "front_exhale": io.BytesIO(fe.getvalue()),
                        "side_exhale":  io.BytesIO(se.getvalue()),
                    },
                    input_unit,
                    float(trim_start),
                    float(trim_end),
                    safety_thresholds,
                    patient_notes,
                    wire_od,
                    material,
                )

            ul = output.get("unit_label", "\u00b5m")

            if not output["table"].empty:
                st.success("\u2705 Analysis complete!")
                st.divider()

                # ── Summary cards ──────────────────────────────────────
                st.subheader("\U0001f4ca Results")
                for card in output.get("summary_cards", []):
                    status = card["status"]
                    st.markdown(
                        f"#### \U0001f9ec {card['name']} &nbsp; "
                        f"<span class='status-badge status-{status}'>{status}</span>",
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Peak Ca (cm\u207b\u00b9)",           f"{card['max_ca']:.4f}")
                    c2.metric("Mean Ca (cm\u207b\u00b9)",           f"{card['mean_ca']:.4f}")
                    c3.metric(f"Inhale Length ({ul})",              f"{card['inhale_length']:.1f}")
                    c4.metric(f"Exhale Length ({ul})",              f"{card['exhale_length']:.1f}")
                    c5, c6, c7, c8 = st.columns(4)
                    c5.metric(f"Arc at Peak ({ul})",                f"{card['arc_at_max']:.1f}")
                    c6.metric(f"Total Arc ({ul})",                  f"{card['total_arc']:.1f}")
                    c7.metric("Peaks Found",                        f"{card['n_peaks']}")
                    fat = card.get("fatigue")
                    if fat and "estimated_cycles" in fat:
                        cyc = fat["estimated_cycles"]
                        cyc_str = "\u221e" if cyc == float("inf") else f"{int(cyc):,}"
                        c8.metric("Fatigue Life", cyc_str + " cyc")
                        st.caption(
                            f"\U0001f9ea {fat['fatigue_status']} | "
                            f"Strain: {fat['bending_strain']:.4f} | {material}"
                        )
                    st.markdown("")

                # ── Downloads ──────────────────────────────────────────
                dl1, dl2 = st.columns(2)
                dl1.download_button(
                    "\u2b07\ufe0f Download CSV",
                    data=output["table"].to_csv(index=False),
                    file_name="curvature_results.csv",
                    mime="text/csv",
                )
                if output.get("html_report"):
                    dl2.download_button(
                        "\U0001f4cb Download HTML Report",
                        data=output["html_report"],
                        file_name="curvature_report.html",
                        mime="text/html",
                    )
                st.divider()

                # ── 3D reconstruction ──────────────────────────────────
                st.subheader("\U0001f9ec 3-D Wire Reconstruction")
                st.caption(
                    "**Solid / opaque** = Inhale &nbsp;|&nbsp; "
                    "**Semi-transparent** = Exhale &nbsp;|&nbsp; "
                    "\U0001f534 Red markers = Peak Ca locations"
                )
                if output["plot_3d"]:
                    st.plotly_chart(output["plot_3d"], use_container_width=True)

                # ── Heatmap ────────────────────────────────────────────
                st.subheader("\U0001f525 Curvature Heatmap")
                st.caption("Wire colored by local curvature magnitude (blue = low, red = high)")
                if output.get("plot_heatmap"):
                    st.plotly_chart(output["plot_heatmap"], use_container_width=True)

                # ── Morph animation ────────────────────────────────────
                st.subheader("\U0001f3ac Inhale \u2194 Exhale Animation")
                st.caption("Press \u25b6 Play to see the wire morph between respiratory states")
                if output.get("plot_morph") and isinstance(output["plot_morph"], dict):
                    for cname, fig in output["plot_morph"].items():
                        st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # ── Ca plots ───────────────────────────────────────────
                st.subheader("\U0001f4c8 Curvature Amplitude vs Arc Length")
                st.caption("Red dashed = safety thresholds &nbsp;|&nbsp; Gray = trimmed regions")
                if output["plot_ca"] and isinstance(output["plot_ca"], dict):
                    for cname, fig in output["plot_ca"].items():
                        st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # ── Calculation transparency ───────────────────────────
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

                # ── Processing log ─────────────────────────────────────
                with st.expander("\U0001f4cb Processing Log"):
                    st.code("\n".join(output["log"]), language="text")

            else:
                st.error("\u274c Analysis failed. Check the log below for details.")
                with st.expander("Log", expanded=True):
                    st.code("\n".join(output["log"]), language="text")
    else:
        st.info("\U0001f446 Upload all 4 files to begin.")

# ═══════════════ BATCH MODE ═══════════════
elif mode == "Batch (ZIP)":
    st.subheader("\U0001f4e6 Batch Processing")
    st.caption(
        "Upload a **.zip** containing sub-folders. "
        "Each sub-folder must have 4 files with **front/side** and **inhale/exhale** in the filenames."
    )
    with st.expander("\U0001f4cb Expected ZIP structure"):
        st.code(
            "archive.zip\n"
            "├── patient_01/\n"
            "│   ├── front_inhale.csv\n"
            "│   ├── front_exhale.csv\n"
            "│   ├── side_inhale.csv\n"
            "│   └── side_exhale.csv\n"
            "└── patient_02/\n"
            "    └── ...",
            language="text",
        )
    zip_file = st.file_uploader("Upload ZIP", type=["zip"], key="batch_zip")
    if zip_file:
        if st.button("\U0001f680 Run Batch", type="primary", use_container_width=True):
            with st.spinner("Processing batch…"):
                result = run_batch_from_zip(
                    zip_file.getvalue(),
                    input_unit,
                    float(trim_start),
                    float(trim_end),
                    safety_thresholds,
                    wire_od,
                    material,
                )
            if not result["master_table"].empty:
                n = len(result["master_table"])
                st.success(f"\u2705 {n} result{'s' if n != 1 else ''} processed!")
                st.dataframe(result["master_table"], use_container_width=True)
                st.download_button(
                    "\u2b07\ufe0f Download Master CSV",
                    data=result["master_table"].to_csv(index=False),
                    file_name="batch_results.csv",
                    mime="text/csv",
                )
            else:
                st.error("\u274c No valid results. Check folder structure and filenames.")
            if result["errors"]:
                with st.expander(f"\u26a0\ufe0f {len(result['errors'])} error(s)"):
                    for e in result["errors"]:
                        st.warning(e)

# ═══════════════ COMPARISON MODE ═══════════════
elif mode == "Comparison (A vs B)":
    st.subheader("\U0001f50d Side-by-Side Lead Comparison")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### \U0001f535 Lead A")
        a_fi = st.file_uploader("A: Front — Inhale", type=["csv", "xlsx", "xls"], key="a_fi")
        a_si = st.file_uploader("A: Side — Inhale",  type=["csv", "xlsx", "xls"], key="a_si")
        a_fe = st.file_uploader("A: Front — Exhale", type=["csv", "xlsx", "xls"], key="a_fe")
        a_se = st.file_uploader("A: Side — Exhale",  type=["csv", "xlsx", "xls"], key="a_se")
    with col_b:
        st.markdown("#### \U0001f7e0 Lead B")
        b_fi = st.file_uploader("B: Front — Inhale", type=["csv", "xlsx", "xls"], key="b_fi")
        b_si = st.file_uploader("B: Side — Inhale",  type=["csv", "xlsx", "xls"], key="b_si")
        b_fe = st.file_uploader("B: Front — Exhale", type=["csv", "xlsx", "xls"], key="b_fe")
        b_se = st.file_uploader("B: Side — Exhale",  type=["csv", "xlsx", "xls"], key="b_se")

    all_a = all([a_fi, a_si, a_fe, a_se])
    all_b = all([b_fi, b_si, b_fe, b_se])

    if all_a and all_b:
        if st.button("\U0001f680 Compare Leads", type="primary", use_container_width=True):
            with st.spinner("Running comparison…"):
                files_a = {
                    "front_inhale": io.BytesIO(a_fi.getvalue()),
                    "side_inhale":  io.BytesIO(a_si.getvalue()),
                    "front_exhale": io.BytesIO(a_fe.getvalue()),
                    "side_exhale":  io.BytesIO(a_se.getvalue()),
                }
                files_b = {
                    "front_inhale": io.BytesIO(b_fi.getvalue()),
                    "side_inhale":  io.BytesIO(b_si.getvalue()),
                    "front_exhale": io.BytesIO(b_fe.getvalue()),
                    "side_exhale":  io.BytesIO(b_se.getvalue()),
                }
                comp = run_comparison(
                    files_a, files_b,
                    "Lead A", "Lead B",
                    input_unit,
                    float(trim_start),
                    float(trim_end),
                    safety_thresholds,
                    wire_od,
                    material,
                )

            if not comp["comparison_table"].empty:
                st.success("\u2705 Comparison complete!")
                st.dataframe(comp["comparison_table"], use_container_width=True)
                st.download_button(
                    "\u2b07\ufe0f Download Comparison CSV",
                    data=comp["comparison_table"].to_csv(index=False),
                    file_name="comparison.csv",
                    mime="text/csv",
                )
                st.divider()
                ca, cb = st.columns(2)
                with ca:
                    st.markdown("### \U0001f535 Lead A")
                    if comp["lead_a"].get("plot_3d"):
                        st.plotly_chart(comp["lead_a"]["plot_3d"], use_container_width=True)
                    if comp["lead_a"].get("plot_ca"):
                        for fig in comp["lead_a"]["plot_ca"].values():
                            st.plotly_chart(fig, use_container_width=True)
                with cb:
                    st.markdown("### \U0001f7e0 Lead B")
                    if comp["lead_b"].get("plot_3d"):
                        st.plotly_chart(comp["lead_b"]["plot_3d"], use_container_width=True)
                    if comp["lead_b"].get("plot_ca"):
                        for fig in comp["lead_b"]["plot_ca"].values():
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("\u274c Comparison failed. Check that all files are valid.")
    else:
        missing = []
        if not all_a:
            missing.append("Lead A")
        if not all_b:
            missing.append("Lead B")
        st.info(f"\U0001f446 Upload all 4 files for: {', '.join(missing)}.")
