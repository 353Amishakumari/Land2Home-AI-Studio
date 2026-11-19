"""
Land2Home — Professional 2D Floor-Plan Renderer
================================================

Produces an architectural concept drawing with:
  • Colour-coded rooms with name / dimension / area labels
  • Door symbols (gap + quarter-circle swing arc) — adjacency-aware
  • Window symbols (triple parallel lines on walls) — collision-safe
  • Schematic furniture (beds, sofa, dining table, kitchen counter, WC/basin)
  • North arrow, road label, main-entrance arrow
  • Overall plot dimension annotations
  • Room colour legend

Architectural rules enforced at render time
-------------------------------------------
1. Bedroom / Kitchen / Store / Bathroom doors are rerouted to the wall that
   actually touches a circulation space (Passage, Corridor, Living, Dining).
   They are NEVER drawn through another bedroom or bathroom.
2. Windows are suppressed on shared interior walls that also carry a door,
   and must maintain ≥ 1.5 ft clearance from any door edge.
3. Door swing arcs are clamped to stay fully inside the host room's bounds.
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
# Circulation-space name fragments (doors should open toward these)
# ---------------------------------------------------------------------------
_CIRCULATION_KEYWORDS = (
    "passage", "corridor", "living", "dining", "hall", "lobby", "foyer",
    "open living",
)

_PRIVATE_KEYWORDS = (
    "bathroom", "toilet", "wc", "store", "staircase", "pooja", "mandir",
)


# ---------------------------------------------------------------------------
# Adjacency helpers
# ---------------------------------------------------------------------------

def _bbox(room: dict) -> tuple[float, float, float, float]:
    """Return (x0, y0, x1, y1) bounding box."""
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    return x, y, x + w, y + h


def _shared_wall(r1: dict, r2: dict, tol: float = 0.15) -> str | None:
    """
    Return the wall name of r1 that is shared with r2, or None.
    Two rooms share a wall when their bounding boxes touch along that edge
    and their transverse spans overlap by at least tol feet.
    """
    x0a, y0a, x1a, y1a = _bbox(r1)
    x0b, y0b, x1b, y1b = _bbox(r2)

    if abs(y0a - y1b) < tol and min(x1a, x1b) - max(x0a, x0b) >= tol:
        return "south"
    if abs(y1a - y0b) < tol and min(x1a, x1b) - max(x0a, x0b) >= tol:
        return "north"
    if abs(x0a - x1b) < tol and min(y1a, y1b) - max(y0a, y0b) >= tol:
        return "west"
    if abs(x1a - x0b) < tol and min(y1a, y1b) - max(y0a, y0b) >= tol:
        return "east"
    return None


def _is_circulation(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _CIRCULATION_KEYWORDS)


def _is_private(name: str) -> bool:
    low = name.lower()
    return any(k in low for k in _PRIVATE_KEYWORDS)


def _wall_neighbor(room: dict, wall: str, all_rooms: list[dict]) -> dict | None:
    """Return the first room sharing `wall` of `room`, or None."""
    for other in all_rooms:
        if other is room:
            continue
        if _shared_wall(room, other) == wall:
            return other
    return None


def _opposite_wall(wall: str) -> str:
    return {"south": "north", "north": "south", "east": "west", "west": "east"}[wall]


def _is_exterior_wall(room: dict, wall: str, plot_width: float, plot_length: float, all_items: list[dict]) -> bool:
    """
    Return True only if the wall is on the building exterior perimeter
    or faces an open amenity (Balcony, Garden, Parking, Road).
    Strictly returns False for any interior partition wall between enclosed rooms.
    """
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    tol = 0.25

    if wall == "west" and x <= tol:
        return True
    if wall == "east" and abs((x + w) - plot_width) <= tol:
        return True
    if wall == "south" and y <= tol:
        return True
    if wall == "north" and abs((y + h) - plot_length) <= tol:
        return True

    neighbor = _wall_neighbor(room, wall, all_items)
    if neighbor is None:
        return True

    nname = neighbor.get("name", "").lower()
    nkind = neighbor.get("kind", "")
    if nkind == "amenity" or "balcony" in nname or "garden" in nname or "parking" in nname:
        return True

    return False


# ---------------------------------------------------------------------------
# Door re-routing: pick the best wall for a door to open into circulation
# ---------------------------------------------------------------------------

def _best_door_wall(room: dict, preferred_wall: str, all_rooms: list[dict]) -> str:
    """
    Return the wall where the door should be drawn.

    Priority:
      1. Living Room South wall is ALWAYS Main Entrance from Parking/Road.
      2. Preferred wall if it faces a circulation space.
      3. Any other wall that faces a circulation space.
      4. Preferred wall if it faces a non-private room (never Pooja/Bathroom).
      5. Fall back to preferred wall.
    """
    rname = room.get("name", "").lower()

    # Living Room south wall door is the Main Entrance door — always keep south
    if "living" in rname and preferred_wall == "south":
        return "south"

    # Staircase: opens into Living or Passage / Corridor
    if "staircase" in rname:
        for w in [preferred_wall, "east", "west", "south", "north"]:
            nbr = _wall_neighbor(room, w, all_rooms)
            if nbr and _is_circulation(nbr.get("name", "")):
                return w
        return preferred_wall

    seen: set[str] = set()
    walls_order = []
    for w in [preferred_wall, "south", "north", "east", "west"]:
        if w not in seen:
            walls_order.append(w)
            seen.add(w)

    for wall in walls_order:
        neighbor = _wall_neighbor(room, wall, all_rooms)
        if neighbor is None and wall == preferred_wall:
            return wall          # exterior — keep as preferred
        if neighbor is not None:
            nname = neighbor.get("name", "").lower()
            if "pooja" in nname or "mandir" in nname:
                continue
            if _is_circulation(neighbor["name"]):
                return wall

    for wall in walls_order:
        neighbor = _wall_neighbor(room, wall, all_rooms)
        if neighbor is None:
            return wall
        nname = neighbor.get("name", "").lower()
        if "pooja" in nname or "mandir" in nname:
            continue
        if not _is_private(neighbor["name"]):
            return wall

    return preferred_wall


# ---------------------------------------------------------------------------
# Window safety check
# ---------------------------------------------------------------------------

def _window_is_safe(room: dict, wall: str, offset_pct: float,
                    win_width: float, all_rooms: list[dict],
                    clearance: float = 1.5) -> bool:
    """
    Return False when the window must be suppressed:
      a) Wall is shared with another room AND a door already sits on it.
      b) A door on the same exterior wall is within `clearance` feet.
    """
    rw, rh = room["width"], room["length"]
    span = rw if wall in ("south", "north") else rh

    w_start = span * offset_pct - win_width / 2
    w_end   = span * offset_pct + win_width / 2

    wall_is_interior = _wall_neighbor(room, wall, all_rooms) is not None

    for door in room.get("doors", []):
        if door.get("wall") != wall:
            continue
        d_start = span * door.get("offset_pct", 0.3)
        d_end   = d_start + door.get("width_ft", 3.0)

        if wall_is_interior:
            return False        # never put a window on a shared wall with a door

        gap_right = w_start - d_end
        gap_left  = d_start - w_end
        if gap_right < clearance and gap_left < clearance:
            return False

    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def create_2d_floorplan(rooms: list[dict],
                         plot_width: float,
                         plot_length: float,
                         features: list[dict] | None = None,
                         design_name: str = "",
                         plot_facing: str = "North") -> plt.Figure:
    """
    Render a professional-quality 2D architectural concept plan.

    Args:
        rooms:        list of room dicts from generate_all_designs().
        plot_width:   total plot width in feet (east-west).
        plot_length:  total plot length in feet (south-north).
        features:     parking / garden amenity dicts.
        design_name:  shown in the figure title.
        plot_facing:  orientation ("North", "South", "East", "West").

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

    # ---- Draw doors (adjacency-aware) ----
    for item in all_items:
        for door in item.get("doors", []):
            _draw_door(ax, item, door, all_items, plot_width, plot_length)

    # ---- Draw windows (collision-safe, strictly exterior) ----
    for item in all_items:
        for win in item.get("windows", []):
            _draw_window(ax, item, win, all_items, plot_width, plot_length)

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
    _draw_north_arrow(ax, plot_width, plot_length, plot_facing=plot_facing)
    _draw_road_label(ax, plot_width)
    _draw_legend(ax, plot_width, plot_length)

    # ---- Axes formatting ----
    pad = max(plot_width, plot_length) * 0.08
    ax.set_xlim(-pad * 1.5, plot_width + max(plot_width, plot_length) * 0.42)
    ymin = min(-5.0, -pad * 1.6)
    ymax = plot_length + max(pad * 1.2, 3.0)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")

    title = f"Land2Home AI Studio — 2D Concept Floor Plan  |  {plot_width:.0f} × {plot_length:.0f} ft"
    if design_name:
        title += f"\n{design_name}"
    ax.set_title(title, fontsize=11, fontweight="bold", pad=12, loc="left")

    fig.tight_layout(pad=1.0)
    return fig


