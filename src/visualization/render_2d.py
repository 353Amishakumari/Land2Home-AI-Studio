"""
Land2Home — Professional 2D Floor-Plan Renderer
================================================

Produces an architectural concept drawing with:
  • Colour-coded rooms with name / dimension / area labels
  • Door symbols (gap + quarter-circle swing arc)
  • Window symbols (triple parallel lines on walls)
  • Schematic furniture (beds, sofa, dining table, kitchen counter, WC/basin)
  • North arrow, road label, main-entrance arrow
  • Overall plot dimension annotations
  • Room colour legend
"""

from __future__ import annotations
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyArrowPatch, Arc, Wedge
from matplotlib.lines import Line2D

from src.visualization.colors import get_room_color, LEGEND_ENTRIES, ROOM_EDGE_COLOR, PLOT_EDGE_COLOR


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def create_2d_floorplan(rooms: list[dict],
                         plot_width: float,
                         plot_length: float,
                         features: list[dict] | None = None,
                         design_name: str = "") -> plt.Figure:
    """
    Render a professional-quality 2D architectural concept plan.

    Args:
        rooms:        list of room dicts from generate_all_designs().
        plot_width:   total plot width in feet (east-west).
        plot_length:  total plot length in feet (south-north).
        features:     parking / garden amenity dicts.
        design_name:  shown in the figure title.

    Returns:
        matplotlib Figure object (caller must call st.pyplot() or fig.savefig()).
    """
    features = features or []
    all_items = features + rooms

    fig, ax = plt.subplots(figsize=(13, 11))
    ax.set_aspect("equal")
    ax.set_facecolor("#F8F8F4")
    fig.patch.set_facecolor("#F8F8F4")

    # ---- Draw rooms and features ----
    for item in all_items:
        _draw_room(ax, item)

    # ---- Draw doors ----
    for item in all_items:
        for door in item.get("doors", []):
            _draw_door(ax, item, door)

    # ---- Draw windows ----
    for item in all_items:
        for win in item.get("windows", []):
            _draw_window(ax, item, win)

    # ---- Draw furniture ----
    for item in rooms:
        if item.get("furniture"):
            _draw_furniture(ax, item)

    # ---- Plot boundary (drawn last so it sits on top) ----
    ax.add_patch(Rectangle((0, 0), plot_width, plot_length,
                            fill=False, edgecolor=PLOT_EDGE_COLOR, linewidth=3.0, zorder=10))

    # ---- Annotations ----
    _draw_main_entrance(ax, rooms, features, plot_width)
    _draw_dimension_annotations(ax, plot_width, plot_length)
    _draw_north_arrow(ax, plot_width, plot_length)
    _draw_road_label(ax, plot_width)
    _draw_legend(ax, plot_width, plot_length)

    # ---- Axes formatting ----
    pad = max(plot_width, plot_length) * 0.08
    ax.set_xlim(-pad * 1.5, plot_width + max(plot_width, plot_length) * 0.42)
    ax.set_ylim(-pad * 1.4, plot_length + pad * 1.2)
    ax.axis("off")

    title = f"Land2Home AI Studio — 2D Concept Floor Plan  |  {plot_width:.0f} × {plot_length:.0f} ft"
    if design_name:
        title += f"\n{design_name}"
    ax.set_title(title, fontsize=11, fontweight="bold", pad=12, loc="left")

    fig.tight_layout(pad=1.0)
    return fig


# ---------------------------------------------------------------------------
# Room box + label
# ---------------------------------------------------------------------------

