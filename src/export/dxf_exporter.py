"""
Land2Home — AutoCAD DXF Floor Plan Exporter
============================================

Exports generated 2D architectural concept plans to industry-standard
AutoCAD DXF format for architects, civil engineers, and drafting teams.

Architectural rules (matching render_2d.py)
-------------------------------------------
1. Door openings are rerouted at export time to the wall that actually touches
   a circulation space (Passage, Corridor, Living, Dining). They are NEVER
   placed through another bedroom or bathroom wall.
2. Windows are suppressed on shared interior walls that also carry a door,
   and must maintain >= 1.5 ft clearance from any door edge on exterior walls.
3. Each door is exported as: (a) a gap line on the layer DOOR_GAPS,
   (b) the door leaf on layer DOORS, and (c) a quarter-circle swing arc on
   layer DOOR_SWINGS — matching standard architectural drawing convention.
"""

from __future__ import annotations
import io
import math

# Import shared adjacency helpers from the 2D renderer
# (keeps a single source of truth for circulation logic)
from src.visualization.render_2d import (
    _best_door_wall,
    _window_is_safe,
    _wall_neighbor,
    _opposite_wall,
)


# ---------------------------------------------------------------------------
# Door geometry helpers
# ---------------------------------------------------------------------------

def _door_geometry(item: dict, door: dict, all_items: list[dict]):
    """
    Return (wall, hx, hy, leaf_p1, leaf_p2, arc_center, arc_radius,
            arc_start_deg, arc_end_deg) for a door after adjacency rerouting.
    All coordinates are in feet (the DXF model-space unit).
    """
    x, y, w, h = item["x"], item["y"], item["width"], item["length"]
    pref = door.get("wall", "south")
    off  = door.get("offset_pct", 0.3)
    dw   = door.get("width_ft", 3.0)

    wall = _best_door_wall(item, pref, all_items)

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    if wall == "south":
        hx = clamp(x + w * off, x, x + w - dw)
        hy = y
        p1, p2 = (hx, hy), (hx + dw, hy)
        arc_c  = (hx, hy)
        a1, a2 = 0.0, 90.0

    elif wall == "north":
        hx = clamp(x + w * off, x, x + w - dw)
        hy = y + h
        # Flip hinge to right side when too close to right edge
        if hx + dw > x + w:
            hx = clamp(x + w - dw, x, x + w - dw)
            arc_c = (hx + dw, hy)
            a1, a2 = 270.0, 360.0
        else:
            arc_c = (hx, hy)
            a1, a2 = 180.0, 270.0
        p1, p2 = (hx, hy), (hx + dw, hy)

    elif wall == "west":
        hx = x
        hy = clamp(y + h * off, y, y + h - dw)
        p1, p2 = (hx, hy), (hx, hy + dw)
        arc_c  = (hx, hy)
        a1, a2 = 270.0, 360.0

    else:  # east
        hx = x + w
        hy = clamp(y + h * off, y, y + h - dw)
        p1, p2 = (hx, hy), (hx, hy + dw)
        arc_c  = (hx, hy)
        a1, a2 = 90.0, 180.0

    return wall, p1, p2, arc_c, dw, a1, a2


