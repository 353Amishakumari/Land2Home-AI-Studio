"""
Land2Home — Commercial PropTech AI Architecture Application
=============================================================

Pages:
  1. 🏠 Dashboard
  2. 📐 Land Measurement & Computer Vision Boundary Detection
  3. 🏡 House Requirements, Vastu & Budget Tier
  4. 📊 Design Comparison & Multi-Criteria Scoring
  5. 📋 2D Floor Plan & AutoCAD (.DXF) Export
  6. 🧊 3D Interactive Visualization
  7. 📄 Commercial PDF Feasibility & BOQ Dossier
"""

from __future__ import annotations
import io
import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

# ============================================================
# Page config (must be first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="Land2Home Architecture Studio",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Local imports
# ============================================================
from src.measurement.geometry import rectangular_plot, square_plot, setback_dimensions
from src.measurement.area_calculation import calculate_land_area, calculate_with_setback
from src.requirement_parser.parser import parse_requirements, validate_feasibility
from src.house_planner.floorplan_generator import generate_all_designs
from src.visualization.render_2d import create_2d_floorplan
from src.visualization.render_3d import create_3d_view
from src.reporting.pdf_generator import generate_pdf_report
from src.land_detection.preprocessing import load_and_preprocess_image
from src.land_detection.segmentation import detect_plot_boundary
from src.measurement.calibration import compute_calibrated_plot
from src.export.dxf_exporter import export_layout_to_dxf
from src.evaluation.vastu import analyze_vastu_compliance
from src.cost_estimation.estimator import estimate_construction_cost, TIER_RATES

# ============================================================
# Session-state initialisation
# ============================================================
_DEFAULTS = {
    "plot_width":          30.0,
    "plot_length":         40.0,
    "setback":             0.0,
    "plot_type":           "Rectangular",
    "plot_facing":         "North",
    "cost_tier":           "Standard",
    "client_name":         "",
    "prepared_by":         "Land2Home AI Architecture Studio",
    "raw_plot_image":      None,
    "custom_points":       [],
    "detected_plot":       None,
    "calibrated_plot":     None,
    "measurements":        None,   # dict from calculate_land_area
    "requirements":        None,   # dict from parse_requirements
    "designs":             None,   # list[dict] — 3 designs
    "selected_design_id":  None,   # 1 | 2 | 3
    "_last_plot_w":        None,
    "_last_plot_l":        None,
    "_last_req_hash":      None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _invalidate_designs():
    """Call whenever plot dims or requirements change."""
    st.session_state.designs            = None
    st.session_state.selected_design_id = None


def _selected_design() -> dict | None:
    designs = st.session_state.designs
    sid     = st.session_state.selected_design_id
    if not designs or sid is None:
        return None
    for d in designs:
        if d["design_id"] == sid:
            return d
    return designs[0] if designs else None


# ============================================================
# Sidebar navigation
# ============================================================
st.sidebar.image("https://via.placeholder.com/200x60/1A3A5C/FFFFFF?text=Land2Home",
                 use_container_width=True)
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard",
     "📐 Land Measurement",
     "🏡 House Requirements",
     "📊 Design Comparison",
     "📋 2D Floor Plan",
     "🧊 3D Visualization",
     "📄 PDF Report"],
    label_visibility="collapsed",
)

# Status indicator in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Project Status**")
st.sidebar.markdown("✅ Measurements" if st.session_state.measurements else "⬜ Measurements")
st.sidebar.markdown("✅ Requirements" if st.session_state.requirements else "⬜ Requirements")
if st.session_state.designs:
    st.sidebar.markdown("✅ Designs (3 Generated)")
else:
    st.sidebar.markdown("⬜ Designs")
if st.session_state.selected_design_id:
    st.sidebar.markdown(f"✅ Selected: Design {st.session_state.selected_design_id}")
else:
    st.sidebar.markdown("⬜ Design selected")

st.sidebar.markdown("---")
st.sidebar.caption("Land2Home AI Architecture Studio\nCommercial PropTech Planning & BOQ Engine")