def _draw_room(ax: plt.Axes, item: dict) -> None:
    x, y, w, h = item["x"], item["y"], item["width"], item["length"]
    color  = item.get("color", get_room_color(item["name"]))
    is_amenity = item.get("kind") in ("amenity",)

    edge_color = "#27AE60" if "garden" in item["name"].lower() else \
                 "#626567" if "parking" in item["name"].lower() else ROOM_EDGE_COLOR
    lw = 1.5 if is_amenity else 2.0

    ax.add_patch(Rectangle((x, y), w, h,
                            facecolor=color, edgecolor=edge_color,
                            linewidth=lw, alpha=0.90, zorder=2))

    # Label — multi-line: name / dims / area
    cx, cy = x + w / 2, y + h / 2
    area   = w * h
    name   = item["name"]
    dims   = f"{w:.1f} × {h:.1f} ft"
    area_s = f"{area:.0f} sq.ft"

    # Font size scales with room size (clamped 6–9 pt)
    fs_name = _clamp(min(w, h) * 0.55, 6.0, 9.0)
    fs_dim  = _clamp(fs_name * 0.78, 5.0, 7.5)

    ax.text(cx, cy + h * 0.10, name,
            ha="center", va="center", fontsize=fs_name, fontweight="bold",
            color="#1A1A1A", zorder=5, clip_on=True)
    ax.text(cx, cy - h * 0.08, dims,
            ha="center", va="center", fontsize=fs_dim, color="#333333",
            zorder=5, clip_on=True)
    ax.text(cx, cy - h * 0.24, area_s,
            ha="center", va="center", fontsize=fs_dim * 0.9, color="#555555",
            fontstyle="italic", zorder=5, clip_on=True)


# ---------------------------------------------------------------------------
# Door symbol
# ---------------------------------------------------------------------------

def _draw_door(ax: plt.Axes, room: dict, door: dict) -> None:
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    wall   = door.get("wall", "south")
    offset = door.get("offset_pct", 0.3)
    dw     = door.get("width_ft", 3.0)

    # Hinge position and swing arc angle
    if wall == "south":
        hx, hy = x + w * offset, y
        angle_start, angle_end = 0, 90
        line = [(hx, hy), (hx + dw, hy)]
        arc_center = (hx, hy)
    elif wall == "north":
        hx, hy = x + w * offset, y + h
        angle_start, angle_end = 270, 360
        line = [(hx, hy), (hx + dw, hy)]
        arc_center = (hx, hy)
    elif wall == "west":
        hx, hy = x, y + h * offset
        angle_start, angle_end = 270, 360
        line = [(hx, hy), (hx, hy + dw)]
        arc_center = (hx, hy)
    else:  # east
        hx, hy = x + w, y + h * offset
        angle_start, angle_end = 90, 180
        line = [(hx, hy), (hx, hy + dw)]
        arc_center = (hx, hy)

    # White gap (erases wall line at door position)
    ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]],
            color="#F8F8F4", linewidth=4.5, zorder=6, solid_capstyle="butt")

    # Door leaf (thin line) and swing arc
    ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]],
            color="#8B4513", linewidth=1.0, zorder=7)

    arc = Arc(arc_center, dw * 2, dw * 2, angle=0,
              theta1=angle_start, theta2=angle_end,
              color="#8B4513", linewidth=0.8, linestyle="--", zorder=7)
    ax.add_patch(arc)


# ---------------------------------------------------------------------------
# Window symbol  (triple parallel lines)
# ---------------------------------------------------------------------------

def _draw_window(ax: plt.Axes, room: dict, win: dict) -> None:
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    wall   = win.get("wall", "south")
    offset = win.get("offset_pct", 0.5)
    ww     = min(win.get("width_ft", 3.5), 5.0)
    gap    = 0.18   # spacing between the 3 lines

    if wall in ("south", "north"):
        wy = y if wall == "south" else y + h
        wx = x + w * offset - ww / 2
        for i in range(3):
            g = (i - 1) * gap
            ax.plot([wx, wx + ww], [wy + g, wy + g],
                    color="#4A90D9", linewidth=1.0, zorder=8, solid_capstyle="round")
    else:  # east / west
        wx = x if wall == "west" else x + w
        wy = y + h * offset - ww / 2
        for i in range(3):
            g = (i - 1) * gap
            ax.plot([wx + g, wx + g], [wy, wy + ww],
                    color="#4A90D9", linewidth=1.0, zorder=8, solid_capstyle="round")


# ---------------------------------------------------------------------------
# Schematic furniture
# ---------------------------------------------------------------------------

