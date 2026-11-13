"""
Land2Home — Professional Commercial PDF Report Generator
=========================================================

Generates a multi-page, publication-grade architectural feasibility and concept PDF
using ReportLab with commercial SaaS branding, white-label client details,
land image & boundary detection visual proof, Vastu compliance audit,
construction cost estimation (BOQ), and 2D/3D visualizations.
"""

from __future__ import annotations
import datetime
from io import BytesIO
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _styles():
    ss = getSampleStyleSheet()
    custom = {
        "Title2": ParagraphStyle("Title2", parent=ss["Title"],
                                 fontSize=22, textColor=colors.HexColor("#1A3A5C"),
                                 spaceAfter=4, alignment=TA_CENTER),
        "Subtitle": ParagraphStyle("Subtitle", parent=ss["Normal"],
                                   fontSize=11, textColor=colors.HexColor("#34495E"),
                                   spaceAfter=4, alignment=TA_CENTER),
        "AgencyHeader": ParagraphStyle("AgencyHeader", parent=ss["Normal"],
                                       fontSize=9, textColor=colors.HexColor("#2980B9"),
                                       spaceAfter=12, alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "H2": ParagraphStyle("H2", parent=ss["Heading2"],
                              fontSize=12, textColor=colors.HexColor("#1A3A5C"),
                              spaceBefore=10, spaceAfter=4),
        "H3": ParagraphStyle("H3", parent=ss["Heading3"],
                              fontSize=10, textColor=colors.HexColor("#2E5F8A"),
                              spaceBefore=6, spaceAfter=3),
        "Body": ParagraphStyle("Body", parent=ss["Normal"],
                               fontSize=8.5, leading=13, spaceAfter=4),
        "TableBody": ParagraphStyle("TableBody", parent=ss["Normal"],
                                    fontSize=7.5, leading=10, textColor=colors.HexColor("#222222")),
        "TableBodyBold": ParagraphStyle("TableBodyBold", parent=ss["Normal"],
                                        fontSize=7.5, leading=10, fontName="Helvetica-Bold",
                                        textColor=colors.HexColor("#1A3A5C")),
        "Small": ParagraphStyle("Small", parent=ss["Normal"],
                                fontSize=7.5, leading=11,
                                textColor=colors.HexColor("#555555")),
        "Disclaimer": ParagraphStyle("Disclaimer", parent=ss["Normal"],
                                     fontSize=7.5, leading=11,
                                     textColor=colors.HexColor("#666666"),
                                     borderColor=colors.HexColor("#DDDDDD"),
                                     borderWidth=0.5, borderPad=5,
                                     backColor=colors.HexColor("#FBFBFB")),
        "Green": ParagraphStyle("Green", parent=ss["Normal"],
                                fontSize=8.5, textColor=colors.HexColor("#27AE60"), fontName="Helvetica-Bold"),
        "Red":   ParagraphStyle("Red",   parent=ss["Normal"],
                                fontSize=8.5, textColor=colors.HexColor("#C0392B"), fontName="Helvetica-Bold"),
        "Amber": ParagraphStyle("Amber", parent=ss["Normal"],
                                fontSize=8.5, textColor=colors.HexColor("#D35400"), fontName="Helvetica-Bold"),
        "MetricBadge": ParagraphStyle("MetricBadge", parent=ss["Normal"],
                                      fontSize=9.0, textColor=colors.HexColor("#1A3A5C"),
                                      fontName="Helvetica-Bold", alignment=TA_CENTER),
    }
    return ss, custom


def _table_style(has_header: bool = True) -> TableStyle:
    cmds = [
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 7.5),
        ("GRID",      (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("PADDING",   (0,0), (-1,-1), 4.0),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#F7F9FC")]),
    ]
    if has_header:
        cmds += [
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1A3A5C")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,0), 8.0),
        ]
    return TableStyle(cmds)


# ---------------------------------------------------------------------------
# Figure → ReportLab Image helper
# ---------------------------------------------------------------------------

def _fig_to_image(fig: plt.Figure,
                  width: float = 6.5 * inch,
                  height: float = 5.2 * inch) -> Image:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width, height=height, kind="proportional")


def _make_land_comparison_image(raw_img: Any, ann_img: Any) -> Image | None:
    """Create a side-by-side comparison figure of uploaded image and detected boundary."""
    if raw_img is None and ann_img is None:
        return None
    try:
        import numpy as np
        from PIL import Image as PILImage

        def _to_rgb(img):
            if img is None:
                return None
            if isinstance(img, (bytes, bytearray)):
                img = PILImage.open(BytesIO(img))
            if hasattr(img, "convert"):
                return np.array(img.convert("RGB"))
            if isinstance(img, np.ndarray):
                if len(img.shape) == 2:
                    return np.stack([img] * 3, axis=-1)
                elif img.shape[2] == 3:
                    return img
                elif img.shape[2] == 4:
                    return img[:, :, :3]
            return None

        arr_raw = _to_rgb(raw_img)
        arr_ann = _to_rgb(ann_img)

        if arr_raw is None and arr_ann is None:
            return None

        has_both = (arr_raw is not None) and (arr_ann is not None)
        n_plots = 2 if has_both else 1
        fig, axes = plt.subplots(1, n_plots, figsize=(6.5, 2.5), dpi=150)

        if has_both:
            axes[0].imshow(arr_raw)
            axes[0].set_title("Uploaded Site Photo / Sketch", fontsize=8.5, fontweight="bold", color="#1A3A5C", pad=4)
            axes[0].axis("off")
            axes[1].imshow(arr_ann)
            axes[1].set_title("AI Boundary & Corner Calibration", fontsize=8.5, fontweight="bold", color="#1A3A5C", pad=4)
            axes[1].axis("off")
        else:
            ax = axes if n_plots == 1 else axes[0]
            single = arr_ann if arr_ann is not None else arr_raw
            title = "AI Boundary Detection & Calibration" if arr_ann is not None else "Uploaded Site Photo / Sketch"
            ax.imshow(single)
            ax.set_title(title, fontsize=8.5, fontweight="bold", color="#1A3A5C", pad=4)
            ax.axis("off")

        fig.tight_layout(pad=0.8)
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=6.5 * inch, height=2.5 * inch, kind="proportional")
    except Exception as exc:
        print(f"Notice: Failed to compose land comparison figure in PDF: {exc}")
        return None