# ============================================================
# PAGE 1 — Dashboard
# ============================================================
if page == "🏠 Dashboard":
    st.title("🏠 Land2Home Architecture Studio")
    st.caption("AI-Powered Land Analysis, Commercial House Planning, Vastu Auditing & 3D Visualization")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Plot Width",   f"{st.session_state.plot_width:.0f} ft")
    col2.metric("Plot Length",  f"{st.session_state.plot_length:.0f} ft")
    col3.metric("Measurements", "✅ Ready" if st.session_state.measurements else "⬜ Pending")
    col4.metric("Designs",      "✅ 3 generated" if st.session_state.designs else "⬜ Pending")

    st.markdown("---")
    st.subheader("Commercial Workflow")
    steps = [
        ("1", "📐 Land Measurement & Computer Vision", "Enter plot dimensions or upload a site photo/sketch to auto-detect boundary."),
        ("2", "🏡 House Requirements & Vastu", "Select BHK, floors, Vastu road facing (N/E/S/W), and construction quality tier."),
        ("3", "📊 Design Comparison & Scoring", "Generate 3 distinct architectural layouts evaluated by geometry, Vastu, and BOQ cost."),
        ("4", "📋 2D Floor Plan & DXF Export", "Review architectural concept drawings and export industry-standard AutoCAD (.DXF) files."),
        ("5", "🧊 3D Visualization", "Explore the interactive 3D model with custom wall heights, orbit, and zoom."),
        ("6", "📄 Commercial PDF Dossier", "Generate a publication-grade, white-labeled client feasibility report with BOQ and visual proof."),
    ]
    for step_num, step_title, step_desc in steps:
        with st.container():
            c1, c2 = st.columns([0.08, 0.92])
            c1.markdown(f"**{step_num}**")
            c2.markdown(f"**{step_title}** — {step_desc}")

    st.markdown("---")
    st.info(
        "🏗️ **Commercial Space Planning Engine:** Land2Home generates three architecturally distinct concept layouts: "
        "**Central Hall**, **Corridor Plan**, and **Open Living+Dining**. "
        "Features non-overlapping geometric partitions, Vastu energy alignment, and full bill of quantities (BOQ)."
    )