# ---------------------------------------------------------------------------
# Staircase drawing (realistic treads + directional UP arrow)
# ---------------------------------------------------------------------------

def _draw_staircase(ax: plt.Axes, item: dict) -> None:
    """
    Draw realistic architectural staircase step treads (parallel lines +
    directional 'UP' arrow) inside the staircase boundary.
    """
    x, y, w, h = item["x"], item["y"], item["width"], item["length"]

    # Base background fill
    ax.add_patch(Rectangle((x, y), w, h,
                           facecolor="#F4EFEA", edgecolor=ROOM_EDGE_COLOR,
                           linewidth=2.0, zorder=2))

    if h >= w:
        # Steps run horizontally
        n_steps = max(7, min(14, int(h / 0.85)))
        dy = h / n_steps
        for i in range(1, n_steps):
            sy = y + i * dy
            ax.plot([x + 0.1, x + w - 0.1], [sy, sy],
                    color="#8C827A", linewidth=0.9, zorder=3)

        mid_x = x + w * 0.5
        y0 = y + h * 0.15
        y1 = y + h * 0.82
        ax.add_patch(plt.Circle((mid_x, y0), 0.35, color="#5D4037", zorder=4))
        ax.annotate("", xy=(mid_x, y1), xytext=(mid_x, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#5D4037",
                                    lw=1.5, mutation_scale=12),
                    zorder=4)
        ax.text(mid_x, y0 + (y1 - y0) * 0.5, "UP",
                ha="center", va="center", fontsize=7.5, fontweight="bold",
                color="#3E2723", backgroundcolor="#F4EFEA", zorder=5)
    else:
        # Steps run vertically
        n_steps = max(7, min(14, int(w / 0.85)))
        dx = w / n_steps
        for i in range(1, n_steps):
            sx = x + i * dx
            ax.plot([sx, sx], [y + 0.1, y + h - 0.1],
                    color="#8C827A", linewidth=0.9, zorder=3)

        mid_y = y + h * 0.5
        x0 = x + w * 0.15
        x1 = x + w * 0.82
        ax.add_patch(plt.Circle((x0, mid_y), 0.35, color="#5D4037", zorder=4))
        ax.annotate("", xy=(x1, mid_y), xytext=(x0, mid_y),
                    arrowprops=dict(arrowstyle="-|>", color="#5D4037",
                                    lw=1.5, mutation_scale=12),
                    zorder=4)
        ax.text(x0 + (x1 - x0) * 0.5, mid_y, "UP",
                ha="center", va="center", fontsize=7.5, fontweight="bold",
                color="#3E2723", backgroundcolor="#F4EFEA", zorder=5)

    # Staircase label
    cx, cy = x + w / 2, y + h / 2
    lbl_y = cy + (h * 0.32 if h >= w else h * 0.28)
    dim_y = cy - (h * 0.32 if h >= w else h * 0.28)
    ax.text(cx, lbl_y, "Staircase",
            ha="center", va="center", fontsize=7.5, fontweight="bold",
            color="#1A1A1A", zorder=5)
    ax.text(cx, dim_y, f"{w:.1f} × {h:.1f} ft",
            ha="center", va="center", fontsize=6.2, color="#555555", zorder=5)


