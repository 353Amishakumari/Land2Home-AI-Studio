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
import os
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
# Global CSS — Modern PropTech SaaS Theme
# ============================================================
st.markdown("""
<style>
/* ── Google Fonts ───────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* ── Hide Streamlit chrome ──────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.stDeployButton { display: none; }
div[data-testid="stDecoration"] { display: none; }

/* ── Base typography & canvas ───────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #F8FAFC;
    color: #0F172A;
}

/* ── Sidebar ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stRadio label { color: #E2E8F0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #F1F5F9 !important; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }
[data-testid="stSidebar"] .stMarkdown p { color: #94A3B8 !important; font-size: 12px; }
[data-testid="stSidebar"] .stCaption { color: #64748B !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #94A3B8 !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #F1F5F9 !important; }
[data-testid="stSidebar"] .stSuccess { background: rgba(5,150,105,0.15) !important; border-color: #059669 !important; }
[data-testid="stSidebar"] .stInfo    { background: rgba(37,99,235,0.15) !important; border-color: #2563EB !important; }

/* Sidebar nav pills */
[data-testid="stSidebar"] .stRadio > div { gap: 2px; }
[data-testid="stSidebar"] .stRadio label {
    padding: 8px 12px;
    border-radius: 8px;
    transition: background 0.15s;
    font-size: 13px;
    font-weight: 500;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,0.08); }

/* ── Main content area ──────────────────────────────────── */
.main .block-container {
    padding-top: 16px;
    padding-left: 32px;
    padding-right: 32px;
    max-width: 1400px;
}

/* ── KPI / info cards ───────────────────────────────────── */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s;
}
.kpi-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.kpi-label {
    font-size: 12px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 12px;
    color: #94A3B8;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
}
.badge-green  { display:inline-block; background:#DCFCE7; color:#15803D; border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-blue   { display:inline-block; background:#DBEAFE; color:#1D4ED8; border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-amber  { display:inline-block; background:#FEF3C7; color:#B45309; border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-red    { display:inline-block; background:#FEE2E2; color:#DC2626; border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }

/* ── Step-flow cards (dashboard) ────────────────────────── */
.step-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #2563EB;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: flex-start;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.step-num {
    background: #2563EB;
    color: white;
    border-radius: 50%;
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700;
    flex-shrink: 0;
}
.step-title { font-weight: 600; color: #0F172A; font-size: 14px; }
.step-desc  { color: #64748B; font-size: 13px; margin-top: 2px; }

/* ── Primary CTA button ─────────────────────────────────── */
.stButton > button[kind="primary"],
.stButton > button[type="primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[type="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.4) !important;
}

/* ── Tabs ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #F1F5F9;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 500;
    font-size: 13px;
    color: #64748B;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #2563EB !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── Dataframes / tables ────────────────────────────────── */
[data-testid="stDataFrame"] { font-variant-numeric: tabular-nums; }
.tabular-num { font-variant-numeric: tabular-nums; }

/* ── Section divider label ──────────────────────────────── */
.section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 20px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #E2E8F0;
}

/* ── Design preview card ────────────────────────────────── */
.design-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 12px;
}

/* ── Vastu compliance pills ─────────────────────────────── */
.vastu-ok   { color: #059669; font-weight: 600; }
.vastu-warn { color: #D97706; font-weight: 600; }
.vastu-fail { color: #DC2626; font-weight: 600; }

/* ── Metric overrides ───────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    color: #0F172A;
}
[data-testid="stMetricLabel"] { color: #64748B; font-size: 13px; }

/* ── Info / warning / success boxes ────────────────────── */
.stAlert { border-radius: 10px; }

/* ── Expander ───────────────────────────────────────────── */
details > summary {
    font-weight: 600;
    color: #0F172A;
    font-size: 14px;
}

/* ── Sidebar CTA button ─────────────────────────────────── */
.sidebar-cta button {
    width: 100% !important;
    background: linear-gradient(135deg, #059669, #047857) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 12px !important;
}
</style>
""", unsafe_allow_html=True)

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
    "user_phone":          "",
    "user_city":           "",
    "is_unlocked":         False,
    "is_owner":            False,
    "unlocked_reason":     "",
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