# ============================================================
# PAGE 2 — Land Measurement
# ============================================================
elif page == "📐 Land Measurement":
    st.title("📐 Land Measurement & Plot Calibration")
    st.caption("Enter plot dimensions manually or upload a site image/sketch for automated computer vision detection.")

    tab_rect, tab_sq, tab_poly, tab_img = st.tabs(
        ["Rectangular Plot", "Square Plot", "Custom Polygon", "📸 Land Image / Sketch Detection"])

    # ---- Rectangular ----
    with tab_rect:
        col1, col2 = st.columns(2)
        with col1:
            pw = st.number_input("Plot width (ft)", min_value=5.0,
                                 value=float(st.session_state.plot_width), step=1.0,
                                 help="East-West dimension")
        with col2:
            pl = st.number_input("Plot length (ft)", min_value=5.0,
                                 value=float(st.session_state.plot_length), step=1.0,
                                 help="South-North dimension (road-to-rear)")

        with st.expander("Optional: Setback Configuration"):
            sc1, sc2, sc3, sc4 = st.columns(4)
            sb_front = sc1.number_input("Front setback (ft)", 0.0, 20.0, 0.0, 0.5)
            sb_rear  = sc2.number_input("Rear setback (ft)",  0.0, 20.0, 0.0, 0.5)
            sb_left  = sc3.number_input("Left setback (ft)",  0.0, 10.0, 0.0, 0.5)
            sb_right = sc4.number_input("Right setback (ft)", 0.0, 10.0, 0.0, 0.5)

        if st.button("Calculate Land Area", type="primary", key="btn_rect"):
            try:
                points = rectangular_plot(pl, pw)
                if any(sb > 0 for sb in [sb_front, sb_rear, sb_left, sb_right]):
                    meas = calculate_with_setback(points, pw, pl,
                                                  sb_front, sb_rear, sb_left, sb_right)
                else:
                    meas = calculate_land_area(points)

                if (st.session_state.plot_width != pw or
                        st.session_state.plot_length != pl):
                    _invalidate_designs()

                st.session_state.measurements  = meas
                st.session_state.plot_width    = pw
                st.session_state.plot_length   = pl
                st.session_state.setback       = max(sb_front, sb_rear, sb_left, sb_right)
                st.session_state.plot_type     = "Rectangular"
                st.session_state._last_plot_w  = pw
                st.session_state._last_plot_l  = pl
                st.success("✅ Land measurements calculated successfully.")
            except ValueError as exc:
                st.error(str(exc))

    # ---- Square ----
    with tab_sq:
        side = st.number_input("Side length (ft)", min_value=5.0,
                               value=float(st.session_state.plot_width), step=1.0)
        if st.button("Calculate Square Plot", type="primary", key="btn_sq"):
            try:
                points = square_plot(side)
                meas   = calculate_land_area(points)
                if st.session_state.plot_width != side:
                    _invalidate_designs()
                st.session_state.measurements = meas
                st.session_state.plot_width   = side
                st.session_state.plot_length  = side
                st.session_state.plot_type    = "Square"
                st.success("✅ Square plot measurements calculated.")
            except ValueError as exc:
                st.error(str(exc))

    # ---- Custom Polygon ----
    with tab_poly:
        st.info("Enter polygon corner coordinates (X, Y in feet). Minimum 3 corners.")
        num_pts = st.number_input("Number of corners", min_value=3, max_value=12, value=4)
        pts = []
        pt_cols = st.columns(2)
        for i in range(int(num_pts)):
            with pt_cols[i % 2]:
                x_ = st.number_input(f"Corner {i+1} — X (ft)", key=f"px{i}", value=0.0)
                y_ = st.number_input(f"Corner {i+1} — Y (ft)", key=f"py{i}", value=0.0)
                pts.append((x_, y_))

        if st.button("Calculate Polygon Area", type="primary", key="btn_poly"):
            try:
                from src.measurement.geometry import polygon_measurements
                pm   = polygon_measurements(pts)
                meas = {
                    "area_sqft":  pm["area_sqft"],
                    "area_sqm":   pm["area_sqm"],
                    "perimeter_ft": pm["perimeter_ft"],
                    "area_cents": round(pm["area_sqft"] / 435.6, 3),
                    "area_str":   f"{pm['area_sqft']:,.1f} sq.ft  ({pm['area_sqm']:,.2f} sq.m)",
                    "perimeter_str": f"{pm['perimeter_ft']:,.1f} ft",
                    "boundary_lengths_ft": pm["boundary_lengths_ft"],
                }
                from shapely.geometry import Polygon
                poly = Polygon(pts)
                minx, miny, maxx, maxy = poly.bounds
                _invalidate_designs()
                st.session_state.measurements  = meas
                st.session_state.plot_width    = round(maxx - minx, 2)
                st.session_state.plot_length   = round(maxy - miny, 2)
                st.session_state.custom_points = pts
                st.session_state.plot_type     = "Custom Polygon"
                st.session_state._last_plot_w  = st.session_state.plot_width
                st.session_state._last_plot_l  = st.session_state.plot_length
                st.success("✅ Custom polygon area calculated.")
            except Exception as exc:
                st.error(f"Polygon error: {exc}")

    # ---- 📸 Land Image & Sketch Detection ----
    with tab_img:
        st.markdown("#### 📸 Automated Land Boundary & Sketch Detection")
        st.write(
            "Upload an aerial site photo, satellite map capture, or a hand-drawn / CAD plot sketch. "
            "OpenCV will detect the plot boundary, rectify perspective, and compute real-world dimensions using interactive scale calibration."
        )

        col_up1, col_up2 = st.columns([0.6, 0.4])
        with col_up1:
            uploaded_file = st.file_uploader(
                "Upload plot image or hand-drawn sketch",
                type=["png", "jpg", "jpeg"],
                key="land_img_uploader",
                help="Supports site photos, satellite screenshots, or paper drawings."
            )
        with col_up2:
            detect_mode = st.selectbox(
                "Detection Preset",
                ["auto", "sketch", "satellite", "photo"],
                format_func=lambda x: {
                    "auto": "Auto-Detect (Adaptive + Edge)",
                    "sketch": "Hand-Drawn Sketch / Blueprint",
                    "satellite": "Satellite Map Screenshot",
                    "photo": "Site Land Photograph"
                }[x],
                help="Fine-tunes OpenCV thresholding and morphological filtering."
            )
            blur_val = st.slider("Denoise filter strength", min_value=3, max_value=9, value=5, step=2)

        if uploaded_file is not None:
            try:
                img_rgb, img_gray = load_and_preprocess_image(uploaded_file)
                st.session_state["raw_plot_image"] = img_rgb
            except Exception as e:
                st.error(f"Error loading image: {e}")
                img_rgb = None

            if img_rgb is not None:
                btn_detect = st.button("🔍 Detect Plot Boundary & Corners", type="primary", key="btn_run_detect")
                if btn_detect:
                    with st.spinner("Analyzing contours, detecting corners & computing homography..."):
                        det_res = detect_plot_boundary(img_rgb, mode=detect_mode, blur_kernel=blur_val)
                        st.session_state["detected_plot"] = det_res
                        if det_res["success"]:
                            st.success(f"✅ {det_res['message']} (Found {len(det_res['corners'])} corners)")
                        else:
                            st.warning(det_res["message"])

                if st.session_state.get("detected_plot"):
                    det = st.session_state["detected_plot"]

                    disp_col1, disp_col2 = st.columns(2)
                    with disp_col1:
                        st.markdown("**Detected Boundary Overlay**")
                        st.image(det["annotated_image"], use_container_width=True, caption="Boundary overlay with corner pins & side pixel lengths")
                    with disp_col2:
                        st.markdown("**Perspective Rectification (Top-Down View)**")
                        if det.get("warped_image") is not None:
                            st.image(det["warped_image"], use_container_width=True, caption=f"Rectified Orthogonal View (Aspect: {det['aspect_ratio']:.2f})")
                        else:
                            st.info("Perspective rectification available for 4-corner quadrilateral plots.")

                    st.markdown("---")
                    st.markdown("#### 📐 Interactive Scale & Calibration Tool")
                    st.caption("Convert detected pixel coordinates into real-world feet.")

                    cal_method = st.radio(
                        "Calibration Method:",
                        ["known_side", "known_area"],
                        format_func=lambda x: "Known Side Length (e.g. Road Frontage)" if x == "known_side" else "Total Known Plot Area (from deed survey)",
                        horizontal=True
                    )

                    c_c1, c_c2 = st.columns(2)
                    if cal_method == "known_side":
                        with c_c1:
                            side_opts = [f"Side {i+1} ({dist:.0f} px)" for i, dist in enumerate(det["side_lengths_px"])]
                            side_idx = st.selectbox("Select reference boundary side:", range(len(side_opts)), format_func=lambda i: side_opts[i])
                        with c_c2:
                            ref_ft = st.number_input("Real length of selected side (ft):", min_value=5.0, max_value=500.0, value=30.0, step=1.0)
                        cal_btn = st.button("Apply Scale Calibration", key="btn_apply_calib_side")
                        if cal_btn:
                            try:
                                cal_res = compute_calibrated_plot(det, calibration_method="side", known_side_index=side_idx, known_side_ft=ref_ft)
                                st.session_state["calibrated_plot"] = cal_res
                                st.success(f"✅ {cal_res['calibration_summary']}")
                            except Exception as ce:
                                st.error(f"Calibration failed: {ce}")
                    else:
                        with c_c1:
                            ref_area = st.number_input("Known total plot area (sq.ft):", min_value=100.0, max_value=50000.0, value=1200.0, step=50.0)
                        with c_c2:
                            st.caption(f"Equivalent: {ref_area * 0.09290304:.2f} sq.m | {ref_area / 435.6:.2f} cents")
                        cal_btn = st.button("Apply Scale Calibration", key="btn_apply_calib_area")
                        if cal_btn:
                            try:
                                cal_res = compute_calibrated_plot(det, calibration_method="area", known_area_sqft=ref_area)
                                st.session_state["calibrated_plot"] = cal_res
                                st.success(f"✅ {cal_res['calibration_summary']}")
                            except Exception as ce:
                                st.error(f"Calibration failed: {ce}")

                    if st.session_state.get("calibrated_plot"):
                        cal = st.session_state["calibrated_plot"]
                        st.markdown("##### 📏 Calibrated Real-World Dimensions")
                        cr1, cr2, cr3, cr4 = st.columns(4)
                        cr1.metric("Width (ft)", f"{cal['plot_width']:.1f} ft")
                        cr2.metric("Length (ft)", f"{cal['plot_length']:.1f} ft")
                        cr3.metric("Area (sq.ft)", f"{cal['area_sqft']:,.0f}")
                        cr4.metric("Perimeter (ft)", f"{cal['perimeter_ft']:.1f} ft")

                        st.write(f"**Individual Boundary Lengths (ft):** {', '.join([f'Side {i+1}: {l:.1f} ft' for i, l in enumerate(cal['side_lengths_ft'])])}")

                        if st.button("🚀 Transfer Detected Plot to House Planner", type="primary", key="btn_use_detected_plot"):
                            pw_cal = float(cal["plot_width"])
                            pl_cal = float(cal["plot_length"])
                            _invalidate_designs()
                            st.session_state.plot_width = pw_cal
                            st.session_state.plot_length = pl_cal
                            st.session_state.plot_type = f"Image Detected ({pw_cal:.0f}×{pl_cal:.0f} ft)"
                            st.session_state.measurements = calculate_land_area(rectangular_plot(pl_cal, pw_cal))
                            st.session_state._last_plot_w = pw_cal
                            st.session_state._last_plot_l = pl_cal
                            st.success(f"🎉 Plot dimensions {pw_cal:.1f} × {pl_cal:.1f} ft successfully transferred to House Planner! Navigate to 🏡 House Requirements.")

    # ---- Results ----
    if st.session_state.measurements:
        m = st.session_state.measurements
        st.markdown("---")
        st.subheader("📊 Measurement Results")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Area (sq.ft)", f"{m.get('area_sqft', 0):,.0f}")
        mc2.metric("Area (sq.m)",  f"{m.get('area_sqm',  0):,.2f}")
        mc3.metric("Perimeter",    f"{m.get('perimeter_ft', 0):,.1f} ft")
        mc4.metric("Area (Cents)", f"{m.get('area_cents', 0):.3f}")

        W = st.session_state.plot_width
        L = st.session_state.plot_length
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_facecolor("#F8F9FA")
        from matplotlib.patches import Rectangle as MRect
        ax.add_patch(MRect((0, 0), W, L, fill=False, edgecolor="#1A3A5C", linewidth=2.5))
        ax.text(W/2, -1.5, f"← {W:.0f} ft →", ha="center", fontsize=9, color="#444")
        ax.text(-1.5, L/2, f"← {L:.0f} ft →", ha="center", fontsize=9, color="#444", rotation=90)
        ax.text(W/2, L/2, f"{W:.0f}×{L:.0f} ft\n{m.get('area_sqft',0):,.0f} sq.ft",
                ha="center", va="center", fontsize=10, fontweight="bold", color="#1A3A5C")
        ax.set_xlim(-3, W+3); ax.set_ylim(-3, L+3)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("Plot Boundary", fontsize=11, fontweight="bold")
        st.pyplot(fig); plt.close(fig)