# ---------------------------------------------------------------------------
# Room box + label
# ---------------------------------------------------------------------------

def _draw_room(ax: plt.Axes, item: dict) -> None:
    if item.get("kind") == "staircase" or "staircase" in item.get("name", "").lower():
        _draw_staircase(ax, item)
        return

    x, y, w, h = item["x"], item["y"], item["width"], item["length"]
    color  = item.get("color", get_room_color(item["name"]))
    is_amenity = item.get("kind") in ("amenity",)

    edge_color = "#27AE60" if "garden" in item["name"].lower() else \
                 "#626567" if "parking" in item["name"].lower() else ROOM_EDGE_COLOR
    lw = 1.5 if is_amenity else 2.0

    ax.add_patch(Rectangle((x, y), w, h,
                            facecolor=color, edgecolor=edge_color,
                            linewidth=lw, alpha=0.90, zorder=2))

    cx, cy = x + w / 2, y + h / 2
    area   = w * h
    name   = item["name"]
    dims   = f"{w:.1f} × {h:.1f} ft"
    area_s = f"{area:.0f} sq.ft"

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
# Door symbol — adjacency-aware wall selection + clipped swing arc
# ---------------------------------------------------------------------------

def _draw_door(ax: plt.Axes, room: dict, door: dict,
               all_rooms: list[dict] | None = None,
               plot_width: float = 30.0, plot_length: float = 40.0) -> None:
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    pref_wall  = door.get("wall", "south")
    offset     = door.get("offset_pct", 0.3)
    dw         = door.get("width_ft", 3.0)

    # Adjacency-aware wall selection
    wall = _best_door_wall(room, pref_wall, all_rooms) if all_rooms else pref_wall

    # Hinge position — clamp so door leaf stays within room span
    if wall == "south":
        hx = _clamp(x + w * offset, x, x + w - dw)
        hy = y

        # Bedroom doors: strictly align within Passage / Corridor X-range so they never overlap Kitchen
        rname = room.get("name", "").lower()
        if "bedroom" in rname and all_rooms:
            passage = next((r for r in all_rooms if "passage" in r.get("name", "").lower() or "corridor" in r.get("name", "").lower()), None)
            if passage:
                pass_min = max(x, passage["x"] + 0.1)
                pass_max = min(x + w - dw, passage["x"] + passage["width"] - dw - 0.1)
                if pass_min <= pass_max:
                    hx = _clamp(hx, pass_min, pass_max)

        line = [(hx, hy), (hx + dw, hy)]
        arc_center = (hx, hy)
        a1, a2 = 0, 90          # swing northward into room

    elif wall == "north":
        hx = _clamp(x + w * offset, x, x + w - dw)
        hy = y + h
        line = [(hx, hy), (hx + dw, hy)]
        arc_center = (hx, hy)
        # Flip hinge to right side when too close to right edge → swing leftward
        if hx + dw > x + w:
            hx = _clamp(x + w - dw, x, x + w - dw)
            arc_center = (hx + dw, hy)
            a1, a2 = 270, 360
        else:
            a1, a2 = 180, 270   # swing southward into room

    elif wall == "west":
        hx = x
        hy = _clamp(y + h * offset, y, y + h - dw)
        line = [(hx, hy), (hx, hy + dw)]
        arc_center = (hx, hy)
        a1, a2 = 270, 360       # swing eastward into room

    else:  # east
        hx = x + w
        hy = _clamp(y + h * offset, y, y + h - dw)
        line = [(hx, hy), (hx, hy + dw)]
        arc_center = (hx, hy)
        a1, a2 = 90, 180        # swing westward into room

    # White gap erases wall line at door position
    ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]],
            color="#F8F8F4", linewidth=4.5, zorder=6, solid_capstyle="butt")

    # Door leaf
    ax.plot([line[0][0], line[1][0]], [line[0][1], line[1][1]],
            color="#8B4513", linewidth=1.0, zorder=7)

    # Swing arc
    arc = Arc(arc_center, dw * 2, dw * 2, angle=0,
              theta1=a1, theta2=a2,
              color="#8B4513", linewidth=0.8, linestyle="--", zorder=7)
    ax.add_patch(arc)