def _clean_status(status_str: str) -> str:
    """Strip emojis from status string for clean PDF rendering."""
    return (status_str.replace("✅", "")
                      .replace("❌", "")
                      .replace("⚠️", "")
                      .replace("✓", "")
                      .replace("✗", "")
                      .strip())


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_pdf_report(
    output_path: str,
    measurements: dict,
    requirements: dict,
    rooms: list[dict],
    plot_width: float = 30.0,
    plot_length: float = 40.0,
    features: list[dict] | None = None,
    design: dict | None = None,
    raw_image: Any = None,
    annotated_image: Any = None,
    cost_data: dict | None = None,
    vastu_data: dict | None = None,
    client_name: str = "",
    prepared_by: str = "Land2Home AI Architecture Studio"
) -> None:
    """
    Generate the complete commercial PDF report and write it to output_path.
    """
    features    = features    or []
    design      = design      or {}
    client_name = client_name.strip() or "Valued Client"
    prepared_by = prepared_by.strip() or "Land2Home AI Architecture Studio"
    ss, cs      = _styles()

    # Calculate built-up area
    total_built_area = sum(r.get("width", 0) * r.get("length", 0)
                           for r in rooms if r.get("kind") != "amenity")

    # Precompute BOQ if missing or refresh with actual built area
    if cost_data is None:
        try:
            from src.cost_estimation.estimator import estimate_construction_cost
            cost_data = estimate_construction_cost(total_built_area or (plot_width * plot_length * 0.75),
                                                   tier=requirements.get("cost_tier", "Standard"))
        except Exception:
            cost_data = {}

    # Precompute Vastu if missing
    if vastu_data is None:
        try:
            from src.evaluation.vastu import analyze_vastu_compliance
            facing = requirements.get("plot_facing", "North")
            vastu_data = analyze_vastu_compliance(rooms, plot_width, plot_length,
                                                  plot_facing=facing, features=features)
        except Exception:
            vastu_data = {}

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.5 * cm,   bottomMargin=1.5 * cm,
        title="Land2Home Architectural Feasibility Report",
        author=prepared_by,
    )

    story: list = []

    # ================================================================
    # PAGE 1 — Commercial Title Page & Project Header
    # ================================================================
    ref_id = f"L2H-{datetime.date.today().strftime('%Y%m%d')}-{abs(hash(str(rooms))) % 10000:04d}"
    c_tier_val = cost_data.get("tier", "Standard")
    c_rate_val = cost_data.get("rate_per_sqft", 2100)

    story += [
        Spacer(1, 1.2 * inch),
        Paragraph("Land2Home Architecture Studio", cs["Title2"]),
        Paragraph("AI-Powered Residential Planning & Feasibility Report", cs["Subtitle"]),
        Paragraph(f"Prepared by: {prepared_by}", cs["AgencyHeader"]),
        Spacer(1, 0.2 * inch),
        HRFlowable(width="85%", thickness=2.5, color=colors.HexColor("#1A3A5C"),
                   spaceAfter=20, spaceBefore=0),
        Spacer(1, 0.15 * inch),
        Paragraph("Executive Architectural Concept & BOQ Dossier", ParagraphStyle(
            "sub2", parent=ss["Normal"], fontSize=13,
            textColor=colors.HexColor("#2C3E50"), alignment=TA_CENTER, fontName="Helvetica-Bold")),
        Spacer(1, 0.3 * inch),
        _info_table([
            ["Client Name",      client_name],
            ["Prepared By",      prepared_by],
            ["Reference Dossier",ref_id],
            ["Plot Dimensions",  f"{plot_width:.1f} × {plot_length:.1f} ft"],
            ["Total Land Area",  measurements.get("area_str", "—")],
            ["Configuration",    f"{requirements.get('house_type', '—')} ({requirements.get('floors', '1 Floor')})"],
            ["Plot Orientation", f"{requirements.get('plot_facing', 'North')} Facing"],
            ["Selected Layout",  design.get("design_name", "Concept Design")],
            ["Construction Tier",f"{c_tier_val} (Rs. {c_rate_val:,.0f}/sq.ft)"],
            ["Report Date",      datetime.date.today().strftime("%d %B %Y")],
        ], ss),
        Spacer(1, 0.5 * inch),
        Paragraph("Confidential & Proprietary Architectural Feasibility Document", cs["Small"]),
        PageBreak(),
    ]

    # ================================================================
    # PAGE 2 — Land Measurements & Boundary Detection Proof
    # ================================================================
    story += [
        Paragraph("1. Land Analysis & Geometry Verification", cs["H2"]),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB"),
                   spaceAfter=8),
    ]

    meas_data = [
        ["Measurement Metric", "Calculated Value"],
        ["Plot Dimensions (W × L)", f"{plot_width:.1f} × {plot_length:.1f} ft"],
        ["Gross Land Area", f"{measurements.get('area_sqft', 0):,.1f} sq.ft ({measurements.get('area_sqm', 0):,.2f} sq.m)"],
        ["Land Area in Cents", f"{measurements.get('area_cents', 0):.3f} Cents"],
        ["Boundary Perimeter", f"{measurements.get('perimeter_ft', 0):,.1f} ft"],
    ]
    if measurements.get("usable_area_sqft"):
        meas_data += [
            ["Usable Build Envelope Width", f"{measurements.get('usable_width_ft', 0):.1f} ft"],
            ["Usable Build Envelope Length", f"{measurements.get('usable_length_ft', 0):.1f} ft"],
            ["Net Usable Area (after setbacks)", f"{measurements.get('usable_area_sqft', 0):,.1f} sq.ft"],
        ]
    story += [
        Table(meas_data, colWidths=[2.8 * inch, 3.7 * inch], style=_table_style()),
        Spacer(1, 0.15 * inch),
    ]

    # Embed side-by-side site photo / sketch detection proof
    comp_img = _make_land_comparison_image(raw_image, annotated_image)
    if comp_img is not None:
        story += [
            Paragraph("AI Computer Vision Site Boundary Verification", cs["H3"]),
            comp_img,
            Spacer(1, 0.15 * inch),
        ]

    # Section 2: House Requirements
    story.append(Paragraph("2. Architectural Design Requirements", cs["H2"]))
    req_data = [
        ["Requirement Item", "Specification", "Requirement Item", "Specification"],
        ["House Type", requirements.get("house_type", "—"), "Road Facing", requirements.get("plot_facing", "North")],
        ["Floors", requirements.get("floors", "—"), "Parking Slot", "Yes" if requirements.get("parking") else "No"],
        ["Bedrooms", str(requirements.get("bedrooms", 1)), "Garden / Green", "Yes" if requirements.get("garden") else "No"],
        ["Bathrooms", str(requirements.get("bathrooms", 1)), "Internal Staircase", "Yes" if requirements.get("staircase") else "No"],
        ["Dining Room", "Yes" if requirements.get("dining_room") else "No", "Balcony Area", "Yes" if requirements.get("balcony") else "No"],
        ["Pooja Room", "Yes" if requirements.get("pooja_room") else "No", "Store Room", "Yes" if requirements.get("store_room") else "No"],
        ["Utility Area", "Yes" if requirements.get("utility") else "No", "Cost Quality Tier", c_tier_val],
    ]
    story += [
        Table(req_data, colWidths=[1.8 * inch, 1.45 * inch, 1.8 * inch, 1.45 * inch],
              style=_table_style()),
        Spacer(1, 0.15 * inch),
        PageBreak(),
    ]

    # ================================================================
    # PAGE 3 — Room Schedule & Design Validation Audit
    # ================================================================
    story.append(Paragraph("3. Room Schedule & Space Allocation", cs["H2"]))
    sched_data = [["Room / Space Name", "Width (ft)", "Length (ft)", "Carpet Area (sq.ft)", "Spatial Category"]]
    all_spaces = rooms + features
    for room in all_spaces:
        w = room.get("width", 0); h = room.get("length", 0); a = w * h
        sched_data.append([
            room.get("name", "?"),
            f"{w:.1f}", f"{h:.1f}", f"{a:.0f}",
            room.get("kind", "room").capitalize(),
        ])
    sched_data.append(["Total Built-up Area", "", "", f"{total_built_area:.0f}", "All Rooms"])

    t = Table(sched_data, colWidths=[2.3 * inch, 1.0 * inch, 1.0 * inch, 1.2 * inch, 1.0 * inch],
              style=_table_style())
    t_style = _table_style()
    t_style.add("FONTNAME", (0, len(sched_data)-1), (-1, len(sched_data)-1), "Helvetica-Bold")
    t_style.add("BACKGROUND", (0, len(sched_data)-1), (-1, len(sched_data)-1), colors.HexColor("#E8F0FE"))
    story += [t, Spacer(1, 0.2 * inch)]

    # Section 4: Design Validation & Algorithmic Score
    story.append(Paragraph("4. Algorithmic Design Validation & Feasibility Score", cs["H2"]))
    val = design.get("validation", {})
    valid_text = ("Non-Overlapping Geometry OK — Strict partition invariant preserved."
                  if val.get("valid") else
                  "Geometry issues detected — see issues list below.")
    conn_text  = ("Circulation & Reachability OK — All habitable rooms connect to central corridor/passage."
                  if val.get("connected", True) else
                  "Circulation Notice — check room access connectivity.")
    story += [
        Paragraph(valid_text, cs["Green"] if val.get("valid") else cs["Red"]),
        Paragraph(conn_text,  cs["Green"] if val.get("connected", True) else cs["Red"]),
        Spacer(1, 4),
    ]

    score_dict = design.get("score", {})
    if score_dict:
        story.append(
            Paragraph(f"Overall Architectural Rating: {score_dict.get('total', 0):.1f} / 100  "
                      f"(Grade: {score_dict.get('grade', 'A')})", cs["H3"])
        )
        breakdown = score_dict.get("breakdown", {})
        if breakdown:
            bd_data = [["Evaluation Criterion", "Points Awarded", "Max Points", "Evaluation Assessment"]]
            for criterion, v in breakdown.items():
                bd_data.append([criterion, f"{v['score']:.1f}", str(v['max']), v.get("note", "")])
            story.append(Table(bd_data,
                               colWidths=[1.8 * inch, 0.9 * inch, 0.8 * inch, 3.0 * inch],
                               style=_table_style()))

    story += [Spacer(1, 0.15 * inch), PageBreak()]

    # ================================================================
    # PAGE 4 — Vastu Shastra Compliance Audit
    # ================================================================
    v_score = vastu_data.get("score", 85.0)
    v_grade = vastu_data.get("grade", "Good")
    v_facing = vastu_data.get("plot_facing", requirements.get("plot_facing", "North"))

    story += [
        Paragraph("5. Vastu Shastra Compliance & Energy Flow Audit", cs["H2"]),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB"), spaceAfter=8),
        Paragraph(f"Plot Road Orientation: <b>{v_facing} Facing</b>  |  "
                  f"Vastu Score: <b>{v_score:.1f} / 100</b>  |  "
                  f"Compliance Rating: <b>{v_grade}</b>", cs["MetricBadge"]),
        Spacer(1, 8),
    ]

    audit_items = vastu_data.get("audit_items", [])
    if audit_items:
        v_table_data = [["Room / Space", "Placed Direction", "Ideal Vastu Zone", "Status", "Architectural Vastu Remedy / Tip"]]
        for item in audit_items:
            room_name = item.get("room", "")
            placed_zone = item.get("zone", "")
            ideal_zone = item.get("ideal_zone", item.get("ideal", "")).split(" or ")[0]
            status_clean = _clean_status(item.get("status", "Acceptable"))
            tip_text = item.get("tip", "")

            # Wrap in Paragraph for clean multiline text wrapping
            v_table_data.append([
                Paragraph(room_name, cs["TableBodyBold"]),
                Paragraph(placed_zone, cs["TableBody"]),
                Paragraph(ideal_zone, cs["TableBody"]),
                Paragraph(status_clean, cs["TableBody"]),
                Paragraph(tip_text, cs["TableBody"]),
            ])
        story.append(Table(v_table_data,
                           colWidths=[1.1 * inch, 1.2 * inch, 1.1 * inch, 0.9 * inch, 2.2 * inch],
                           style=_table_style()))
        Spacer(1, 8)

    recs = vastu_data.get("recommendations", [])
    if recs:
        story.append(Paragraph("Actionable Vastu Harmonization Recommendations:", cs["H3"]))
        for r in recs[:4]:
            story.append(Paragraph(f"• {_clean_status(r)}", cs["Body"]))

    story += [Spacer(1, 0.15 * inch), PageBreak()]

    # ================================================================
    # PAGE 5 — Construction Cost & Material Quantity Estimator (BOQ)
    # ================================================================
    c_lakhs = cost_data.get("total_cost_lakhs", cost_data.get("total_lakhs", 0.0))
    c_total = cost_data.get("total_cost_inr", 0.0)
    c_area  = cost_data.get("built_up_area_sqft", total_built_area)

    story += [
        Paragraph("6. Construction Cost & Material Quantity Estimator (BOQ)", cs["H2"]),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BBBBBB"), spaceAfter=8),
        Paragraph(f"Estimated Construction Budget: <b>Rs. {c_lakhs:.2f} Lakhs</b> (Rs. {c_total:,.0f})  |  "
                  f"Quality Tier: <b>{c_tier_val} (@ Rs. {c_rate_val:,.0f}/sq.ft)</b>  |  "
                  f"Covered Area: <b>{c_area:,.0f} sq.ft</b>", cs["MetricBadge"]),
        Spacer(1, 10),
        Paragraph("Milestone-Wise Project Cashflow Forecast", cs["H3"]),
    ]

    p_breakdown = cost_data.get("phase_breakdown", [])
    if p_breakdown:
        p_table = [["Construction Milestone Phase", "% Share", "Estimated Cost", "Scope Description"]]
        for p in p_breakdown:
            p_table.append([
                Paragraph(p.get("phase", ""), cs["TableBodyBold"]),
                Paragraph(f"{p.get('pct', 0):.1f}%", cs["TableBody"]),
                Paragraph(f"Rs. {p.get('cost_lakhs', 0):.2f} L", cs["TableBody"]),
                Paragraph(p.get("description", ""), cs["TableBody"]),
            ])
        story.append(Table(p_table,
                           colWidths=[1.6 * inch, 0.7 * inch, 1.1 * inch, 3.1 * inch],
                           style=_table_style()))
        Spacer(1, 10)

    # Material Takeoff Table
    m_dict = cost_data.get("materials", cost_data.get("material_takeoff", {}))
    if m_dict:
        story.append(Paragraph("Primary Material Takeoff (Bill of Quantities)", cs["H3"]))
        m_table = [["Construction Material", "Estimated Quantity", "Unit of Measure", "Application & Specs"]]
        for mat_key, m_info in m_dict.items():
            name_val = m_info.get("name", mat_key)
            qty_val = f"{m_info.get('quantity', 0):,}"
            unit_val = m_info.get("unit", "")
            note_val = m_info.get("note", m_info.get("notes", ""))
            m_table.append([
                Paragraph(name_val, cs["TableBodyBold"]),
                Paragraph(qty_val, cs["TableBody"]),
                Paragraph(unit_val, cs["TableBody"]),
                Paragraph(note_val, cs["TableBody"]),
            ])
        story.append(Table(m_table,
                           colWidths=[1.8 * inch, 1.1 * inch, 1.0 * inch, 2.6 * inch],
                           style=_table_style()))
        Spacer(1, 6)
        story.append(Paragraph("Note: Actual BOQ may vary based on soil test bearing capacity and local market commodity rates.", cs["Small"]))

    story += [Spacer(1, 0.15 * inch), PageBreak()]

    # ================================================================
    # PAGE 6 — 2D Concept Floor Plan
    # ================================================================
    story.append(Paragraph("7. 2D Architectural Concept Floor Plan", cs["H2"]))
    try:
        from src.visualization.render_2d import create_2d_floorplan
        fig_2d = create_2d_floorplan(rooms, plot_width, plot_length,
                                     features, design.get("design_name", ""))
        story.append(_fig_to_image(fig_2d, 6.5 * inch, 5.8 * inch))
    except Exception as exc:
        story.append(Paragraph(f"[2D plan could not be rendered: {exc}]", cs["Small"]))

    story += [Spacer(1, 0.1 * inch), PageBreak()]

    # ================================================================
    # PAGE 7 — 3D Schematic Visualization
    # ================================================================
    story.append(Paragraph("8. 3D Architectural Schematic Model", cs["H2"]))
    rendered_3d = False
    try:
        from src.visualization.render_3d import create_3d_view
        fig_3d = create_3d_view(rooms, plot_width, plot_length, features,
                                design.get("design_name", ""))
        img_bytes = fig_3d.to_image(format="png", width=950, height=720, scale=2)
        buf3d = BytesIO(img_bytes)
        story.append(Image(buf3d, width=6.5 * inch, height=5.2 * inch, kind="proportional"))
        rendered_3d = True
    except Exception:
        rendered_3d = False

    if not rendered_3d:
        try:
            from src.visualization.render_3d import create_matplotlib_3d_figure
            fig_3d_mpl = create_matplotlib_3d_figure(
                rooms, plot_width, plot_length, features,
                design.get("design_name", "")
            )
            story.append(_fig_to_image(fig_3d_mpl, width=6.5 * inch, height=5.2 * inch))
            rendered_3d = True
        except Exception as exc:
            story.append(Paragraph(f"[3D schematic could not be rendered: {exc}]", cs["Small"]))

    story += [Spacer(1, 0.15 * inch), PageBreak()]

    # ================================================================
    # PAGE 8 — Commercial Disclaimer & Specifications
    # ================================================================
    story += [
        Paragraph("9. Professional Disclaimer & Commercial Terms", cs["H2"]),
        Spacer(1, 8),
        Paragraph(
            f"This architectural concept report has been prepared by <b>{prepared_by}</b> "
            "using the Land2Home Computational Architecture Engine. It provides comprehensive space planning, "
            "Vastu Shastra energy alignment, and preliminary construction budgeting.",
            cs["Body"]),
        Spacer(1, 6),
        Paragraph("Important Terms & Conditions:", cs["Body"]),
        Spacer(1, 4),
    ]

    for item in [
        "This document is a conceptual space plan and preliminary architectural feasibility study.",
        "Prior to on-site construction, structural engineering drawings (RCC column/beam details, soil bearing capacity, foundation depths) must be prepared and stamped by a licensed structural engineer.",
        "Local Municipal Corporation bye-laws, Floor Area Ratio (FAR/FSI), ground coverage limits, fire safety codes, and mandatory setbacks must be verified with local planning authorities.",
        "Plumbing, electrical conduit routes, HVAC, and internal drainage (MEP) schematics must be developed according to National Building Code (NBC) standards.",
        "Construction budget estimates are based on current regional standard rates and prevailing material indices; actual contractor tenders may vary.",
        "Land boundaries derived from aerial captures or sketches should be confirmed through an on-ground physical total station survey before registry or digging.",
    ]:
        story.append(Paragraph(f"• {item}", cs["Disclaimer"]))
        story.append(Spacer(1, 3))

    story += [
        Spacer(1, 24),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#1A3A5C")),
        Spacer(1, 8),
        Paragraph(
            f"Generated by {prepared_by} | www.land2home.ai | Commercial Architectural Dossier | "
            f"{datetime.datetime.now().strftime('%d %b %Y, %H:%M')}",
            ParagraphStyle("footer", parent=ss["Normal"], fontSize=7.5,
                           textColor=colors.HexColor("#7F8C8D"), alignment=TA_CENTER)),
    ]

    doc.build(story)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _info_table(rows: list[list[str]], ss) -> Table:
    """Styled 2-column key-value table for executive cover sheet."""
    style = TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",   (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9.0),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#D0D7DE")),
        ("PADDING",    (0,0), (-1,-1), 5.5),
        ("ALIGN",      (0,0), (0,-1),  "RIGHT"),
        ("ALIGN",      (1,0), (1,-1),  "LEFT"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1),
         [colors.white, colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAF0FB")),
        ("TOPPADDING", (0,0), (-1,0), 7),
        ("BOTTOMPADDING", (0,-1), (-1,-1), 7),
    ])
    return Table(rows, colWidths=[2.2 * inch, 3.8 * inch], style=style,
                 hAlign="CENTER")