# ============================================================
# PAGE 3 — House Requirements
# ============================================================
elif page == "🏡 House Requirements":
    st.title("🏡 House Requirements & Vastu Configuration")
    st.caption("Configure house type, floors, Vastu orientation, and construction quality tier.")

    if not st.session_state.measurements:
        st.warning("⬅️ Please complete Land Measurement first.")
        st.stop()

    with st.form("requirements_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            house_type = st.selectbox("House Type", ["1BHK", "2BHK", "3BHK", "4BHK"], index=1)
            floors     = st.selectbox("Number of Floors", ["Ground Floor", "G+1", "G+2"], index=0)
        with col2:
            plot_facing = st.selectbox(
                "Plot Road Facing (Vastu Orientation)",
                ["North", "East", "South", "West"],
                index=["North", "East", "South", "West"].index(st.session_state.get("plot_facing", "North")),
                help="Front road compass direction for Vastu Shastra energy alignment."
            )
            bathrooms  = st.number_input("Bathrooms (0 = auto)", 0, 6, 0,
                                         help="Leave 0 to auto-derive from BHK type")
        with col3:
            cost_tier = st.selectbox(
                "Construction Quality Tier (BOQ)",
                ["Basic", "Standard", "Premium"],
                index=["Basic", "Standard", "Premium"].index(st.session_state.get("cost_tier", "Standard")),
                format_func=lambda x: f"{x} (Rs. {TIER_RATES[x]:,.0f}/sq.ft)"
            )

        st.markdown("**Optional Spaces & Amenities**")
        oc1, oc2, oc3 = st.columns(3)
        with oc1:
            parking     = st.checkbox("Parking Slot", value=True)
            garden      = st.checkbox("Garden / Landscaping", value=True)
            staircase   = st.checkbox("Internal Staircase", value=floors != "Ground Floor")
        with oc2:
            dining_room = st.checkbox("Dining Room", value=True)
            balcony     = st.checkbox("Balcony Area", value=False)
            pooja_room  = st.checkbox("Pooja / Prayer Room", value=False)
        with oc3:
            store_room  = st.checkbox("Store Room", value=False)
            utility     = st.checkbox("Utility / Wash Area", value=False)

        submitted = st.form_submit_button("Save Requirements & Validate", type="primary")

    if submitted:
        reqs = parse_requirements(
            house_type=house_type, floors=floors,
            parking=parking, staircase=staircase, garden=garden,
            dining_room=dining_room, balcony=balcony, store_room=store_room,
            pooja_room=pooja_room, utility=utility, bathrooms=bathrooms,
        )
        reqs["plot_facing"] = plot_facing
        reqs["cost_tier"]   = cost_tier
        st.session_state.plot_facing = plot_facing
        st.session_state.cost_tier   = cost_tier

        feas = validate_feasibility(
            reqs, st.session_state.plot_width, st.session_state.plot_length,
            st.session_state.setback
        )
        if feas["feasible"]:
            st.success(f"✅ {feas['reason']}  |  Buildable area ≈ {feas['buildable_area_sqft']:,.0f} sq.ft")
        else:
            st.error(f"⚠️ {feas['reason']}")
            if feas["suggestion"]:
                st.info(f"💡 Suggestion: {feas['suggestion']}")

        req_hash = str(sorted(reqs.items()))
        if req_hash != st.session_state._last_req_hash:
            _invalidate_designs()
            st.session_state._last_req_hash = req_hash

        st.session_state.requirements = reqs
        st.success("Requirements saved. Go to **📊 Design Comparison** to generate layouts.")


# ============================================================
# PAGE 4 — Design Comparison
# ============================================================
elif page == "📊 Design Comparison":
    st.title("📊 Design Comparison & Commercial Feasibility")
    st.caption("Generate 3 distinct layouts and evaluate them by spatial efficiency, Vastu score, and BOQ budget.")

    if not st.session_state.measurements:
        st.warning("⬅️ Complete Land Measurement first."); st.stop()
    if not st.session_state.requirements:
        st.warning("⬅️ Complete House Requirements first."); st.stop()

    if st.button("🔄 Generate All 3 Designs", type="primary"):
        with st.spinner("Generating architectural layouts, validating geometry & computing Vastu/BOQ…"):
            try:
                designs = generate_all_designs(
                    st.session_state.plot_width,
                    st.session_state.plot_length,
                    st.session_state.requirements,
                )
                st.session_state.designs = designs
                st.session_state.selected_design_id = None
                st.success("✅ 3 architectural designs generated successfully.")
            except ValueError as exc:
                st.error(f"❌ Layout generation failed: {exc}")
                st.stop()

    if st.session_state.designs:
        designs = st.session_state.designs

        st.markdown("### Commercial Design Overview")
        tbl_data = []
        for d in designs:
            sc = d["score"]
            val = d["validation"]
            built_a = sum(r["width"] * r["length"] for r in d["rooms"] if r.get("kind") != "amenity")
            c_est = estimate_construction_cost(built_a, tier=st.session_state.get("cost_tier", "Standard"))
            v_audit = analyze_vastu_compliance(
                d["rooms"], st.session_state.plot_width, st.session_state.plot_length,
                plot_facing=st.session_state.get("plot_facing", "North"), features=d["features"]
            )
            tbl_data.append({
                "Layout": d["design_name"],
                "Built Area": f"{built_a:,.0f} sq.ft",
                "Design Score": f"{sc['total']:.1f}/100 ({sc['grade']})",
                "Vastu Score": f"{v_audit['score']:.0f}/100 ({v_audit['grade']})",
                "Est. Budget": f"Rs. {c_est['total_cost_lakhs']:.2f} Lakhs",
                "Geometry ✓": "✅ OK" if val.get("valid") else "❌ Overlap",
                "Circulation ✓": "✅ OK" if val.get("connected", True) else "❌ Notice",
            })
        st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)

        # Previews
        st.markdown("### Architectural Floor Plan Previews")
        prev_cols = st.columns(3)
        for col, design in zip(prev_cols, designs):
            with col:
                st.markdown(f"**{design['design_name'].split('—')[1].strip()}**")
                try:
                    fig_prev = create_2d_floorplan(
                        design["rooms"], st.session_state.plot_width,
                        st.session_state.plot_length, design["features"],
                        design["design_name"],
                    )
                    st.pyplot(fig_prev)
                    plt.close(fig_prev)
                except Exception as exc:
                    st.error(f"Preview error: {exc}")

                sc = design["score"]
                built_a = sum(r["width"] * r["length"] for r in design["rooms"] if r.get("kind") != "amenity")
                c_est = estimate_construction_cost(built_a, tier=st.session_state.get("cost_tier", "Standard"))
                v_audit = analyze_vastu_compliance(
                    design["rooms"], st.session_state.plot_width, st.session_state.plot_length,
                    plot_facing=st.session_state.get("plot_facing", "North"), features=design["features"]
                )

                mc1, mc2 = st.columns(2)
                mc1.metric("Arch Score", f"{sc['total']:.1f}", f"Grade {sc['grade']}")
                mc2.metric("Vastu Score", f"{v_audit['score']:.0f}/100", f"{v_audit['grade']}")
                st.metric("Est. Cost", f"Rs. {c_est['total_cost_lakhs']:.2f} L", f"{st.session_state.get('cost_tier', 'Standard')} Tier")

        # Selection
        st.markdown("---")
        st.subheader("Select Preferred Design for Full Export")
        design_options = {d["design_name"]: d["design_id"] for d in designs}
        current_sel = None
        if st.session_state.selected_design_id:
            for d in designs:
                if d["design_id"] == st.session_state.selected_design_id:
                    current_sel = d["design_name"]
                    break

        sel_name = st.radio("Choose design:", list(design_options.keys()),
                            index=0 if current_sel is None else list(design_options.keys()).index(current_sel) if current_sel in design_options else 0)

        if st.button("✅ Confirm Selection", type="primary"):
            st.session_state.selected_design_id = design_options[sel_name]
            st.success(f"✅ **{sel_name}** selected! Navigate to **📋 2D Floor Plan**, **🧊 3D Visualization**, or **📄 PDF Report**.")