# ---------------------------------------------------------------------------
# Window symbol (triple parallel lines) — strictly exterior & collision-safe
# ---------------------------------------------------------------------------

def _draw_window(ax: plt.Axes, room: dict, win: dict,
                 all_rooms: list[dict] | None = None,
                 plot_width: float = 30.0, plot_length: float = 40.0) -> None:
    x, y, w, h = room["x"], room["y"], room["width"], room["length"]
    wall   = win.get("wall", "south")
    offset = win.get("offset_pct", 0.5)
    ww     = min(win.get("width_ft", 3.5), 5.0)
    gap    = 0.18   # spacing between the 3 lines

    # Strict Exterior-Only: Never draw on an interior partition wall between enclosed rooms
    if all_rooms:
        if not _is_exterior_wall(room, wall, plot_width, plot_length, all_rooms):
            # Check if this room has another wall that IS an exterior wall
            found_wall = None
            for cand_wall in ["north", "south", "west", "east"]:
                if _is_exterior_wall(room, cand_wall, plot_width, plot_length, all_rooms):
                    if _window_is_safe(room, cand_wall, offset, ww, all_rooms):
                        found_wall = cand_wall
                        break
            if found_wall:
                wall = found_wall
            else:
                return   # Suppress window! Never draw on an interior wall between enclosed rooms

        if not _window_is_safe(room, wall, offset, ww, all_rooms):
            return

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
    ax.add_patch(Rectangle((bx, by), bw, bh,
                            fc="#B0C4DE", ec="#4682B4", lw=0.8, alpha=0.7, zorder=3))
    ax.add_patch(Rectangle((bx + 0.3, by + bh * 0.70), bw - 0.6, bh * 0.25,
                            fc="white", ec="#888", lw=0.5, alpha=0.8, zorder=4))


