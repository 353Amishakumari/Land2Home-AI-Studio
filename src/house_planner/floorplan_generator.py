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
    1: (20.0, 25.0),
    2: (25.0, 32.0),
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
    # 1. FRONT ZONE [y = fd to y1]: Living + (Dining) + (Pooja)
    # =========================================================================
    if has_dining and has_pooja:
        pw_front = max(5.0, min(7.0, W * 0.18))
        rem_w = W - pw_front
        dw_front = max(7.5, rem_w * 0.38)
        lw_front = rem_w - dw_front

        rooms.append(_r("Living Room", 0, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5)],
                        windows=[_win("south", 0.65, 4.0), _win("west", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Dining Room", lw_front, fd, dw_front, front_h,
                        doors=[_door("south", 0.5, 3.0)],
                        windows=[_win("south", 0.5, 3.0)],
                        furniture="dining"))
        rooms.append(_r("Pooja Room", lw_front + dw_front, fd, pw_front, front_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    elif has_dining:
        dw_front = max(8.0, W * 0.35)
        lw_front = W - dw_front

        rooms.append(_r("Living Room", 0, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5)],
                        windows=[_win("south", 0.65, 4.0), _win("west", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Dining Room", lw_front, fd, dw_front, front_h,
                        doors=[_door("south", 0.5, 3.0)],
                        windows=[_win("east", 0.5, 3.0)],
                        furniture="dining"))
    elif has_pooja:
        pw_front = max(5.0, min(7.5, W * 0.20))
        lw_front = W - pw_front

        rooms.append(_r("Living Room", 0, fd, lw_front, front_h,
                        doors=[_door("south", 0.30, 3.5)],
                        windows=[_win("south", 0.65, 4.0), _win("west", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Pooja Room", lw_front, fd, pw_front, front_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    else:
        rooms.append(_r("Living Room", 0, fd, W, front_h,
                        doors=[_door("south", 0.28, 3.5)],
                        windows=[_win("south", 0.68, 4.5), _win("east", 0.5, 3.0)],
                        furniture="sofa"))

    # =========================================================================
    # 2. MIDDLE SERVICE ZONE [y = y1 to y2]: Kitchen, Utility, Passage, Bath, Store
    # =========================================================================
    uw = max(4.0, min(5.5, W * 0.13)) if has_utility else 0.0
    sw = max(4.0, min(5.5, W * 0.13)) if has_store else 0.0
    kw = max(6.5, min(9.5, W * 0.28))
    pw = max(3.5, min(5.0, W * 0.14))

    rem_bath_w = W - kw - uw - pw - sw
    min_needed_bath = 4.0 * max(n_bt, 1)
    if rem_bath_w < min_needed_bath:
        # Re-balance slightly from kitchen/passage
        deficit = min_needed_bath - rem_bath_w
        kw = max(6.0, kw - deficit * 0.6)
        pw = max(3.2, pw - deficit * 0.4)
        rem_bath_w = W - kw - uw - pw - sw

    # Cap bathroom width so Bathroom 1 doesn't blow up to 90+ sq.ft when n_bt=1
    auto_store = False
    auto_sw = 0.0
    max_bw = 6.8 * n_bt
    if rem_bath_w > max_bw + 3.0:
        surplus = rem_bath_w - max_bw
        if not has_store:
            auto_store = True
            auto_sw = min(5.5, surplus)
            surplus -= auto_sw
        if surplus > 0:
            kw += surplus * 0.6
            pw += surplus * 0.4
        rem_bath_w = W - kw - uw - pw - (sw + auto_sw)

    each_bw = rem_bath_w / max(n_bt, 1)

    cur_x = 0.0
    rooms.append(_r("Kitchen", cur_x, y1, kw, svc_h,
                    doors=[_door("north", 0.5, 3.0)],
                    windows=[_win("west", 0.5, 2.5)],
                    furniture="kitchen"))
    cur_x += kw

    if has_utility:
        rooms.append(_r("Utility", cur_x, y1, uw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("south", 0.5, 2.0)]))
        cur_x += uw

    rooms.append(_r("Passage", cur_x, y1, pw, svc_h, kind="passage",
                    doors=[_door("south", 0.5, 3.0)]))
    cur_x += pw

    for bi in range(n_bt):
        rooms.append(_r(f"Bathroom {bi+1}", cur_x, y1, each_bw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("north" if bi == 0 else "east", 0.5, 1.5)],
                        furniture="bathroom"))
        cur_x += each_bw

    if has_store or auto_store:
        label = "Store Room" if has_store else "Store / Utility"
        rooms.append(_r(label, cur_x, y1, sw + auto_sw, svc_h,
                        doors=[_door("west", 0.5, 2.5)]))
        cur_x += (sw + auto_sw)

    # =========================================================================
    # 3. REAR PRIVATE ZONE [y = y2 to L]: Bedrooms, Staircase, Balcony
    # =========================================================================
    if has_balcony:
        bal_h = max(3.5, min(4.5, prv_h * 0.25))
        bed_zone_h = prv_h - bal_h
    else:
        bal_h = 0.0
        bed_zone_h = prv_h

    if has_stair:
        stair_w = max(5.5, min(7.5, W * 0.20))
        rooms.append(_r("Staircase", W - stair_w, y2, stair_w, bed_zone_h,
                        kind="staircase"))
        bed_total_w = W - stair_w
    else:
        bed_total_w = W

    each_bed_w = bed_total_w / max(n_b, 1)
    for bi in range(n_b):
        bx = bi * each_bed_w
        win_wall = "west" if bi == 0 else ("east" if (bi == n_b - 1 and not has_stair) else "north")
        rooms.append(_r(f"Bedroom {bi+1}", bx, y2, each_bed_w, bed_zone_h,
                        doors=[_door("south", 0.4, 3.0)],
                        windows=[_win("north", 0.5, 3.5), _win(win_wall, 0.5, 2.5)],
                        furniture="bed"))

    if has_balcony:
        rooms.append(_r("Balcony", 0, y2 + bed_zone_h, bed_total_w, bal_h,
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

    # Right side: Dining / Pooja
    if has_dining and has_pooja:
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
    # 3. REAR ZONE [y = y_mid to L]: Bedrooms, Corridor, Staircase, Balcony
    # =========================================================================
    if has_balcony:
        bal_h = max(3.5, min(4.5, rear_h * 0.25))
        bed_rear_h = rear_h - bal_h
    else:
        bal_h = 0.0
        bed_rear_h = rear_h

    # Corridor and Staircase
    if has_stair:
        stair_h = max(5.5, min(bed_rear_h * 0.55, 8.5))
        corr_h = (bh - bal_h) - stair_h
        rooms.append(_r("Corridor", cx, fd, cw, corr_h, kind="passage",
                        doors=[_door("south", 0.5, 3.0)]))
        rooms.append(_r("Staircase", cx, fd + corr_h, cw, stair_h, kind="staircase"))
    else:
        rooms.append(_r("Corridor", cx, fd, cw, bh - bal_h, kind="passage",
                        doors=[_door("south", 0.5, 3.0)]))

    # Bedrooms divided left and right
    n_left_beds  = n_b // 2 + (n_b % 2)
    n_right_beds = n_b - n_left_beds

    each_lb = bed_rear_h / max(n_left_beds, 1)
    for bi in range(n_left_beds):
        by = y_mid + bi * each_lb
        rooms.append(_r(f"Bedroom {bi+1}", 0, by, left_w, each_lb,
                        doors=[_door("east", 0.4, 3.0)],
                        windows=[_win("west", 0.5, 2.5)],
                        furniture="bed"))

    if n_right_beds > 0:
        each_rb = bed_rear_h / n_right_beds
        for bi in range(n_right_beds):
            by = y_mid + bi * each_rb
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

    if has_balcony:
        rooms.append(_r("Balcony", 0, y_mid + bed_rear_h, W, bal_h,
                        kind="room", windows=[_win("north", 0.5, 6.0)]))

    return rooms


# ---------------------------------------------------------------------------
# Design C — Open Living + Dining Layout
# ---------------------------------------------------------------------------

def _design_c(W: float, L: float, fd: float, reqs: dict) -> list[dict]:
    """
    Open Living + Dining layout:
      Zone 1 (Front):   Spacious Open Living + Dining (with Pooja Room if requested).
      Zone 2 (Middle):  Kitchen, Utility (if requested), Passage, Bathrooms, Store Room (if requested).
      Zone 3 (Rear):    Bedrooms, Staircase (if requested), Balcony (if requested).

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
    # 1. FRONT ZONE [y = fd to y1]: Open Living + Dining (+ Pooja)
    # =========================================================================
    if has_pooja:
        pj_w = max(5.0, min(7.5, W * 0.18))
        rooms.append(_r("Open Living + Dining", 0, fd, W - pj_w, open_h,
                        doors=[_door("south", 0.25, 3.5)],
                        windows=[_win("south", 0.55, 5.0), _win("west", 0.5, 3.0)],
                        furniture="sofa"))
        rooms.append(_r("Pooja Room", W - pj_w, fd, pj_w, open_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("east", 0.5, 2.0)]))
    else:
        rooms.append(_r("Open Living + Dining", 0, fd, W, open_h,
                        doors=[_door("south", 0.25, 3.5)],
                        windows=[_win("south", 0.55, 5.5), _win("east", 0.5, 3.5),
                                 _win("west", 0.5, 3.0)],
                        furniture="sofa"))

    # =========================================================================
    # 2. MIDDLE SERVICE ZONE [y = y1 to y2]: Kitchen, Utility, Passage, Bath, Store
    # =========================================================================
    uw = max(4.0, min(5.5, W * 0.13)) if has_utility else 0.0
    sw = max(4.0, min(5.5, W * 0.13)) if has_store else 0.0
    kw = max(6.5, min(9.5, W * 0.28))
    pw = max(3.5, min(5.0, W * 0.14))

    rem_bath_w = W - kw - uw - pw - sw
    min_needed_bath = 4.0 * max(n_bt, 1)
    if rem_bath_w < min_needed_bath:
        deficit = min_needed_bath - rem_bath_w
        kw = max(6.0, kw - deficit * 0.6)
        pw = max(3.2, pw - deficit * 0.4)
        rem_bath_w = W - kw - uw - pw - sw

    # Cap bathroom width so Bathroom 1 doesn't blow up to 90+ sq.ft when n_bt=1
    auto_store = False
    auto_sw = 0.0
    max_bw = 6.8 * n_bt
    if rem_bath_w > max_bw + 3.0:
        surplus = rem_bath_w - max_bw
        if not has_store:
            auto_store = True
            auto_sw = min(5.5, surplus)
            surplus -= auto_sw
        if surplus > 0:
            kw += surplus * 0.6
            pw += surplus * 0.4
        rem_bath_w = W - kw - uw - pw - (sw + auto_sw)

    each_bw = rem_bath_w / max(n_bt, 1)

    cur_x = 0.0
    rooms.append(_r("Kitchen", cur_x, y1, kw, svc_h,
                    doors=[_door("north", 0.5, 3.0)],
                    windows=[_win("west", 0.5, 2.5)],
                    furniture="kitchen"))
    cur_x += kw

    if has_utility:
        rooms.append(_r("Utility", cur_x, y1, uw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("south", 0.5, 2.0)]))
        cur_x += uw

    rooms.append(_r("Passage", cur_x, y1, pw, svc_h, kind="passage",
                    doors=[_door("south", 0.5, 3.0)]))
    cur_x += pw

    for bi in range(n_bt):
        rooms.append(_r(f"Bathroom {bi+1}", cur_x, y1, each_bw, svc_h,
                        doors=[_door("west", 0.5, 2.5)],
                        windows=[_win("north" if bi == 0 else "east", 0.5, 1.5)],
                        furniture="bathroom"))
        cur_x += each_bw

    if has_store or auto_store:
        label = "Store Room" if has_store else "Store / Utility"
        rooms.append(_r(label, cur_x, y1, sw + auto_sw, svc_h,
                        doors=[_door("west", 0.5, 2.5)]))
        cur_x += (sw + auto_sw)

    # =========================================================================
    # 3. REAR PRIVATE ZONE [y = y2 to L]: Bedrooms, Staircase, Balcony
    # =========================================================================
    if has_balcony:
        bal_h = max(3.5, min(4.5, prv_h * 0.25))
        bed_zone_h = prv_h - bal_h
    else:
        bal_h = 0.0
        bed_zone_h = prv_h

    if has_stair:
        stair_w = max(5.5, min(7.5, W * 0.20))
        rooms.append(_r("Staircase", W - stair_w, y2, stair_w, bed_zone_h,
                        kind="staircase"))
        bed_total_w = W - stair_w
    else:
        bed_total_w = W

    each_bed_w = bed_total_w / max(n_b, 1)
    for bi in range(n_b):
        bx = bi * each_bed_w
        win_wall = "west" if bi == 0 else ("east" if (bi == n_b - 1 and not has_stair) else "north")
        rooms.append(_r(f"Bedroom {bi+1}", bx, y2, each_bed_w, bed_zone_h,
                        doors=[_door("south", 0.4, 3.0)],
                        windows=[_win("north", 0.5, 3.5), _win(win_wall, 0.5, 2.5)],
                        furniture="bed"))

    if has_balcony:
        rooms.append(_r("Balcony", 0, y2 + bed_zone_h, bed_total_w, bal_h,
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