def is_commercial_unlocked() -> bool:
    """Returns True if the user has paid or if owner mode is enabled."""
    return bool(st.session_state.get("is_owner", False) or st.session_state.get("is_unlocked", False))


def save_lead(name: str, phone: str, city: str, code: str = ""):
    """Save customer contact and UTR/promo lead to leads.csv."""
    lead_row = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "client_name": name.strip() or "Anonymous User",
        "phone": phone.strip() or "Not Provided",
        "city": city.strip() or "Not Provided",
        "plot_dims": f"{st.session_state.get('plot_width', 0):.0f}x{st.session_state.get('plot_length', 0):.0f} ft",
        "house_type": st.session_state.get("requirements", {}).get("house_type", "2BHK") if st.session_state.get("requirements") else "—",
        "utr_or_promo": code.strip() or "—",
        "status": "Unlocked" if code else "Lead Capture"
    }
    df_new = pd.DataFrame([lead_row])
    leads_path = "leads.csv"
    if os.path.exists(leads_path):
        try:
            df_old = pd.read_csv(leads_path)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df_all = df_new
    else:
        df_all = df_new
    df_all.to_csv(leads_path, index=False)


def render_commercial_unlock_card(feature_name: str = "Commercial Dossier & AutoCAD DXF"):
    """Renders the self-serve payment card with UPI QR and UTR validation."""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1A3A5C 0%, #244C73 100%);
                    padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;
                    border-left: 5px solid #27AE60;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="color: #FFFFFF; margin: 0 0 4px 0;">🔒 Unlock {feature_name}</h3>
                    <p style="color: #D6E4F0; margin: 0; font-size: 13.5px;">
                        Full 8-Page Architectural Concept Report, Material Takeoff (BOQ), and Layered AutoCAD (.DXF) Files.
                    </p>
                </div>
                <div style="background: #27AE60; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin-top: 8px;">
                    One-Time License: ₹199
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_lead, col_pay = st.columns([0.48, 0.52])

    with col_lead:
        st.markdown("##### 1. Client & Project Details")
        u_name = st.text_input("Full Name / Client Name *", value=st.session_state.get("client_name", ""), key="unlock_name")
        u_phone = st.text_input("WhatsApp / Contact Number *", value=st.session_state.get("user_phone", ""), placeholder="+91 98765 43210", key="unlock_phone")
        u_city = st.text_input("City / Project Location", value=st.session_state.get("user_city", ""), placeholder="e.g. Bangalore, Mumbai, Pune", key="unlock_city")
        st.caption("🔒 Details are stored securely for project record and drawing delivery.")

    with col_pay:
        st.markdown("##### 2. Instant UPI Payment (₹199)")

        # --- Merchant UPI configuration -----------------------------------------
        # Real UPI ID from PhonePe (Kotak Bank ×0608)
        # Override via st.secrets["MERCHANT_UPI_ID"] if configured in secrets.toml
        try:
            upi_id = st.secrets.get("MERCHANT_UPI_ID", "7643897910@ybl")
        except Exception:
            upi_id = "7643897910@ybl"

        # NPCI-compliant UPI deep-link URI
        upi_uri = (
            f"upi://pay?pa={upi_id}"
            f"&pn=Amisha%20Kumari"
            f"&am=199.00"
            f"&cu=INR"
            f"&tn=Land2Home%20Report"
        )

        # High-contrast scannable QR (300×300 with 4-module quiet zone, black on white)
        upi_qr_url = (
            f"https://api.qrserver.com/v1/create-qr-code/"
            f"?size=300x300&margin=16&qzone=4&color=000000&bgcolor=ffffff"
            f"&data={upi_uri.replace('&', '%26')}"
        )

        p_c1, p_c2 = st.columns([0.46, 0.54])
        with p_c1:
            # Check if a local QR asset exists (placed in repo as assets/my_upi_qr.png)
            import os
            local_qr = "assets/my_upi_qr.png"
            if os.path.exists(local_qr):
                st.image(local_qr, width=160, caption="Scan to Pay ₹199")
            else:
                try:
                    st.image(upi_qr_url, width=160, caption="Scan with any UPI App")
                except Exception:
                    st.info(f"UPI: {upi_id}")

        with p_c2:
            st.markdown("**UPI ID (copy & paste):**")
            st.code(upi_id, language=None)
            st.markdown("**Amount:** **₹199** *(One-Time License)*")
            st.caption("Works with: GPay · PhonePe · Paytm · BHIM · CRED")
            st.caption("After payment, enter your 12-digit UTR below.")

        ref_code = st.text_input(
            "Transaction Reference (12-Digit UTR) / Promo Code *",
            placeholder="e.g. 431289567123 or promo code",
            key="unlock_code_in"
        )

        if st.button("🚀 Verify & Unlock Commercial Downloads", type="primary", key="btn_verify_payment"):
            clean_code = ref_code.strip()
            valid_promos = {"AMISHA2026", "FOUNDER", "MTECH", "DEMO", "PROMO100", "FREEPASS", "VIP199"}
            is_valid_utr = len(clean_code) == 12 and clean_code.isdigit()
            is_promo = clean_code.upper() in valid_promos

            if not u_name.strip() or not u_phone.strip():
                st.warning("Please provide your Name and WhatsApp number before verification.")
            elif is_valid_utr or is_promo:
                st.session_state["is_unlocked"] = True
                st.session_state["client_name"] = u_name.strip()
                st.session_state["user_phone"] = u_phone.strip()
                st.session_state["user_city"] = u_city.strip()
                st.session_state["unlocked_reason"] = f"UTR: {clean_code}" if is_valid_utr else f"Promo: {clean_code.upper()}"
                save_lead(u_name, u_phone, u_city, clean_code)
                st.balloons()
                st.success("Commercial Package Successfully Unlocked! You can now download the complete PDF Dossier and AutoCAD (.DXF) files.")
                st.rerun()
            else:
                st.error("Invalid reference code. Please enter a valid 12-digit bank UTR / UPI reference ID or a valid promotional voucher.")