def _draw_sofa(ax, rx, ry, rw, rh):
    sw = min(rw * 0.65, 10.0); sh = min(rh * 0.28, 4.0)
    sx = rx + (rw - sw) / 2; sy = ry + rh * 0.08
    ax.add_patch(Rectangle((sx, sy), sw, sh,
                            fc="#D2B48C", ec="#8B4513", lw=0.8, alpha=0.7, zorder=3))
    ax.add_patch(Rectangle((sx, sy + sh * 0.70), sw, sh * 0.30,
                            fc="#C4A882", ec="#8B4513", lw=0.5, alpha=0.8, zorder=4))
    ctw = sw * 0.40; cth = rh * 0.14
    ctx = rx + (rw - ctw) / 2; cty = sy + sh + rh * 0.06
    ax.add_patch(Rectangle((ctx, cty), ctw, cth,
                            fc="#DEB887", ec="#8B4513", lw=0.6, alpha=0.65, zorder=3))


def _draw_dining(ax, rx, ry, rw, rh):
    tw = min(rw * 0.55, 7.0); th = min(rh * 0.55, 5.0)
    tx = rx + (rw - tw) / 2; ty = ry + (rh - th) / 2
    ax.add_patch(Rectangle((tx, ty), tw, th,
                            fc="#F5DEB3", ec="#8B4513", lw=0.8, alpha=0.80, zorder=3))
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
    cth = min(rh * 0.18, 2.0)
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3), rw - 0.6, cth,
                            fc="#C8C8C8", ec="#888", lw=0.6, alpha=0.80, zorder=3))
    ctw_ = min(rw * 0.18, 2.0)
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3 + cth), ctw_, rh - cth - 0.6,
                            fc="#C8C8C8", ec="#888", lw=0.6, alpha=0.80, zorder=3))
    sink_r = min(0.7, cth * 0.45)
    ax.add_patch(plt.Circle((rx + ctw_ * 0.5 + 0.3, ry + 0.3 + cth * 0.5),
                             sink_r, fc="white", ec="#555", lw=0.6, zorder=4))


def _draw_bathroom(ax, rx, ry, rw, rh):
    wc_w = min(rw * 0.45, 2.0); wc_h = min(rh * 0.42, 2.5)
    ax.add_patch(Rectangle((rx + 0.3, ry + 0.3), wc_w, wc_h,
                            fc="#E0F7FA", ec="#555", lw=0.6, alpha=0.85, zorder=3))
    b_w = min(rw * 0.38, 1.6); b_h = min(rh * 0.30, 1.6)
    ax.add_patch(Rectangle((rx + rw - b_w - 0.3, ry + 0.3), b_w, b_h,
                            fc="#E0F7FA", ec="#555", lw=0.6, alpha=0.85, zorder=3))


