"""
Land2Home — AutoCAD DXF Floor Plan Exporter
============================================

Exports generated 2D architectural concept plans to industry-standard
AutoCAD DXF format for architects, civil engineers, and drafting teams.
"""

from __future__ import annotations
import io


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

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        # Setup standard architectural layers
        doc.layers.add(name="PLOT_BOUNDARY", color=7, lineweight=50)
        doc.layers.add(name="WALLS", color=1, lineweight=35)
        doc.layers.add(name="ROOM_NAMES", color=3)
        doc.layers.add(name="ROOM_DIMENSIONS", color=2)
        doc.layers.add(name="DOORS", color=4)
        doc.layers.add(name="WINDOWS", color=5)
        doc.layers.add(name="AMENITIES", color=9)

        # Draw outer plot boundary
        plot_pts = [(0, 0), (plot_width, 0), (plot_width, plot_length), (0, plot_length), (0, 0)]
        msp.add_lwpolyline(plot_pts, dxfattribs={"layer": "PLOT_BOUNDARY", "closed": True})

        # Draw rooms and features
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
                f"{item['name']}",
                dxfattribs={"layer": "ROOM_NAMES", "height": min(w, h) * 0.08 + 0.6}
            ).set_placement((cx, cy + h * 0.08), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

            msp.add_text(
                f"{w:.1f} x {h:.1f} ft ({area:.0f} sqft)",
                dxfattribs={"layer": "ROOM_DIMENSIONS", "height": min(w, h) * 0.06 + 0.45}
            ).set_placement((cx, cy - h * 0.12), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

            # Doors
            for door in item.get("doors", []):
                wall = door.get("wall", "south")
                off = door.get("offset_pct", 0.3)
                dw = door.get("width_ft", 3.0)
                if wall == "south":
                    p1 = (x + w * off, y)
                    p2 = (x + w * off + dw, y)
                elif wall == "north":
                    p1 = (x + w * off, y + h)
                    p2 = (x + w * off + dw, y + h)
                elif wall == "west":
                    p1 = (x, y + h * off)
                    p2 = (x, y + h * off + dw)
                else:
                    p1 = (x + w, y + h * off)
                    p2 = (x + w, y + h * off + dw)
                msp.add_line(p1, p2, dxfattribs={"layer": "DOORS"})

            # Windows
            for win in item.get("windows", []):
                wall = win.get("wall", "south")
                off = win.get("offset_pct", 0.5)
                ww = win.get("width_ft", 3.5)
                if wall in ("south", "north"):
                    wy = y if wall == "south" else y + h
                    p1 = (x + w * off - ww / 2, wy)
                    p2 = (x + w * off + ww / 2, wy)
                else:
                    wx = x if wall == "west" else x + w
                    p1 = (wx, y + h * off - ww / 2)
                    p2 = (wx, y + h * off + ww / 2)
                msp.add_line(p1, p2, dxfattribs={"layer": "WINDOWS"})

        # Header title note in model space
        info_str = f"Land2Home AI Studio | {design_name} | {plot_width:.0f}x{plot_length:.0f} ft"
        if client_name:
            info_str += f" | Client: {client_name}"
        msp.add_text(info_str, dxfattribs={"layer": "ROOM_NAMES", "height": 1.2}).set_placement(
            (0, plot_length + 2.0), align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT
        )

        out = io.StringIO()
        doc.write(out)
        return out.getvalue().encode("utf-8")

    except Exception:
        # Minimal pure ASCII DXF R12 fallback
        return _pure_python_dxf_fallback(all_items, plot_width, plot_length, design_name)


def _pure_python_dxf_fallback(items: list[dict], W: float, L: float, design_name: str) -> bytes:
    """Pure Python ASCII DXF generator as a zero-dependency fallback."""
    lines = [
        "0", "SECTION",
        "2", "ENTITIES",
    ]
    # Plot boundary
    for p1, p2 in [((0, 0), (W, 0)), ((W, 0), (W, L)), ((W, L), (0, L)), ((0, L), (0, 0))]:
        lines.extend(["0", "LINE", "8", "PLOT_BOUNDARY",
                      "10", str(p1[0]), "20", str(p1[1]), "30", "0.0",
                      "11", str(p2[0]), "21", str(p2[1]), "31", "0.0"])

    for item in items:
        x, y, w, h = item["x"], item["y"], item["width"], item["length"]
        # 4 lines per box
        box_pts = [((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                   ((x + w, y + h), (x, y + h)), ((x, y + h), (x, y))]
        for p1, p2 in box_pts:
            lines.extend(["0", "LINE", "8", "WALLS",
                          "10", str(p1[0]), "20", str(p1[1]), "30", "0.0",
                          "11", str(p2[0]), "21", str(p2[1]), "31", "0.0"])

        # Room text
        lines.extend(["0", "TEXT", "8", "ROOM_NAMES",
                      "10", str(x + w / 2), "20", str(y + h / 2), "30", "0.0",
                      "40", "1.0", "1", item["name"]])

    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines).encode("utf-8")