# ============================================================
# Sidebar — Modern Dark Navigation
# ============================================================
with st.sidebar:
    # Brand logo / wordmark
    st.markdown("""
    <div style="padding: 16px 4px 8px 4px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <span style="font-size:28px;">🏠</span>
            <div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:17px; font-weight:800; color:#F1F5F9; line-height:1.1;">Land2Home</div>
                <div style="font-size:10px; color:#64748B; letter-spacing:0.08em; text-transform:uppercase; font-weight:500;">AI Architecture Studio</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="color:#475569;">Navigation</div>', unsafe_allow_html=True)

    page = st.radio(
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

    # Project Progress tracker
    st.markdown('<div class="section-label" style="color:#475569; margin-top:16px;">Project Progress</div>', unsafe_allow_html=True)

    def _status_pill(done: bool, label: str) -> str:
        if done:
            return f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;"><span style="color:#10B981;font-size:14px;">✓</span><span style="color:#CBD5E1;font-size:12px;">{label}</span></div>'
        return f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;"><span style="color:#475569;font-size:14px;">○</span><span style="color:#64748B;font-size:12px;">{label}</span></div>'

    st.markdown(
        _status_pill(bool(st.session_state.measurements), "Land Measurements") +
        _status_pill(bool(st.session_state.requirements), "House Requirements") +
        _status_pill(bool(st.session_state.designs), "Designs Generated") +
        _status_pill(bool(st.session_state.selected_design_id), "Design Selected"),
        unsafe_allow_html=True
    )

    # Commercial access badge
    st.markdown('<div class="section-label" style="color:#475569; margin-top:12px;">License</div>', unsafe_allow_html=True)
    if is_commercial_unlocked():
        if st.session_state.get("is_owner", False):
            st.success("👑 **Owner Mode Active**\nUnlimited Free Exports")
        else:
            st.success(f"💎 **Commercial Unlocked**\n({st.session_state.get('unlocked_reason', 'Active')})")
    else:
        st.info("🔒 **Freemium Preview**\nFull CAD/PDF locked (₹199)")

    # Studio Owner Access
    with st.expander("🔐 Studio Owner Access", expanded=st.session_state.get("is_owner", False)):
        if st.session_state.get("is_owner", False):
            st.write("Welcome, Studio Founder! You have unlimited access to all features.")
            if os.path.exists("leads.csv"):
                try:
                    leads_df = pd.read_csv("leads.csv")
                    st.caption(f"📊 Collected Leads: **{len(leads_df)}**")
                    csv_bytes = leads_df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Download leads.csv", data=csv_bytes, file_name="leads.csv", mime="text/csv", key="btn_dl_leads")
                except Exception:
                    pass
            else:
                st.caption("No leads collected yet.")

            if st.button("🔒 Switch to Public User Mode", key="btn_logout_owner"):
                st.session_state.is_owner = False
                st.session_state.is_unlocked = False
                st.session_state.unlocked_reason = ""
                st.rerun()
        else:
            st.caption("Enter owner passcode for personal testing, demos, and unlimited free exports.")
            owner_code = st.text_input("Owner Passcode:", type="password", key="owner_pass_in")
            if st.button("Authenticate", key="btn_auth_owner"):
                expected_code = "AMISHA2026"
                try:
                    if "OWNER_PASSCODE" in st.secrets:
                        expected_code = st.secrets["OWNER_PASSCODE"]
                except Exception:
                    pass
                if owner_code.strip() == expected_code:
                    st.session_state.is_owner = True
                    st.session_state.is_unlocked = True
                    st.session_state.unlocked_reason = "Owner Passcode"
                    st.success("Welcome, Studio Founder! Owner mode enabled.")
                    st.rerun()
                else:
                    st.error("Invalid passcode.")

    st.markdown("---")
    st.caption("Land2Home AI Architecture Studio\nCommercial PropTech Planning & BOQ Engine")


# ============================================================
# PAGE 1 — Dashboard
# ============================================================
if page == "🏠 Dashboard":

    # Hero banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #1E293B 100%);
                padding: 36px 40px; border-radius: 16px; margin-bottom: 28px;
                border: 1px solid #334155; position: relative; overflow: hidden;">
        <div style="position:absolute;top:0;right:0;width:300px;height:100%;
                    background:radial-gradient(circle at 80% 50%, rgba(37,99,235,0.15) 0%, transparent 70%);
                    pointer-events:none;"></div>
        <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:32px; font-weight:800;
                    color:#FFFFFF; margin-bottom:8px; letter-spacing:-0.5px;">
            🏠 Land2Home AI Studio
        </div>
        <div style="color:#94A3B8; font-size:15px; margin-bottom:20px; max-width:620px;">
            Automated Indian Residential Floor Plans &nbsp;•&nbsp; 8-Direction Vastu Auditor
            &nbsp;•&nbsp; Instant BOQ Estimator &nbsp;•&nbsp; AutoCAD DXF Export
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span style="background:rgba(5,150,105,0.2); border:1px solid rgba(5,150,105,0.4);
                         color:#34D399; border-radius:20px; padding:4px 14px; font-size:12px; font-weight:600;">
                ⚡ &lt;2s AI Inference
            </span>
            <span style="background:rgba(37,99,235,0.2); border:1px solid rgba(37,99,235,0.4);
                         color:#93C5FD; border-radius:20px; padding:4px 14px; font-size:12px; font-weight:600;">
                🔲 Zero-Overlap Geometry Engine
            </span>
            <span style="background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.4);
                         color:#C4B5FD; border-radius:20px; padding:4px 14px; font-size:12px; font-weight:600;">
                📐 AutoCAD DXF Ready
            </span>
            <span style="background:rgba(245,158,11,0.2); border:1px solid rgba(245,158,11,0.4);
                         color:#FCD34D; border-radius:20px; padding:4px 14px; font-size:12px; font-weight:600;">
                ☸️ 8-Direction Vastu Audit
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI cards (shown when measurements and designs are available)
    if st.session_state.measurements and st.session_state.designs:
        design_kpi = _selected_design() or st.session_state.designs[0]
        built_kpi = sum(r["width"] * r["length"] for r in design_kpi["rooms"] if r.get("kind") != "amenity")
        plot_area = st.session_state.plot_width * st.session_state.plot_length
        efficiency = (built_kpi / plot_area * 100) if plot_area > 0 else 0
        vastu_kpi = analyze_vastu_compliance(
            design_kpi["rooms"], st.session_state.plot_width, st.session_state.plot_length,
            plot_facing=st.session_state.get("plot_facing", "North"), features=design_kpi["features"]
        )
        cost_kpi = estimate_construction_cost(built_kpi, tier=st.session_state.get("cost_tier", "Standard"))
        eff_badge = "badge-green" if efficiency >= 70 else "badge-amber"
        vastu_badge = "badge-green" if vastu_kpi["score"] >= 70 else ("badge-amber" if vastu_kpi["score"] >= 50 else "badge-red")

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📐 Plot & Built-up Area</div>
                <div class="kpi-value">{plot_area:,.0f} <span style="font-size:14px;color:#64748B;">sq.ft</span></div>
                <div class="kpi-sub">Built-up: {built_kpi:,.0f} sq.ft &nbsp;|&nbsp; {st.session_state.plot_width:.0f}×{st.session_state.plot_length:.0f} ft</div>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">📊 Space Efficiency</div>
                <div class="kpi-value">{efficiency:.1f}<span style="font-size:16px;color:#64748B;">%</span></div>
                <div class="kpi-sub"><span class="{eff_badge}">{'Optimal' if efficiency >= 70 else 'Review'}</span> &nbsp; Plot utilisation</div>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">☸️ Vastu Compliance</div>
                <div class="kpi-value">{vastu_kpi['score']:.0f}<span style="font-size:16px;color:#64748B;">/100</span></div>
                <div class="kpi-sub"><span class="{vastu_badge}">{vastu_kpi['grade']}</span> &nbsp; {st.session_state.get('plot_facing','North')} Facing</div>
            </div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">💰 Estimated Cost</div>
                <div class="kpi-value">₹{cost_kpi['total_cost_lakhs']:.2f} <span style="font-size:14px;color:#64748B;">L</span></div>
                <div class="kpi-sub">₹{cost_kpi['rate_per_sqft']:,.0f}/sq.ft &nbsp;|&nbsp; {st.session_state.get('cost_tier','Standard')} tier</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # Workflow steps
    st.markdown('<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:18px;font-weight:700;color:#0F172A;margin-bottom:16px;">Commercial Workflow</div>', unsafe_allow_html=True)

    steps = [
        ("1", "📐 Land Measurement & Computer Vision", "Enter plot dimensions or upload a site photo/sketch to auto-detect boundary using OpenCV."),
        ("2", "🏡 House Requirements & Vastu", "Select BHK, floors, Vastu road facing (N/E/S/W), and construction quality tier."),
        ("3", "📊 Design Comparison & Scoring", "Generate 3 distinct architectural layouts evaluated by geometry, Vastu, and BOQ cost."),
        ("4", "📋 2D Floor Plan & DXF Export", "Review architectural concept drawings and export industry-standard AutoCAD (.DXF) files."),
        ("5", "🧊 3D Visualization", "Explore the interactive 3D model with custom wall heights, orbit, and zoom."),
        ("6", "📄 Commercial PDF Dossier", "Generate a publication-grade, white-labeled client feasibility report with BOQ and visual proof."),
    ]
    for step_num, step_title, step_desc in steps:
        st.markdown(f"""
        <div class="step-card">
            <div class="step-num">{step_num}</div>
            <div>
                <div class="step-title">{step_title}</div>
                <div class="step-desc">{step_desc}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:16px 20px;">
        <span style="font-weight:600; color:#1D4ED8;">🏗️ Commercial Space Planning Engine:</span>
        <span style="color:#1E40AF; font-size:14px;">
        Land2Home generates three architecturally distinct concept layouts:
        <strong>Central Hall</strong>, <strong>Corridor Plan</strong>, and <strong>Open Living+Dining</strong>.
        Features non-overlapping geometric partitions, Vastu energy alignment, and full bill of quantities (BOQ).
        </span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PAGE 2 — Land Measurement
# ============================================================
elif page == "📐 Land Measurement":
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">📐 Land Measurement & Plot Calibration</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Enter plot dimensions manually or upload a site image/sketch for automated computer vision detection.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_rect, tab_sq, tab_poly, tab_img = st.tabs(
        ["🔲 Rectangular Plot", "⬛ Square Plot", "⬡ Custom Polygon", "📸 Land Image / Sketch Detection"])

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

    # ---- Measurement Results ----
    if st.session_state.measurements:
        m = st.session_state.measurements
        st.markdown("---")

        st.markdown('<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:18px;font-weight:700;color:#0F172A;margin-bottom:16px;">📊 Measurement Results</div>', unsafe_allow_html=True)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Area (sq.ft)", f"{m.get('area_sqft', 0):,.0f}")
        mc2.metric("Area (sq.m)",  f"{m.get('area_sqm',  0):,.2f}")
        mc3.metric("Perimeter",    f"{m.get('perimeter_ft', 0):,.1f} ft")
        mc4.metric("Area (Cents)", f"{m.get('area_cents', 0):.3f}")

        W = st.session_state.plot_width
        L = st.session_state.plot_length
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_facecolor("#F8FAFC")
        fig.patch.set_facecolor("#F8FAFC")
        from matplotlib.patches import Rectangle as MRect
        ax.add_patch(MRect((0, 0), W, L, fill=True, facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=2.5))
        ax.text(W/2, -1.5, f"← {W:.0f} ft →", ha="center", fontsize=9, color="#475569")
        ax.text(-1.5, L/2, f"← {L:.0f} ft →", ha="center", fontsize=9, color="#475569", rotation=90)
        ax.text(W/2, L/2, f"{W:.0f}×{L:.0f} ft\n{m.get('area_sqft',0):,.0f} sq.ft",
                ha="center", va="center", fontsize=11, fontweight="bold", color="#1D4ED8")
        ax.set_xlim(-3, W+3); ax.set_ylim(-3, L+3)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("Plot Boundary Diagram", fontsize=12, fontweight="bold", color="#0F172A", pad=10)
        st.pyplot(fig); plt.close(fig)