# ---------------------------------------------------------------------------
# North arrow
# ---------------------------------------------------------------------------

def _draw_north_arrow(ax: plt.Axes, W: float, L: float, plot_facing: str = "North") -> None:
    px = W + max(W, L) * 0.08
    py = L * 0.75
    arrow_len = max(W, L) * 0.07

    facing = plot_facing.strip().capitalize() if plot_facing else "North"
    if facing == "North":
        # Entrance at bottom = North -> N arrow points DOWN (↓)
        xy = (px, py - arrow_len)
        xytext = (px, py)
        text_pos = (px, py - arrow_len - 0.7)
        va = "top"
        ha = "center"
    elif facing == "South":
        # Entrance at bottom = South -> N arrow points UP (↑)
        xy = (px, py + arrow_len)
        xytext = (px, py)
        text_pos = (px, py + arrow_len + 0.5)
        va = "bottom"
        ha = "center"
    elif facing == "East":
        # Entrance at bottom = East -> N arrow points LEFT (←)
        xy = (px - arrow_len, py)
        xytext = (px, py)
        text_pos = (px - arrow_len - 0.7, py)
        va = "center"
        ha = "right"
    elif facing == "West":
        # Entrance at bottom = West -> N arrow points RIGHT (→)
        xy = (px + arrow_len, py)
        xytext = (px, py)
        text_pos = (px + arrow_len + 0.7, py)
        va = "center"
        ha = "left"
    else:
        # Default North (↓)
        xy = (px, py - arrow_len)
        xytext = (px, py)
        text_pos = (px, py - arrow_len - 0.7)
        va = "top"
        ha = "center"

    ax.annotate("", xy=xy, xytext=xytext,
                arrowprops=dict(arrowstyle="-|>", color="#1A1A1A",
                                lw=1.8, mutation_scale=16),
                zorder=12)
    ax.text(text_pos[0], text_pos[1], "N", ha=ha, va=va,
            fontsize=10.5, fontweight="bold", color="#1A1A1A", zorder=12)


# ---------------------------------------------------------------------------
# Road label
# ---------------------------------------------------------------------------

def _draw_road_label(ax: plt.Axes, W: float) -> None:
    ax.annotate("ROAD  ⟶", xy=(W * 0.5, -2.6), xytext=(W * 0.5, -2.6),
                ha="center", va="center", fontsize=9, color="#C0392B",
                fontweight="bold", zorder=12)


# ---------------------------------------------------------------------------
# Main entrance arrow
# ---------------------------------------------------------------------------

def _draw_main_entrance(ax: plt.Axes, rooms: list[dict],
                         features: list[dict], W: float) -> None:
    entrance_x = W * 0.35
    for item in rooms:
        if "living" in item.get("name", "").lower():
            for door in item.get("doors", []):
                if door.get("wall") == "south":
                    entrance_x = item["x"] + item["width"] * door.get("offset_pct", 0.3)
                    break
            break

    ax.annotate("MAIN ENTRANCE", xy=(entrance_x, -0.1),
                xytext=(entrance_x, -3.8),
                fontsize=8.5, fontweight="bold", color="#C0392B", ha="center",
                arrowprops=dict(arrowstyle="-|>", color="#C0392B", lw=1.8,
                                mutation_scale=15),
                zorder=12)


# ---------------------------------------------------------------------------
# Dimension annotations (four sides of plot)
# ---------------------------------------------------------------------------

def _draw_dimension_annotations(ax: plt.Axes, W: float, L: float) -> None:
    off = max(W, L) * 0.04
    kw  = dict(ha="center", va="center", fontsize=8.5, color="#2C3E50",
               fontweight="semibold", zorder=12)
    ax.text(W / 2, -1.2, f"← {W:.0f} ft →", **kw)
    ax.text(W / 2, L + off, f"← {W:.0f} ft →", **kw)
    ax.text(-off * 1.5, L / 2, f"← {L:.0f} ft →", rotation=90, **kw)
    ax.text(W + off * 1.5, L / 2, f"← {L:.0f} ft →", rotation=90, **kw)


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