def _draw_furniture(ax: plt.Axes, room: dict) -> None:
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    kind = room.get("furniture", "")
    if not kind:
        return

    if kind == "bed":
        _draw_bed(ax, x, y, w, h)
    elif kind == "sofa":
        _draw_sofa(ax, x, y, w, h)
    elif kind == "dining":
        _draw_dining(ax, x, y, w, h)
    elif kind == "kitchen":
        _draw_kitchen(ax, x, y, w, h)
    elif kind == "bathroom":
        _draw_bathroom(ax, x, y, w, h)


def _draw_bed(ax, rx, ry, rw, rh):
    bw = rw * 0.70; bh = rh * 0.55
    bx = rx + (rw - bw) / 2; by = ry + rh * 0.25
    # Bed frame
    ax.add_patch(Rectangle((bx, by), bw, bh,
                            fc="#B0C4DE", ec="#4682B4", lw=0.8, alpha=0.7, zorder=3))
    # Pillow band
    ax.add_patch(Rectangle((bx + 0.3, by + bh * 0.70), bw - 0.6, bh * 0.25,
                            fc="white", ec="#888", lw=0.5, alpha=0.8, zorder=4))


def _draw_sofa(ax, rx, ry, rw, rh):
    # Sofa along south wall
    sw = min(rw * 0.65, 10.0); sh = min(rh * 0.28, 4.0)
    sx = rx + (rw - sw) / 2; sy = ry + rh * 0.08
    ax.add_patch(Rectangle((sx, sy), sw, sh,
                            fc="#D2B48C", ec="#8B4513", lw=0.8, alpha=0.7, zorder=3))
    # Sofa back
    ax.add_patch(Rectangle((sx, sy + sh * 0.70), sw, sh * 0.30,
                            fc="#C4A882", ec="#8B4513", lw=0.5, alpha=0.8, zorder=4))
    # Coffee table
    ctw = sw * 0.40; cth = rh * 0.14
    ctx = rx + (rw - ctw) / 2; cty = sy + sh + rh * 0.06
    ax.add_patch(Rectangle((ctx, cty), ctw, cth,
                            fc="#DEB887", ec="#8B4513", lw=0.6, alpha=0.65, zorder=3))


def _draw_dining(ax, rx, ry, rw, rh):
    # Table + chairs
    tw = min(rw * 0.55, 7.0); th = min(rh * 0.55, 5.0)
    tx = rx + (rw - tw) / 2; ty = ry + (rh - th) / 2
    ax.add_patch(Rectangle((tx, ty), tw, th,
                            fc="#F5DEB3", ec="#8B4513", lw=0.8, alpha=0.80, zorder=3))
    # Chairs (circles)
    r_chair = min(0.9, tw * 0.09)
    for cx_, cy_ in [
        (tx + tw / 2, ty - r_chair * 1.5),
        (tx + tw / 2, ty + th + r_chair * 1.5),
        (tx - r_chair * 1.5, ty + th / 2),
        (tx + tw + r_chair * 1.5, ty + th / 2),
    ]:
        ax.add_patch(plt.Circle((cx_, cy_), r_chair,
                                fc="#C49A6C", ec="#8B4513", lw=0.5, alpha=0.70, zorder=3))


def _draw_kitchen(ax, rx, ry, rw, rh):
    # Counter along south and west walls
    cth = min(rh * 0.18, 2.0)
    # South counter
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3), rw - 0.6, cth,
                            fc="#C8C8C8", ec="#888", lw=0.6, alpha=0.80, zorder=3))
    # West counter
    ctw_ = min(rw * 0.18, 2.0)
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3 + cth), ctw_, rh - cth - 0.6,
                            fc="#C8C8C8", ec="#888", lw=0.6, alpha=0.80, zorder=3))
    # Sink (circle in south-west corner)
    sink_r = min(0.7, cth * 0.45)
    ax.add_patch(plt.Circle((rx + ctw_ * 0.5 + 0.3, ry + 0.3 + cth * 0.5),
                             sink_r, fc="white", ec="#555", lw=0.6, zorder=4))