def _window_geometry(item: dict, win: dict, all_items: list[dict]):
    """
    Return (wall, p1, p2) for a window after collision/interior-wall safety check,
    or None if the window should be suppressed.
    """
    x, y, w, h = item["x"], item["y"], item["width"], item["length"]
    wall   = win.get("wall", "south")
    off    = win.get("offset_pct", 0.5)
    ww     = min(win.get("width_ft", 3.5), 5.0)

    if not _window_is_safe(item, wall, off, ww, all_items):
        alt = _opposite_wall(wall)
        if (_wall_neighbor(item, alt, all_items) is None
                and _window_is_safe(item, alt, off, ww, all_items)):
            wall = alt
        else:
            return None   # suppress

    if wall in ("south", "north"):
        wy = y if wall == "south" else y + h
        wx = x + w * off
        p1 = (wx - ww / 2, wy)
        p2 = (wx + ww / 2, wy)
    else:
        wx = x if wall == "west" else x + w
        wy = y + h * off
        p1 = (wx, wy - ww / 2)
        p2 = (wx, wy + ww / 2)

    return p1, p2


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def export_layout_to_dxf(
    rooms: list[dict],
    plot_width: float,
    plot_length: float,
    features: list[dict] | None = None,
    design_name: str = "",
    client_name: str = "",
    prepared_by: str = ""
) -> bytes:
    """
    Generate an AutoCAD DXF R2010 document from the layout rooms.

    Returns:
        bytes representing the .dxf file content.
    """
    features = features or []
    all_items = features + rooms

    try:
        import ezdxf
        import ezdxf.enums

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        # Standard architectural layers
        doc.layers.add(name="PLOT_BOUNDARY",  color=7,  lineweight=50)
        doc.layers.add(name="WALLS",          color=1,  lineweight=35)
        doc.layers.add(name="ROOM_NAMES",     color=3)
        doc.layers.add(name="ROOM_DIMENSIONS",color=2)
        doc.layers.add(name="DOOR_GAPS",      color=7)   # white gap on wall
        doc.layers.add(name="DOORS",          color=4,  lineweight=18)
        doc.layers.add(name="DOOR_SWINGS",    color=4,  lineweight=9)
        doc.layers.add(name="WINDOWS",        color=5,  lineweight=18)
        doc.layers.add(name="AMENITIES",      color=9)

        # Outer plot boundary
        plot_pts = [
            (0, 0), (plot_width, 0),
            (plot_width, plot_length), (0, plot_length), (0, 0),
        ]
        msp.add_lwpolyline(plot_pts, dxfattribs={"layer": "PLOT_BOUNDARY", "closed": True})

        # Rooms + features
        for item in all_items:
            x, y, w, h = item["x"], item["y"], item["width"], item["length"]
            is_amenity = item.get("kind") == "amenity"
            layer = "AMENITIES" if is_amenity else "WALLS"

            pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
            msp.add_lwpolyline(pts, dxfattribs={"layer": layer, "closed": True})

            # Text labels
            cx, cy = x + w / 2, y + h / 2
            area = w * h
            msp.add_text(
                item["name"],
                dxfattribs={"layer": "ROOM_NAMES", "height": min(w, h) * 0.08 + 0.6}
            ).set_placement(
                (cx, cy + h * 0.08),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
            msp.add_text(
                f"{w:.1f} x {h:.1f} ft ({area:.0f} sqft)",
                dxfattribs={"layer": "ROOM_DIMENSIONS", "height": min(w, h) * 0.06 + 0.45}
            ).set_placement(
                (cx, cy - h * 0.12),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )

            # --- Doors (adjacency-aware) ---
            for door in item.get("doors", []):
                wall, p1, p2, arc_c, dw, a1, a2 = _door_geometry(item, door, all_items)

                # 1) White gap line (erases wall at door position on DOOR_GAPS layer)
                msp.add_line(p1, p2, dxfattribs={"layer": "DOOR_GAPS"})

                # 2) Door leaf line
                msp.add_line(p1, p2, dxfattribs={"layer": "DOORS"})

                # 3) Quarter-circle swing arc
                msp.add_arc(
                    center=arc_c,
                    radius=dw,
                    start_angle=a1,
                    end_angle=a2,
                    dxfattribs={"layer": "DOOR_SWINGS"}
                )

            # --- Windows (collision-safe) ---
            for win in item.get("windows", []):
                result = _window_geometry(item, win, all_items)
                if result is None:
                    continue   # suppressed by collision check
                wp1, wp2 = result
                msp.add_line(wp1, wp2, dxfattribs={"layer": "WINDOWS"})

        # Title block note
        info_str = (
            f"Land2Home AI Studio | {design_name} | "
            f"{plot_width:.0f}x{plot_length:.0f} ft"
        )
        if client_name:
            info_str += f" | Client: {client_name}"
        if prepared_by:
            info_str += f" | By: {prepared_by}"

        msp.add_text(
            info_str,
            dxfattribs={"layer": "ROOM_NAMES", "height": 1.2}
        ).set_placement(
            (0, plot_length + 2.0),
            align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT
        )

        out = io.StringIO()
        doc.write(out)
        return out.getvalue().encode("utf-8")

    except Exception:
        # Minimal pure-ASCII DXF R12 fallback (zero dependencies)
        return _pure_python_dxf_fallback(all_items, plot_width, plot_length,
                                         design_name)


# ---------------------------------------------------------------------------
# Pure-Python ASCII DXF R12 fallback
# ---------------------------------------------------------------------------

def _pure_python_dxf_fallback(items: list[dict], W: float, L: float,
                               design_name: str) -> bytes:
    """
    Zero-dependency DXF R12 generator.
    Includes adjacency-aware doors and collision-safe windows.
    """
    lines = ["0", "SECTION", "2", "ENTITIES"]

    def _line(p1, p2, layer):
        return ["0", "LINE", "8", layer,
                "10", str(round(p1[0], 4)), "20", str(round(p1[1], 4)), "30", "0.0",
                "11", str(round(p2[0], 4)), "21", str(round(p2[1], 4)), "31", "0.0"]

    def _arc(cx, cy, radius, a1, a2, layer):
        return ["0", "ARC", "8", layer,
                "10", str(round(cx, 4)), "20", str(round(cy, 4)), "30", "0.0",
                "40", str(round(radius, 4)),
                "50", str(round(a1, 2)), "51", str(round(a2, 2))]

    # Plot boundary
    for p1, p2 in [((0, 0), (W, 0)), ((W, 0), (W, L)),
                   ((W, L), (0, L)), ((0, L), (0, 0))]:
        lines.extend(_line(p1, p2, "PLOT_BOUNDARY"))

    for item in items:
        x, y, w, h = item["x"], item["y"], item["width"], item["length"]
        # Wall box
        for p1, p2 in [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                       ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]:
            lines.extend(_line(p1, p2, "WALLS"))

        # Room label
        lines.extend(["0", "TEXT", "8", "ROOM_NAMES",
                       "10", str(x + w / 2), "20", str(y + h / 2), "30", "0.0",
                       "40", "1.0", "1", item["name"]])

        # Doors (adjacency-aware)
        for door in item.get("doors", []):
            wall, p1, p2, arc_c, dw, a1, a2 = _door_geometry(item, door, items)
            lines.extend(_line(p1, p2, "DOORS"))
            lines.extend(_arc(arc_c[0], arc_c[1], dw, a1, a2, "DOOR_SWINGS"))

        # Windows (collision-safe)
        for win in item.get("windows", []):
            result = _window_geometry(item, win, items)
            if result is None:
                continue
            wp1, wp2 = result
            lines.extend(_line(wp1, wp2, "WINDOWS"))

    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines).encode("utf-8")
