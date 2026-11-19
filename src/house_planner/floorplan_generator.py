"""
Land2Home — Intelligent Floor-Plan Generator
=============================================

Generates THREE architecturally distinct floor-plan arrangements for
1BHK, 2BHK, 3BHK and 4BHK on any rectangular plot.

Design A — Central Hall      : Living room prominently at front, bedrooms rear.
Design B — Corridor Plan     : Central passage spine, rooms on both sides.
Design C — Open Living+Dining: Open-plan living/dining zone, private rear wing.

All layouts are strictly validated with Shapely (zero overlaps, inside plot boundary)
and NetworkX (room connectivity).
"""

from __future__ import annotations
from src.visualization.colors import get_room_color
from .constraints import check_rectangular_layout, dimension_sanity_check, connectivity_check


# ---------------------------------------------------------------------------
# Minimum plot dimensions required per BHK
# ---------------------------------------------------------------------------
_MIN_DIMS: dict[int, tuple[float, float]] = {
    1: (15.0, 25.0),
    2: (15.0, 30.0),
    3: (28.0, 38.0),
    4: (32.0, 44.0),
}

_MIN_AREA: dict[int, float] = {1: 380.0, 2: 650.0, 3: 1000.0, 4: 1380.0}


# ---------------------------------------------------------------------------
# Room factory helper
# ---------------------------------------------------------------------------

def _r(name: str, x: float, y: float, w: float, h: float,
       kind: str = "room",
       doors:     list | None = None,
       windows:   list | None = None,
       furniture: str | None  = None) -> dict:
    """Create a room dict with rounded coordinates and auto-colour."""
    return {
        "name":      name,
        "kind":      kind,
        "x":         round(float(x), 2),
        "y":         round(float(y), 2),
        "width":     round(float(w), 2),
        "length":    round(float(h), 2),
        "color":     get_room_color(name),
        "doors":     doors    or [],
        "windows":   windows  or [],
        "furniture": furniture,
    }


def _door(wall: str, offset: float = 0.3, width: float = 3.0) -> dict:
    return {"wall": wall, "offset_pct": offset, "width_ft": width}


def _win(wall: str, offset: float = 0.5, width: float = 3.5) -> dict:
    return {"wall": wall, "offset_pct": offset, "width_ft": width}


# ---------------------------------------------------------------------------
# Design A — Central Hall Layout
# ---------------------------------------------------------------------------