def _draw_bathroom(ax, rx, ry, rw, rh):
    # WC (south-west)
    wc_w = min(rw * 0.45, 2.0); wc_h = min(rh * 0.42, 2.5)
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3), wc_w, wc_h,
                            fc="#E0F7FA", ec="#555", lw=0.6, alpha=0.85, zorder=3))
    # Basin (east)
    b_w = min(rw * 0.38, 1.6); b_h = min(rh * 0.30, 1.6)
    ax.add_patch(Rectangle((rx + rw - b_w - 0.3, ry + 0.3), b_w, b_h,
                            fc="#E0F7FA", ec="#555", lw=0.6, alpha=0.85, zorder=3))


# ---------------------------------------------------------------------------
# North arrow
# ---------------------------------------------------------------------------

def _draw_north_arrow(ax: plt.Axes, W: float, L: float) -> None:
    px = W + max(W, L) * 0.065
    py = L * 0.75
    arrow_len = max(W, L) * 0.07
    ax.annotate("", xy=(px, py + arrow_len), xytext=(px, py),
                arrowprops=dict(arrowstyle="-|>", color="#1A1A1A",
                                lw=1.6, mutation_scale=16),
                zorder=12)
    ax.text(px, py + arrow_len + 0.5, "N", ha="center", va="bottom",
            fontsize=10, fontweight="bold", color="#1A1A1A", zorder=12)


# ---------------------------------------------------------------------------
# Road label
# ---------------------------------------------------------------------------

def _draw_road_label(ax: plt.Axes, W: float) -> None:
    ax.annotate("ROAD  ⟶", xy=(W * 0.5, -0.6), xytext=(W * 0.5, -0.6),
                ha="center", va="top", fontsize=9, color="#C0392B",
                fontweight="bold", zorder=12)


# ---------------------------------------------------------------------------
# Main entrance arrow
# ---------------------------------------------------------------------------

def _draw_main_entrance(ax: plt.Axes, rooms: list[dict],
                         features: list[dict], W: float) -> None:
    # Find first south-facing door in rooms
    entrance_x = W * 0.30
    for item in rooms:
        for door in item.get("doors", []):
            if door.get("wall") == "south":
                entrance_x = item["x"] + item["width"] * door.get("offset_pct", 0.3)
                break

    ax.annotate("ENTRANCE", xy=(entrance_x, -0.1),
                xytext=(entrance_x, -2.8),
                fontsize=8, fontweight="bold", color="#E74C3C", ha="center",
                arrowprops=dict(arrowstyle="-|>", color="#E74C3C", lw=1.5,
                                mutation_scale=14),
                zorder=12)


# ---------------------------------------------------------------------------
# Dimension annotations (four sides of plot)
# ---------------------------------------------------------------------------

def _draw_dimension_annotations(ax: plt.Axes, W: float, L: float) -> None:
    off = max(W, L) * 0.04
    kw  = dict(ha="center", va="center", fontsize=8.5, color="#2C3E50",
               fontweight="semibold", zorder=12)
    # South
    ax.text(W / 2, -off, f"← {W:.0f} ft →", **kw)
    # North
    ax.text(W / 2, L + off, f"← {W:.0f} ft →", **kw)
    # West
    ax.text(-off * 1.5, L / 2, f"← {L:.0f} ft →",
            rotation=90, **kw)
    # East
    ax.text(W + off * 1.5, L / 2, f"← {L:.0f} ft →",
            rotation=90, **kw)


# ---------------------------------------------------------------------------
# Colour legend
# ---------------------------------------------------------------------------

def _draw_legend(ax: plt.Axes, W: float, L: float) -> None:
    handles = [
        mpatches.Patch(facecolor=color, edgecolor="#555", linewidth=0.6, label=label)
        for label, color in LEGEND_ENTRIES
    ]
    legend = ax.legend(handles=handles, title="Space Color Guide",
                       loc="lower left",
                       bbox_to_anchor=(1.01, 0.0),
                       fontsize=8.0, title_fontsize=9.0,
                       frameon=True, edgecolor="#B0BEC5", facecolor="#FFFFFF",
                       ncol=1)
    legend.get_frame().set_alpha(0.95)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