# ============================================================
# PAGE 5 — 2D Floor Plan & DXF Export
# ============================================================
elif page == "📋 2D Floor Plan":
    st.title("📋 2D Concept Floor Plan & AutoCAD Export")
    st.caption("Architectural layout drawing, Vastu energy audit, and construction bill of quantities.")

    if not st.session_state.measurements:
        st.warning("⬅️ Complete Land Measurement first."); st.stop()
    if not st.session_state.requirements:
        st.warning("⬅️ Complete House Requirements first."); st.stop()
    if not st.session_state.designs:
        st.warning("⬅️ Generate designs in **📊 Design Comparison** first."); st.stop()

    design = _selected_design()
    if design is None:
        st.info("ℹ️ No design selected yet — showing Design A by default.")
        design = st.session_state.designs[0]

    st.info(f"🎨 Selected: **{design['design_name']}**")

    with st.spinner("Rendering 2D floor plan…"):
        try:
            fig = create_2d_floorplan(
                design["rooms"],
                st.session_state.plot_width,
                st.session_state.plot_length,
                design["features"],
                design["design_name"],
            )
            st.pyplot(fig, use_container_width=True)

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                st.download_button(
                    "⬇️ Download 2D Floor Plan (PNG)",
                    data=buf, file_name=f"{design['design_name'].replace(' ', '_')}.png",
                    mime="image/png",
                )

            with d_col2:
                # AutoCAD DXF Export
                dxf_bytes = export_layout_to_dxf(
                    design["rooms"],
                    st.session_state.plot_width,
                    st.session_state.plot_length,
                    features=design["features"],
                    design_name=design["design_name"],
                    client_name=st.session_state.get("client_name", ""),
                    prepared_by=st.session_state.get("prepared_by", "Land2Home AI Architecture Studio")
                )
                st.download_button(
                    "📐 Download AutoCAD (.DXF)",
                    data=dxf_bytes,
                    file_name=f"{design['design_name'].replace(' ', '_')}.dxf",
                    mime="application/dxf",
                    help="Exports layered CAD drawings compatible with AutoCAD, FreeCAD, and LibreCAD."
                )
        except Exception as exc:
            st.error(f"2D rendering error: {exc}")

    # Vastu Shastra Expander
    with st.expander("☸️ Vastu Shastra Compliance Audit", expanded=True):
        vastu = analyze_vastu_compliance(
            design["rooms"],
            st.session_state.plot_width,
            st.session_state.plot_length,
            plot_facing=st.session_state.get("plot_facing", "North"),
            features=design["features"]
        )
        vc1, vc2, vc3 = st.columns(3)
        vc1.metric("Plot Facing", f"{vastu['plot_facing']} Facing")
        vc2.metric("Vastu Score", f"{vastu['score']:.1f} / 100")
        vc3.metric("Rating", vastu["grade"])

        v_df = []
        for itm in vastu["audit_items"]:
            v_df.append({
                "Room": itm["room"],
                "Placed Zone": itm["zone"],
                "Ideal Zone": itm["ideal_zone"],
                "Compliance": itm["status"],
                "Architectural Tip": itm["tip"],
            })
        st.dataframe(pd.DataFrame(v_df), use_container_width=True, hide_index=True)

        if vastu.get("recommendations"):
            st.markdown("**Key Harmonization Tips:**")
            for r in vastu["recommendations"]:
                st.caption(f"• {r}")

    # Construction Cost & BOQ Expander
    built_a = sum(r["width"] * r["length"] for r in design["rooms"] if r.get("kind") != "amenity")
    with st.expander("💰 Construction Cost & Material Quantity Estimator (BOQ)", expanded=True):
        cost_est = estimate_construction_cost(built_a, tier=st.session_state.get("cost_tier", "Standard"))
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Estimated Cost", f"Rs. {cost_est['total_cost_lakhs']:.2f} Lakhs", f"Rs. {cost_est['total_cost_inr']:,.0f}")
        cc2.metric("Quality Tier", cost_est["tier"], f"Rs. {cost_est['rate_per_sqft']:,.0f} / sq.ft")
        cc3.metric("Built-up Area", f"{cost_est['built_up_area_sqft']:,.0f} sq.ft")

        st.markdown("**Milestone Cashflow Breakdown**")
        p_df = []
        for p in cost_est["phase_breakdown"]:
            p_df.append({
                "Phase": p["phase"],
                "Share %": f"{p['pct']:.1f}%",
                "Cost (Lakhs)": f"Rs. {p['cost_lakhs']:.2f} L",
                "Scope Description": p["description"],
            })
        st.dataframe(pd.DataFrame(p_df), use_container_width=True, hide_index=True)

        st.markdown("**Primary Material Takeoff (BOQ)**")
        m_df = []
        for m_name, m_val in cost_est["materials"].items():
            m_df.append({
                "Material": m_name,
                "Estimated Qty": f"{m_val['quantity']:,}",
                "Unit": m_val["unit"],
                "Specification": m_val["note"],
            })
        st.dataframe(pd.DataFrame(m_df), use_container_width=True, hide_index=True)

    # Room Schedule
    with st.expander("📋 Room Schedule Details"):
        r_rows = []
        for r in design["rooms"] + design["features"]:
            area = r["width"] * r["length"]
            r_rows.append({
                "Room": r["name"],
                "Width (ft)": f"{r['width']:.1f}",
                "Length (ft)": f"{r['length']:.1f}",
                "Area (sq.ft)": f"{area:.0f}",
                "Type": r.get("kind", "room").capitalize()
            })
        st.dataframe(pd.DataFrame(r_rows), use_container_width=True, hide_index=True)