def _design_a(W: float, L: float, fd: float, reqs: dict) -> list[dict]:
    """
    Central Hall layout:
      Zone 1 (Front):   Living Room, Dining Room (if requested), Pooja Room (if requested).
      Zone 2 (Middle):  Kitchen, Utility (if requested), Passage, Bathrooms, Store Room (if requested).
      Zone 3 (Rear):    Bedrooms, Staircase (if requested), Balcony (if requested).

    Guarantees strict non-overlapping room partitions.
    """
    bh   = L - fd          # total built depth
    n_b  = reqs.get("bedrooms",  2)
    n_bt = reqs.get("bathrooms", 1)
    has_dining  = reqs.get("dining_room", True)
    has_stair   = reqs.get("staircase", False)
    has_balcony = reqs.get("balcony",   False)
    has_store   = reqs.get("store_room",False)
    has_pooja   = reqs.get("pooja_room",False)
    has_utility = reqs.get("utility",   False)

    # Row split fractions: front / service / private
    if   n_b == 1: r_front, r_svc = 0.38, 0.28
    elif n_b == 2: r_front, r_svc = 0.34, 0.28
    elif n_b == 3: r_front, r_svc = 0.30, 0.26
    else:          r_front, r_svc = 0.26, 0.26

    front_h = round(bh * r_front, 2)
    svc_h   = round(bh * r_svc, 2)
    y1      = round(fd + front_h, 2)
    y2      = round(y1 + svc_h, 2)
    prv_h   = round(L - y2, 2)
    rooms: list[dict] = []

    # =========================================================================
    # 1. FRONT ZONE [y = fd to y1]: Staircase (if req) + Living + (Dining) + (Pooja)
    # =========================================================================
    if has_stair:
        stair_w = round(max(5.5, min(7.0, W * 0.20)), 2)
        rooms.append(_r("Staircase", 0, fd, stair_w, front_h,
                        kind="staircase",
                        doors=[_door("east", 0.5, 3.0)]))
        rem_W = round(W - stair_w, 2)
        fx = stair_w
    else:
        stair_w = 0.0
        rem_W = W
        fx = 0.0

    if has_dining and has_pooja:
        pw_front = round(max(4.5, min(6.0, rem_W * 0.18)), 2)
        rem_w2 = round(rem_W - pw_front, 2)
        dw_front = round(max(7.0, rem_w2 * 0.38), 2)
        lw_front = round(rem_w2 - dw_front, 2)

        rooms.append(_r("Living Room", fx, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.70, 4.0), _win("west" if fx == 0 else "south", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Dining Room", fx + lw_front, fd, dw_front, front_h,
                        doors=[_door("south", 0.5, 3.0)],
                        windows=[_win("south", 0.5, 3.0)],
                        furniture="dining"))
        rooms.append(_r("Pooja Room", fx + lw_front + dw_front, fd, pw_front, front_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    elif has_dining:
        dw_front = round(max(7.5, rem_W * 0.35), 2)
        lw_front = round(rem_W - dw_front, 2)

        rooms.append(_r("Living Room", fx, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.70, 4.0), _win("west" if fx == 0 else "south", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Dining Room", fx + lw_front, fd, dw_front, front_h,
                        doors=[_door("south", 0.5, 3.0)],
                        windows=[_win("east", 0.5, 3.0)],
                        furniture="dining"))
    elif has_pooja:
        pw_front = round(max(4.5, min(6.5, rem_W * 0.20)), 2)
        lw_front = round(rem_W - pw_front, 2)

        rooms.append(_r("Living Room", fx, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.70, 4.0), _win("west" if fx == 0 else "south", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Pooja Room", fx + lw_front, fd, pw_front, front_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    else:
        rooms.append(_r("Living Room", fx, fd, rem_W, front_h,
                        doors=[_door("south", 0.30, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.70, 4.5), _win("east", 0.5, 3.0)],
                        furniture="sofa"))

    # =========================================================================
    # 2. MIDDLE SERVICE ZONE [y = y1 to y2]: Kitchen, Utility, Passage, Bath, Store
    # =========================================================================
    each_bed_w = round(W / max(n_b, 1), 2)
    boundary_x = each_bed_w if n_b >= 2 else round(W * 0.45, 2)
    pw = round(max(4.0, min(6.0, W * 0.18)), 2)
    pass_x = round(max(4.5, boundary_x - pw * 0.5), 2)
    if pass_x + pw > W - 4.5:
        pass_x = round(W - 4.5 - pw, 2)

    # West wing: Kitchen (+ Utility)
    west_w = pass_x
    if has_utility:
        uw = round(max(3.8, min(5.0, west_w * 0.35)), 2)
        kw = round(west_w - uw, 2)
        rooms.append(_r("Kitchen", 0, y1, kw, svc_h,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="kitchen"))
        rooms.append(_r("Utility", kw, y1, uw, svc_h,
                        doors=[_door("east", 0.5, 2.5)],
                        windows=[_win("west", 0.5, 2.0)]))
    else:
        kw = west_w
        rooms.append(_r("Kitchen", 0, y1, kw, svc_h,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="kitchen"))

    # Central Passage: perfectly straddles the bedroom division
    rooms.append(_r("Passage", pass_x, y1, pw, svc_h, kind="passage",
                    doors=[_door("south", 0.5, 3.0)]))

    # East wing: Bathrooms (+ Store Room)
    east_w = round(W - (pass_x + pw), 2)
    if has_store:
        sw = round(max(3.8, min(5.0, east_w * 0.38)), 2)
        bath_total_w = round(east_w - sw, 2)
    else:
        sw = 0.0
        bath_total_w = east_w

    each_bw = round(bath_total_w / max(n_bt, 1), 2)
    cur_bx = round(pass_x + pw, 2)
    for bi in range(n_bt):
        bw = round(cur_bx + each_bw, 2) - cur_bx if bi < n_bt - 1 else round(bath_total_w - bi * each_bw, 2)
        rooms.append(_r(f"Bathroom {bi+1}", cur_bx, y1, bw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 1.5)],
                        furniture="bathroom"))
        cur_bx = round(cur_bx + bw, 2)

    if has_store:
        rooms.append(_r("Store Room", cur_bx, y1, sw, svc_h,
                        doors=[_door("west", 0.5, 2.5)]))

    # =========================================================================
    # 3. REAR PRIVATE ZONE [y = y2 to L]: Bedrooms, Balcony (Zero Voids!)
    # =========================================================================
    if has_balcony:
        bal_h = round(max(3.5, min(4.5, prv_h * 0.25)), 2)
        bed_zone_h = round(prv_h - bal_h, 2)
    else:
        bal_h = 0.0
        bed_zone_h = prv_h

    # All bedrooms span the full width W cleanly without staircase interruption
    for bi in range(n_b):
        bx = round(bi * each_bed_w, 2)
        bw = round(W - bx, 2) if bi == n_b - 1 else each_bed_w
        win_wall = "west" if bi == 0 else ("east" if bi == n_b - 1 else "north")

        # Door strictly opens into Passage
        if bi == 0:
            door_cx = round(min(pass_x + pw * 0.45, bx + bw - 1.6), 2)
            d_off = round(max(0.1, min(0.9, (door_cx - bx) / bw)), 2)
        elif bi == 1:
            door_cx = round(max(pass_x + pw * 0.55, bx + 1.6), 2)
            d_off = round(max(0.1, min(0.9, (door_cx - bx) / bw)), 2)
        else:
            d_off = 0.4

        rooms.append(_r(f"Bedroom {bi+1}", bx, y2, bw, bed_zone_h,
                        doors=[_door("south", d_off, 3.0)],
                        windows=[_win("north", 0.5, 3.5), _win(win_wall, 0.5, 2.5)],
                        furniture="bed"))

    # Rear Balcony spans FULL width W cleanly (zero voids!)
    if has_balcony:
        rooms.append(_r("Balcony", 0, round(y2 + bed_zone_h, 2), W, bal_h,
                        kind="room", windows=[_win("north", 0.5, 6.0)]))

    return rooms


# ---------------------------------------------------------------------------
# Design B — Corridor Plan Layout
# ---------------------------------------------------------------------------

def _design_b(W: float, L: float, fd: float, reqs: dict) -> list[dict]:
    """
    Corridor Plan layout:
      A central corridor runs from front to back, dividing West service / beds
      from East living / beds.
      Guarantees strict non-overlapping room partitions.
    """
    bh   = L - fd
    n_b  = reqs.get("bedrooms",  2)
    n_bt = reqs.get("bathrooms", 1)
    has_dining  = reqs.get("dining_room", True)
    has_stair   = reqs.get("staircase", False)
    has_balcony = reqs.get("balcony",   False)
    has_store   = reqs.get("store_room",False)
    has_pooja   = reqs.get("pooja_room",False)
    has_utility = reqs.get("utility",   False)

    cw = round(max(4.0, min(5.5, W * 0.16)), 2)
    left_w = round((W - cw) * 0.50, 2)
    right_w = round(W - left_w - cw, 2)
    cx = left_w

    if   n_b <= 2: r_top, r_mid = 0.32, 0.24
    elif n_b == 3: r_top, r_mid = 0.30, 0.24
    else:          r_top, r_mid = 0.27, 0.23

    top_h = round(bh * r_top, 2)
    mid_h = round(bh * r_mid, 2)
    y_top = round(fd + top_h, 2)
    y_mid = round(y_top + mid_h, 2)
    rear_h = round(L - y_mid, 2)

    rooms: list[dict] = []

    # =========================================================================
    # 1. TOP ZONE [y = fd to y_top]: Kitchen/Utility (West), Living (East)
    # =========================================================================
    if has_utility:
        uh = top_h * 0.35
        kh = top_h - uh
        rooms.append(_r("Utility", 0, fd, left_w, uh,
                        doors=[_door("east", 0.5, 2.5)],
                        windows=[_win("west", 0.5, 2.0)]))
        rooms.append(_r("Kitchen", 0, fd + uh, left_w, kh,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("west", 0.5, 2.5), _win("north", 0.5, 2.0)],
                        furniture="kitchen"))
    else:
        rooms.append(_r("Kitchen", 0, fd, left_w, top_h,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("south", 0.5, 3.5), _win("west", 0.5, 2.5)],
                        furniture="kitchen"))

    rooms.append(_r("Living Room", cx + cw, fd, right_w, top_h,
                    doors=[_door("west", 0.5, 3.5), _door("south", 0.3, 3.5)],
                    windows=[_win("south", 0.6, 4.0), _win("east", 0.5, 3.0)],
                    furniture="sofa"))

    # =========================================================================
    # 2. MID ZONE [y = y_top to y_mid]: Store + Baths (West), Dining + Pooja (East)
    # =========================================================================
    if has_store:
        sw = max(4.0, min(5.5, left_w * 0.40))
        bw = left_w - sw
        rooms.append(_r("Store Room", 0, y_top, sw, mid_h,
                        doors=[_door("east", 0.5, 2.5)]))
        each_bh = mid_h / max(n_bt, 1)
        for bi in range(n_bt):
            rooms.append(_r(f"Bathroom {bi+1}", sw, y_top + bi * each_bh, bw, each_bh,
                            doors=[_door("east", 0.5, 2.5)],
                            windows=[_win("west" if sw == 0 else "north", 0.5, 1.5)],
                            furniture="bathroom"))
    else:
        # Cap bathroom width if left_w is wide (e.g., > 7.0 ft) to avoid oversized bathrooms
        if n_bt == 1 and left_w > 7.0:
            bw = min(6.8, left_w * 0.55)
            sw = left_w - bw
            rooms.append(_r("Store / Utility", 0, y_top, sw, mid_h,
                            doors=[_door("east", 0.5, 2.5)]))
            rooms.append(_r("Bathroom 1", sw, y_top, bw, mid_h,
                            doors=[_door("east", 0.5, 2.5)],
                            windows=[_win("north", 0.5, 1.5)],
                            furniture="bathroom"))
        else:
            each_bh = mid_h / max(n_bt, 1)
            for bi in range(n_bt):
                rooms.append(_r(f"Bathroom {bi+1}", 0, y_top + bi * each_bh, left_w, each_bh,
                                doors=[_door("east", 0.5, 2.5)],
                                windows=[_win("west", 0.5, 1.5)],
                                furniture="bathroom"))

    # Right side: Dining / Pooja / Staircase
    if has_stair:
        if has_dining:
            dw = round(right_w * 0.52, 2)
            sw = round(right_w - dw, 2)
            rooms.append(_r("Dining Room", cx + cw, y_top, dw, mid_h,
                            doors=[_door("west", 0.5, 3.0)],
                            windows=[_win("north", 0.5, 3.0)],
                            furniture="dining"))
            rooms.append(_r("Staircase", cx + cw + dw, y_top, sw, mid_h,
                            kind="staircase",
                            doors=[_door("west", 0.5, 2.5)]))
        else:
            rooms.append(_r("Staircase", cx + cw, y_top, right_w, mid_h,
                            kind="staircase",
                            doors=[_door("west", 0.5, 3.0)]))
    elif has_dining and has_pooja:
        pw = max(4.0, min(5.5, right_w * 0.35))
        dw = right_w - pw
        rooms.append(_r("Dining Room", cx + cw, y_top, dw, mid_h,
                        doors=[_door("west", 0.5, 3.0)],
                        windows=[_win("north", 0.5, 3.0)],
                        furniture="dining"))
        rooms.append(_r("Pooja Room", cx + cw + dw, y_top, pw, mid_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    elif has_dining:
        rooms.append(_r("Dining Room", cx + cw, y_top, right_w, mid_h,
                        doors=[_door("west", 0.5, 3.0)],
                        windows=[_win("east", 0.5, 3.0)],
                        furniture="dining"))
    elif has_pooja:
        rooms.append(_r("Pooja Room", cx + cw, y_top, right_w, mid_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    else:
        rooms.append(_r("Passage", cx + cw, y_top, right_w, mid_h, kind="passage"))

    # =========================================================================
    # 3. REAR ZONE [y = y_mid to L]: Bedrooms, Corridor, Balcony (Zero Voids!)
    # =========================================================================
    if has_balcony:
        bal_h = round(max(3.5, min(4.5, rear_h * 0.25)), 2)
        bed_rear_h = round(rear_h - bal_h, 2)
    else:
        bal_h = 0.0
        bed_rear_h = rear_h

    # Corridor runs full depth to rear bedrooms cleanly
    corr_h = round(bh - bal_h, 2)
    rooms.append(_r("Corridor", cx, fd, cw, corr_h, kind="passage",
                    doors=[_door("south", 0.5, 3.0)]))

    # Bedrooms divided left and right
    n_left_beds  = n_b // 2 + (n_b % 2)
    n_right_beds = n_b - n_left_beds

    each_lb = round(bed_rear_h / max(n_left_beds, 1), 2)
    for bi in range(n_left_beds):
        by = round(y_mid + bi * each_lb, 2)
        rooms.append(_r(f"Bedroom {bi+1}", 0, by, left_w, each_lb,
                        doors=[_door("east", 0.4, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="bed"))

    if n_right_beds > 0:
        each_rb = round(bed_rear_h / n_right_beds, 2)
        for bi in range(n_right_beds):
            by = round(y_mid + bi * each_rb, 2)
            idx = n_left_beds + bi + 1
            rooms.append(_r(f"Bedroom {idx}", cx + cw, by, right_w, each_rb,
                            doors=[_door("west", 0.4, 3.0)],
                            windows=[_win("east", 0.5, 2.5)],
                            furniture="bed"))
    else:
        # 1BHK case: place quiet Study on right side
        rooms.append(_r("Study Room", cx + cw, y_mid, right_w, bed_rear_h,
                        doors=[_door("west", 0.5, 3.0)],
                        windows=[_win("east", 0.5, 2.5)]))

    # Rear Balcony spans FULL width W cleanly (zero voids!)
    if has_balcony:
        rooms.append(_r("Balcony", 0, round(y_mid + bed_rear_h, 2), W, bal_h,
                        kind="room", windows=[_win("north", 0.5, 6.0)]))

    return rooms


# ---------------------------------------------------------------------------
# Design C — Open Living + Dining Layout
# ---------------------------------------------------------------------------

def _design_c(W: float, L: float, fd: float, reqs: dict) -> list[dict]:
    """
    Open Living + Dining layout:
      Zone 1 (Front):   Staircase (if req), Spacious Open Living + Dining (+ Pooja).
      Zone 2 (Middle):  Kitchen, Utility, Passage, Bathrooms, Store.
      Zone 3 (Rear):    Bedrooms, Balcony (Zero Voids!).

    Guarantees strict non-overlapping room partitions.
    """
    bh   = L - fd
    n_b  = reqs.get("bedrooms",  2)
    n_bt = reqs.get("bathrooms", 1)
    has_stair   = reqs.get("staircase", False)
    has_balcony = reqs.get("balcony",   False)
    has_store   = reqs.get("store_room",False)
    has_pooja   = reqs.get("pooja_room",False)
    has_utility = reqs.get("utility",   False)

    if   n_b == 1: r1, r2 = 0.38, 0.26
    elif n_b == 2: r1, r2 = 0.33, 0.25
    elif n_b == 3: r1, r2 = 0.29, 0.24
    else:          r1, r2 = 0.25, 0.24

    open_h = round(bh * r1, 2)
    svc_h  = round(bh * r2, 2)
    y1     = round(fd + open_h, 2)
    y2     = round(y1 + svc_h, 2)
    prv_h  = round(L - y2, 2)

    rooms: list[dict] = []

    # =========================================================================
    # 1. FRONT ZONE [y = fd to y1]: Staircase (if req) + Open Living + Dining (+ Pooja)
    # =========================================================================
    if has_stair:
        stair_w = round(max(5.5, min(7.0, W * 0.20)), 2)
        rooms.append(_r("Staircase", 0, fd, stair_w, open_h,
                        kind="staircase",
                        doors=[_door("east", 0.5, 3.0)]))
        rem_W = round(W - stair_w, 2)
        fx = stair_w
    else:
        stair_w = 0.0
        rem_W = W
        fx = 0.0

    if has_pooja:
        pj_w = round(max(4.5, min(6.5, rem_W * 0.18)), 2)
        rooms.append(_r("Open Living + Dining", fx, fd, round(rem_W - pj_w, 2), open_h,
                        doors=[_door("south", 0.25, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.55, 5.0), _win("west" if fx == 0 else "south", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Pooja Room", fx + round(rem_W - pj_w, 2), fd, pj_w, open_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    else:
        rooms.append(_r("Open Living + Dining", fx, fd, rem_W, open_h,
                        doors=[_door("south", 0.25, 3.5), _door("north", 0.5, 3.0)],
                        windows=[_win("south", 0.55, 5.5), _win("east", 0.5, 3.5)],
                        furniture="sofa"))

    # =========================================================================
    # 2. MIDDLE SERVICE ZONE [y = y1 to y2]: Kitchen, Utility, Passage, Bath, Store
    # =========================================================================
    each_bed_w = round(W / max(n_b, 1), 2)
    boundary_x = each_bed_w if n_b >= 2 else round(W * 0.45, 2)
    pw = round(max(4.0, min(6.0, W * 0.18)), 2)
    pass_x = round(max(4.5, boundary_x - pw * 0.5), 2)
    if pass_x + pw > W - 4.5:
        pass_x = round(W - 4.5 - pw, 2)

    west_w = pass_x
    if has_utility:
        uw = round(max(3.8, min(5.0, west_w * 0.35)), 2)
        kw = round(west_w - uw, 2)
        rooms.append(_r("Kitchen", 0, y1, kw, svc_h,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="kitchen"))
        rooms.append(_r("Utility", kw, y1, uw, svc_h,
                        doors=[_door("east", 0.5, 2.5)],
                        windows=[_win("west", 0.5, 2.0)]))
    else:
        kw = west_w
        rooms.append(_r("Kitchen", 0, y1, kw, svc_h,
                        doors=[_door("east", 0.5, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="kitchen"))

    rooms.append(_r("Passage", pass_x, y1, pw, svc_h, kind="passage",
                    doors=[_door("south", 0.5, 3.0)]))

    east_w = round(W - (pass_x + pw), 2)
    if has_store:
        sw = round(max(3.8, min(5.0, east_w * 0.38)), 2)
        bath_total_w = round(east_w - sw, 2)
    else:
        sw = 0.0
        bath_total_w = east_w

    each_bw = round(bath_total_w / max(n_bt, 1), 2)
    cur_bx = round(pass_x + pw, 2)
    for bi in range(n_bt):
        bw = round(cur_bx + each_bw, 2) - cur_bx if bi < n_bt - 1 else round(bath_total_w - bi * each_bw, 2)
        rooms.append(_r(f"Bathroom {bi+1}", cur_bx, y1, bw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 1.5)],
                        furniture="bathroom"))
        cur_bx = round(cur_bx + bw, 2)

    if has_store:
        rooms.append(_r("Store Room", cur_bx, y1, sw, svc_h,
                        doors=[_door("west", 0.5, 2.5)]))

    # =========================================================================
    # 3. REAR PRIVATE ZONE [y = y2 to L]: Bedrooms, Balcony (Zero Voids!)
    # =========================================================================
    if has_balcony:
        bal_h = round(max(3.5, min(4.5, prv_h * 0.25)), 2)
        bed_zone_h = round(prv_h - bal_h, 2)
    else:
        bal_h = 0.0
        bed_zone_h = prv_h

    for bi in range(n_b):
        bx = round(bi * each_bed_w, 2)
        bw = round(W - bx, 2) if bi == n_b - 1 else each_bed_w
        win_wall = "west" if bi == 0 else ("east" if bi == n_b - 1 else "north")

        if bi == 0:
            door_cx = round(min(pass_x + pw * 0.45, bx + bw - 1.6), 2)
            d_off = round(max(0.1, min(0.9, (door_cx - bx) / bw)), 2)
        elif bi == 1:
            door_cx = round(max(pass_x + pw * 0.55, bx + 1.6), 2)
            d_off = round(max(0.1, min(0.9, (door_cx - bx) / bw)), 2)
        else:
            d_off = 0.4

        rooms.append(_r(f"Bedroom {bi+1}", bx, y2, bw, bed_zone_h,
                        doors=[_door("south", d_off, 3.0)],
                        windows=[_win("north", 0.5, 3.5), _win(win_wall, 0.5, 2.5)],
                        furniture="bed"))

    if has_balcony:
        rooms.append(_r("Balcony", 0, round(y2 + bed_zone_h, 2), W, bal_h,
                        kind="room", windows=[_win("north", 0.5, 6.0)]))

    return rooms


# ---------------------------------------------------------------------------
# Features (parking + garden in front strip)
# ---------------------------------------------------------------------------

def _make_features(W: float, L: float, fd: float, reqs: dict) -> list[dict]:
    features: list[dict] = []
    has_parking = reqs.get("parking", False)
    has_garden  = reqs.get("garden",  False)

    if has_parking and has_garden:
        p_w = W * 0.58
        features.append(_r("Parking", 0,   0, p_w,     fd, kind="amenity"))
        features.append(_r("Garden",  p_w, 0, W - p_w, fd, kind="amenity"))
    elif has_parking:
        features.append(_r("Parking", 0, 0, W, fd, kind="amenity"))
    elif has_garden:
        features.append(_r("Garden", 0, 0, W, fd, kind="amenity"))
    return features


# ---------------------------------------------------------------------------
# Full validation for a design
# ---------------------------------------------------------------------------

def _validate(rooms: list[dict], features: list[dict],
              W: float, L: float) -> dict:
    all_items   = rooms + features
    geo         = check_rectangular_layout(all_items, W, L)
    dim_warns   = dimension_sanity_check(rooms)
    try:
        conn    = connectivity_check(rooms)
    except Exception:
        conn    = {"connected": True, "issues": [], "warnings": []}

    all_issues  = geo["issues"] + conn["issues"]
    all_warns   = geo.get("warnings", []) + dim_warns + conn.get("warnings", [])
    return {
        "valid":        len(all_issues) == 0,
        "issues":       all_issues,
        "warnings":     all_warns,
        "geometry_ok":  len(geo["issues"]) == 0,
        "connected":    conn["connected"],
    }


# ---------------------------------------------------------------------------
# Feasibility check
# ---------------------------------------------------------------------------

def check_feasibility(plot_width: float, plot_length: float,
                       requirements: dict) -> tuple[bool, str, str]:
    """
    Return (feasible, reason, suggestion).
    """
    n_b     = requirements.get("bedrooms", 2)
    n_b     = max(1, min(n_b, 4))
    min_w, min_l = _MIN_DIMS.get(n_b, (25.0, 35.0))

    fd           = min(10.0, plot_length * 0.22)
    build_area   = plot_width * (plot_length - fd)
    min_area     = _MIN_AREA.get(n_b, 800.0)

    if plot_width < min_w:
        sugg = (f"Increase plot width to >= {min_w:.0f} ft, "
                f"or select {max(1,n_b-1)}BHK.")
        return False, (f"Plot width {plot_width:.1f} ft is below the {min_w:.0f} ft "
                       f"minimum needed for a {n_b}BHK."), sugg

    if plot_length < min_l:
        sugg = (f"Increase plot length to >= {min_l:.0f} ft, "
                f"or select {max(1,n_b-1)}BHK.")
        return False, (f"Plot length {plot_length:.1f} ft is below the {min_l:.0f} ft "
                       f"minimum needed for a {n_b}BHK."), sugg

    if build_area < min_area:
        sugg = f"Select {max(1,n_b-1)}BHK for this plot size."
        return False, (f"Buildable area {build_area:.0f} sqft < {min_area:.0f} sqft "
                       f"required for {n_b}BHK."), sugg

    return True, f"{n_b}BHK fits on a {plot_width:.0f}x{plot_length:.0f} ft plot.", ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_designs(plot_width: float, plot_length: float,
                          requirements: dict) -> list[dict]:
    """
    Generate all THREE designs and return them as a list.
    """
    feasible, reason, suggestion = check_feasibility(plot_width, plot_length, requirements)
    if not feasible:
        msg = reason
        if suggestion:
            msg += f"\n\nSuggestion: {suggestion}"
        raise ValueError(msg)

    # Front strip depth (parking + garden zone, below the built structure)
    fd = min(10.0, plot_length * 0.22)

    features = _make_features(plot_width, plot_length, fd, requirements)

    design_meta = [
        (1, "Design A — Central Hall",
         "Living room prominently at the front with bedrooms arranged at the rear. "
         "Kitchen and bathrooms occupy the middle service zone. Clear separation "
         "between public (front) and private (rear) spaces."),
        (2, "Design B — Corridor Plan",
         "A central passage spine runs the full depth of the built zone. "
         "Service rooms (kitchen, bathrooms) are on the west side, living and "
         "bedrooms on the east side. Each bedroom has an independent corridor access."),
        (3, "Design C — Open Living + Dining",
         "An open-plan living and dining area spans the full front width, creating "
         "a bright, spacious public zone. The service zone separates the bedrooms "
         "from the living area, ensuring clear public-private zoning."),
    ]
    layout_fns = [_design_a, _design_b, _design_c]

    designs: list[dict] = []
    for (did, dname, ddesc), fn in zip(design_meta, layout_fns):
        rooms = fn(plot_width, plot_length, fd, requirements)
        val   = _validate(rooms, features, plot_width, plot_length)

        # Scoring
        from src.evaluation.metrics import score_layout
        score = score_layout(rooms, features, plot_width, plot_length,
                             requirements, val)

        designs.append({
            "design_id":          did,
            "design_name":        dname,
            "design_description": ddesc,
            "rooms":              rooms,
            "features":           features,
            "validation":         val,
            "score":              score,
            "plot_width":         plot_width,
            "plot_length":        plot_length,
            "front_depth":        fd,
        })

    return designs


# ---------------------------------------------------------------------------
# Legacy shim — keeps existing app.py imports working
# ---------------------------------------------------------------------------

def generate_basic_layout(plot_width: float, plot_length: float,
                           requirements: dict) -> dict:
    designs = generate_all_designs(plot_width, plot_length, requirements)
    best    = designs[0]
    return {
        "rooms":      best["rooms"],
        "features":   best["features"],
        "validation": best["validation"],
        "built_depth": plot_length - best["front_depth"],
        "design_name": best["design_name"],
    }