# ============================================================
# PAGE 3 — House Requirements
# ============================================================
elif page == "🏡 House Requirements":
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">🏡 House Requirements & Vastu Configuration</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Configure house type, floors, Vastu orientation, and construction quality tier.</div>
    </div>
    """, unsafe_allow_html=True)

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

        submitted = st.form_submit_button("💾 Save Requirements & Validate", type="primary")

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
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">📊 Design Comparison & Commercial Feasibility</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Generate 3 distinct layouts and evaluate them by spatial efficiency, Vastu score, and BOQ budget.</div>
    </div>
    """, unsafe_allow_html=True)

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

        st.markdown('<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:18px;font-weight:700;color:#0F172A;margin:20px 0 12px 0;">Commercial Design Overview</div>', unsafe_allow_html=True)

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
        st.markdown('<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:18px;font-weight:700;color:#0F172A;margin:20px 0 12px 0;">Architectural Floor Plan Previews</div>', unsafe_allow_html=True)

        prev_cols = st.columns(3)
        for col, design in zip(prev_cols, designs):
            with col:
                st.markdown(f"""
                <div class="design-card">
                    <div style="font-weight:700; color:#0F172A; font-size:14px; margin-bottom:10px;">
                        {design['design_name'].split('—')[1].strip() if '—' in design['design_name'] else design['design_name']}
                    </div>
                """, unsafe_allow_html=True)
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
                st.markdown("</div>", unsafe_allow_html=True)

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
        st.markdown('<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-size:18px;font-weight:700;color:#0F172A;margin-bottom:12px;">Select Preferred Design for Full Export</div>', unsafe_allow_html=True)

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
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">📋 2D Concept Floor Plan & AutoCAD Export</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Architectural layout drawing, Vastu energy audit, and construction bill of quantities.</div>
    </div>
    """, unsafe_allow_html=True)

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

    # Main tabs for this page
    tab_plan, tab_vastu, tab_boq, tab_exports = st.tabs([
        "📐 2D & 3D Plans",
        "🧭 Vastu Audit",
        "📊 BOQ & Cost",
        "⬇️ Engineering Exports"
    ])

    # Pre-compute shared data
    built_a = sum(r["width"] * r["length"] for r in design["rooms"] if r.get("kind") != "amenity")
    vastu = analyze_vastu_compliance(
        design["rooms"],
        st.session_state.plot_width,
        st.session_state.plot_length,
        plot_facing=st.session_state.get("plot_facing", "North"),
        features=design["features"]
    )
    cost_est = estimate_construction_cost(built_a, tier=st.session_state.get("cost_tier", "Standard"))

    # ── Tab 1: 2D & 3D Plans ────────────────────────────────
    with tab_plan:
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

                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
                plt.close(fig)
                buf.seek(0)
                st.download_button(
                    "⬇️ Download 2D Floor Plan (PNG)",
                    data=buf, file_name=f"{design['design_name'].replace(' ', '_')}.png",
                    mime="image/png",
                )
            except Exception as exc:
                st.error(f"2D rendering error: {exc}")

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

    # ── Tab 2: Vastu Audit ───────────────────────────────────
    with tab_vastu:
        # Score KPIs
        vc1, vc2, vc3 = st.columns(3)
        vc1.metric("Plot Facing", f"{vastu['plot_facing']} Facing")
        vc2.metric("Vastu Score", f"{vastu['score']:.1f} / 100")
        vc3.metric("Rating", vastu["grade"])

        st.markdown("---")

        # Compliance table with color coding
        v_df = []
        for itm in vastu["audit_items"]:
            status = itm["status"]
            if "✅" in status or "compliant" in status.lower():
                status_disp = f"✅ {status}"
            elif "⚠️" in status or "partial" in status.lower():
                status_disp = f"⚠️ {status}"
            else:
                status_disp = f"❌ {status}"
            v_df.append({
                "Room": itm["room"],
                "Placed Zone": itm["zone"],
                "Ideal Zone": itm["ideal_zone"],
                "Compliance": status_disp,
                "Architectural Tip": itm["tip"],
            })
        st.dataframe(pd.DataFrame(v_df), use_container_width=True, hide_index=True)

        if vastu.get("recommendations"):
            st.markdown("**Key Harmonization Tips:**")
            for r in vastu["recommendations"]:
                st.caption(f"• {r}")

    # ── Tab 3: BOQ & Cost ────────────────────────────────────
    with tab_boq:
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Estimated Cost", f"Rs. {cost_est['total_cost_lakhs']:.2f} Lakhs", f"Rs. {cost_est['total_cost_inr']:,.0f}")
        cc2.metric("Quality Tier", cost_est["tier"], f"Rs. {cost_est['rate_per_sqft']:,.0f} / sq.ft")
        cc3.metric("Built-up Area", f"{cost_est['built_up_area_sqft']:,.0f} sq.ft")

        st.markdown("---")
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

    # ── Tab 4: Engineering Exports ───────────────────────────
    with tab_exports:
        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            st.markdown("""
            <div class="kpi-card" style="text-align:center; padding:28px 20px;">
                <div style="font-size:36px; margin-bottom:12px;">📐</div>
                <div style="font-weight:700; font-size:16px; color:#0F172A; margin-bottom:6px;">AutoCAD DXF File</div>
                <div style="color:#64748B; font-size:13px; margin-bottom:16px;">Layered CAD drawings compatible with AutoCAD, FreeCAD, and LibreCAD.</div>
            </div>
            """, unsafe_allow_html=True)
            if is_commercial_unlocked():
                try:
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
                        type="primary",
                    )
                except Exception as exc:
                    st.error(f"DXF export error: {exc}")
            else:
                st.button("🔒 Locked — Unlock for ₹199", disabled=True)

        with exp_col2:
            st.markdown("""
            <div class="kpi-card" style="text-align:center; padding:28px 20px;">
                <div style="font-size:36px; margin-bottom:12px;">📄</div>
                <div style="font-weight:700; font-size:16px; color:#0F172A; margin-bottom:6px;">Commercial PDF Dossier</div>
                <div style="color:#64748B; font-size:13px; margin-bottom:16px;">8-page publication-grade architectural report with BOQ, Vastu audit, and visual proof.</div>
            </div>
            """, unsafe_allow_html=True)
            if is_commercial_unlocked():
                st.info("Navigate to **📄 PDF Report** page to generate and download the full dossier.")
            else:
                st.button("🔒 Locked — Unlock for ₹199", disabled=True, key="pdf_lock_btn")

        # Unlock card if locked
        if not is_commercial_unlocked():
            st.markdown("---")
            render_commercial_unlock_card("AutoCAD (.DXF) CAD Files & Full Report")


# ============================================================
# PAGE 6 — 3D Visualization
# ============================================================
elif page == "🧊 3D Visualization":
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">🧊 3D Interactive Visualization</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Rotate, zoom and pan the 3D model using your mouse or touchpad.</div>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:24px;font-weight:700;color:#0F172A;">📄 Commercial PDF Concept & Feasibility Dossier</div>
        <div style="color:#64748B;font-size:14px;margin-top:4px;">Download a multi-page, publication-grade architectural and BOQ report.</div>
    </div>
    """, unsafe_allow_html=True)

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

    # Check monetization lock
    if is_commercial_unlocked():
        st.markdown("""
        <div style="background:linear-gradient(135deg,#064E3B,#065F46); border-radius:10px;
                    padding:14px 20px; border-left:4px solid #10B981; margin-bottom:20px;">
            <span style="color:#34D399; font-weight:700; font-size:14px;">👑 Commercial License Active</span>
            <span style="color:#A7F3D0; font-size:13px; margin-left:8px;">— Unlimited PDF & DXF Generation Enabled</span>
        </div>
        """, unsafe_allow_html=True)

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

    else:
        render_commercial_unlock_card("8-Page Commercial PDF Feasibility Dossier")

        with st.expander("Preview Dossier Outline (Unlocked upon purchase)"):
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


# ============================================================
# Commercial Footer
# ============================================================
st.markdown("---")
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
            padding:4px 0; color:#94A3B8; font-size:12px;">
    <span>🏠 <strong style="color:#64748B;">Land2Home AI Architecture Studio</strong>
        &nbsp;|&nbsp; Commercial Architectural Concept Platform</span>
    <span>
        <a href="https://land2home-ai-studio-jtvtkxuc9xzjvxy7qevkb8.streamlit.app/"
           target="_blank" style="color:#2563EB; text-decoration:none; font-weight:500;">
           🌐 Live App
        </a>
        &nbsp;·&nbsp;
        <a href="https://github.com/353Amishakumari/Land2Home-AI-Studio"
           target="_blank" style="color:#2563EB; text-decoration:none; font-weight:500;">
           GitHub
        </a>
    </span>
</div>
""", unsafe_allow_html=True)