# ============================================================
# PAGE 6 — 3D Visualization
# ============================================================
elif page == "🧊 3D Visualization":
    st.title("🧊 3D Interactive Visualization")
    st.caption("Rotate, zoom and pan the 3D model using your mouse or touchpad.")

    if not st.session_state.measurements:
        st.warning("⬅️ Complete Land Measurement first."); st.stop()
    if not st.session_state.requirements:
        st.warning("⬅️ Complete House Requirements first."); st.stop()
    if not st.session_state.designs:
        st.warning("⬅️ Generate designs in **📊 Design Comparison** first."); st.stop()

    design = _selected_design()
    if design is None:
        st.info("ℹ️ No design selected yet — showing Design A by default.")
        design = st.session_state.designs[0]

    st.info(f"🧊 Showing: **{design['design_name']}**")
    wall_h = st.slider("Wall height (ft)", min_value=8, max_value=14, value=9, step=1)

    with st.spinner("Building 3D model…"):
        try:
            fig3d = create_3d_view(
                design["rooms"],
                st.session_state.plot_width,
                st.session_state.plot_length,
                design["features"],
                design["design_name"],
                wall_height=float(wall_h),
            )
            st.plotly_chart(fig3d, use_container_width=True)
        except Exception as exc:
            st.error(f"3D rendering error: {exc}")

    st.caption("💡 Tip: Click and drag to rotate the 3D model. Scroll to zoom.")


# ============================================================
# PAGE 7 — PDF Report
# ============================================================
elif page == "📄 PDF Report":
    st.title("📄 Commercial PDF Concept & Feasibility Dossier")
    st.caption("Download a multi-page, publication-grade architectural and BOQ report.")

    if not st.session_state.measurements:
        st.warning("⬅️ Complete Land Measurement first."); st.stop()
    if not st.session_state.requirements:
        st.warning("⬅️ Complete House Requirements first."); st.stop()
    if not st.session_state.designs:
        st.warning("⬅️ Generate designs in **📊 Design Comparison** first."); st.stop()

    design = _selected_design()
    if design is None:
        st.info("ℹ️ No design selected — PDF will use Design A.")
        design = st.session_state.designs[0]

    st.info(f"📄 Report Layout: **{design['design_name']}**")

    # White-Label B2B input fields
    st.markdown("#### 🏢 B2B White-Label & Client Customization")
    w_col1, w_col2 = st.columns(2)
    with w_col1:
        client_name = st.text_input(
            "Prepared For (Client Name):",
            value=st.session_state.get("client_name", "Mr. & Mrs. Sharma"),
            help="Name of homeowner or real estate investor."
        )
    with w_col2:
        prepared_by = st.text_input(
            "Prepared By (Architect / Agency Name):",
            value=st.session_state.get("prepared_by", "Land2Home AI Architecture Studio"),
            help="Your agency or studio branding for white-label client presentation."
        )
    st.session_state.client_name = client_name
    st.session_state.prepared_by = prepared_by

    with st.expander("Report Contents Preview (8 Pages)"):
        st.markdown("""
        1. 🏠 **Executive Cover Page** — Client name, agency branding, plot dimensions, dossier ID
        2. 📐 **Land Verification & Visual Proof** — Plot measurements and side-by-side computer vision detection overlay
        3. 🏡 **Room Schedule & Validation Audit** — Exact carpet areas, non-overlapping geometry verification
        4. ☸️ **Vastu Shastra Compliance Audit** — 8-direction zone audit table, road orientation alignment, remedies
        5. 💰 **Construction Cost & Material BOQ** — Milestone project cashflows, material takeoff quantities (cement, steel, bricks)
        6. 🗺️ **2D Concept Floor Plan** — High-resolution architectural plan with furniture, dimensions, and legend
        7. 🧊 **3D Schematic Isometric Model** — Orthogonal structural perspective
        8. ⚠️ **Commercial Disclaimer & Terms** — Preliminary architectural and structural engineering caveats
        """)

    if st.button("📥 Generate Publication-Grade PDF Report", type="primary"):
        with st.spinner("Compiling high-resolution report, calculating BOQ and rendering architectural diagrams…"):
            try:
                built_a = sum(r["width"] * r["length"] for r in design["rooms"] if r.get("kind") != "amenity")
                cost_data = estimate_construction_cost(built_a, tier=st.session_state.get("cost_tier", "Standard"))
                vastu_data = analyze_vastu_compliance(
                    design["rooms"],
                    st.session_state.plot_width,
                    st.session_state.plot_length,
                    plot_facing=st.session_state.get("plot_facing", "North"),
                    features=design["features"]
                )

                raw_img = st.session_state.get("raw_plot_image")
                ann_img = st.session_state.get("detected_plot", {}).get("annotated_image") if st.session_state.get("detected_plot") else None

                pdf_buf = io.BytesIO()
                generate_pdf_report(
                    pdf_buf,
                    st.session_state.measurements,
                    st.session_state.requirements,
                    design["rooms"],
                    st.session_state.plot_width,
                    st.session_state.plot_length,
                    features=design["features"],
                    design=design,
                    raw_image=raw_img,
                    annotated_image=ann_img,
                    cost_data=cost_data,
                    vastu_data=vastu_data,
                    client_name=client_name,
                    prepared_by=prepared_by
                )
                pdf_buf.seek(0)
                st.download_button(
                    "⬇️ Download Commercial PDF Dossier",
                    data=pdf_buf,
                    file_name=f"Land2Home_Architectural_Dossier_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary",
                )
                st.success("🎉 PDF generated successfully! Click above to download the complete client dossier.")
            except Exception as exc:
                st.error(f"PDF generation error: {exc}")
                st.exception(exc)

# ============================================================
# Commercial Footer
# ============================================================
st.markdown("---")
st.caption("🏠 Land2Home AI Architecture Studio | www.land2home.ai | Commercial Architectural Concept Platform")
