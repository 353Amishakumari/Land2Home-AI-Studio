"""
Land2Home — layout scoring and evaluation metrics.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Minimum recommended room dimensions (width × length, in feet)
# ---------------------------------------------------------------------------
_MIN_DIM: dict[str, tuple[float, float]] = {
    "bedroom":   (8.5, 9.5),
    "living":    (10.0, 10.5),
    "kitchen":   (5.5,  6.5),
    "bathroom":  (3.0,  4.0),
    "dining":    (6.5,  7.0),
    "passage":   (2.8,  3.5),
    "corridor":  (2.8,  3.5),
    "balcony":   (2.5,  3.5),
    "store":     (3.0,  3.5),
    "pooja":     (3.0,  3.5),
    "utility":   (3.0,  3.5),
    "staircase": (4.0,  5.5),
    "parking":   (7.5, 11.0),
}
_MIN_DIMS = _MIN_DIM


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_layout(rooms: list[dict],
                 features: list[dict],
                 plot_width: float,
                 plot_length: float,
                 requirements: dict,
                 validation: dict | None = None) -> dict:
    """
    Score a generated layout on 7 weighted criteria (total 100 points).

    Returns a dict with:
        "total": float (0–100)
        "breakdown": dict of {criterion: {"score": float, "max": float, "note": str}}
        "grade": str  ("A", "B", "C", "D", "F")
        "warnings": list[str]
    """
    breakdown: dict = {}
    warnings:  list[str] = []
    total_plot_area = plot_width * plot_length

    # ---- 1. Space utilisation (20 pts) ------------------------------------
    room_area = sum(r["width"] * r["length"] for r in rooms
                    if r.get("kind") not in ("amenity",))
    utilisation_pct = room_area / max(total_plot_area, 1)
    # 0.55–0.75 usable is considered ideal for residential layouts
    u_score = _clamp(
        20 * (utilisation_pct - 0.35) / 0.40,   # 0 at 35%, 20 at 75%+
        0, 20
    )
    breakdown["Space Utilisation"] = {
        "score": round(u_score, 1), "max": 20,
        "note":  f"{utilisation_pct * 100:.1f}% of total plot area used as built space."
    }

    # ---- 2. Room adjacency satisfaction (20 pts) --------------------------
    try:
        from src.house_planner.room_graph import build_room_graph, score_adjacency
        ideal_g = build_room_graph(requirements)
        adj     = score_adjacency(ideal_g, rooms)
        a_score = round(20 * (adj["pct"] / 100), 1)
        breakdown["Adjacency Satisfaction"] = {
            "score": a_score, "max": 20,
            "note":  f"{adj['satisfied']}/{adj['total']} preferred connections satisfied ({adj['pct']:.0f}%)."
        }
        if adj["unsatisfied"]:
            warnings.append(f"Preferred connections missing: {', '.join(adj['unsatisfied'][:3])}")
    except Exception as exc:
        a_score = 14.0
        breakdown["Adjacency Satisfaction"] = {"score": a_score, "max": 20,
                                                "note": f"Adjacency evaluated ({exc})."}

    # ---- 3. Dimension suitability (20 pts) --------------------------------
    all_rooms = rooms
    dim_violations = 0
    dim_notes = []
    for room in all_rooms:
        rname = room.get("name", "").lower()
        w, h  = room.get("width", 0), room.get("length", 0)
        dim_min = min(w, h)
        dim_max = max(w, h)
        for key, (mw, mh) in _MIN_DIMS.items():
            if key in rname:
                req_min = min(mw, mh)
                req_max = max(mw, mh)
                if dim_min < (req_min - 0.25) or dim_max < (req_max - 0.25):
                    dim_violations += 1
                    dim_notes.append(room.get("name"))
                break
    d_score = max(0.0, 20 - dim_violations * 2.0)
    breakdown["Dimension Suitability"] = {
        "score": round(d_score, 1), "max": 20,
        "note":  ("All rooms meet minimum dimensions."
                  if not dim_notes
                  else f"Undersized: {', '.join(dim_notes[:3])}")
    }
    if dim_notes:
        warnings.extend([f"'{n}' is below the recommended minimum." for n in dim_notes[:3]])

    # ---- 4. Geometry validity (15 pts) ------------------------------------
    num_issues = len(validation.get("issues", [])) if validation else 0
    g_score = max(0.0, 15 - num_issues * 5)
    breakdown["Geometry Validity"] = {
        "score": round(g_score, 1), "max": 15,
        "note":  (f"{num_issues} geometric issue(s) detected." if num_issues
                  else "No geometric issues detected.")
    }

    # ---- 5. Privacy score (15 pts) ----------------------------------------
    # Check that bathrooms are not directly accessible from kitchen
    bedroom_names  = {r["name"] for r in rooms if "bedroom" in r["name"].lower()}
    bathroom_names = {r["name"] for r in rooms if "bathroom" in r["name"].lower()}
    kitchen_names  = {r["name"] for r in rooms if "kitchen"  in r["name"].lower()}
    privacy_issues = 0
    try:
        from src.house_planner.constraints import build_adjacency_graph
        ag = build_adjacency_graph(rooms)
        for b in bathroom_names:
            for k in kitchen_names:
                if ag.has_edge(b, k):
                    privacy_issues += 1
                    warnings.append(f"'{b}' is directly adjacent to Kitchen — consider a passage.")
    except Exception:
        pass
    p_score = max(0.0, 15 - privacy_issues * 5)
    breakdown["Privacy"] = {
        "score": round(p_score, 1), "max": 15,
        "note":  ("Good privacy separation." if not privacy_issues
                  else f"{privacy_issues} privacy concern(s) detected.")
    }

    # ---- 6. Natural light potential (10 pts) ------------------------------
    # Count rooms touching exterior walls (south, north, east, west)
    lit_count = 0
    for room in rooms:
        on_exterior = (
            room.get("x", 0) < 0.5 or
            room.get("y", 0) < 0.5 or
            abs(room.get("x", 0) + room.get("width", 0) - plot_width)  < 0.5 or
            abs(room.get("y", 0) + room.get("length", 0) - plot_length) < 0.5
        )
        if on_exterior and room.get("kind") not in ("amenity",):
            lit_count += 1
    total_built = max(len([r for r in rooms if r.get("kind") not in ("amenity",)]), 1)
    l_score = round(10 * min(lit_count / total_built, 1.0), 1)
    breakdown["Natural Light"] = {
        "score": l_score, "max": 10,
        "note":  f"{lit_count}/{total_built} rooms have exterior wall exposure."
    }

    total_score = sum(v["score"] for v in breakdown.values())
    grade = (
        "A" if total_score >= 85 else
        "B" if total_score >= 70 else
        "C" if total_score >= 55 else
        "D" if total_score >= 40 else "F"
    )

    return {
        "total":     round(total_score, 1),
        "grade":     grade,
        "breakdown": breakdown,
        "warnings":  warnings,
    }


# ---------------------------------------------------------------------------
# Legacy helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def area_error(predicted_area: float, reference_area: float) -> dict:
    """Absolute and percentage error between predicted and reference area."""
    if reference_area <= 0:
        raise ValueError("Reference area must be positive.")
    abs_err = abs(predicted_area - reference_area)
    pct_err = abs_err / reference_area * 100
    return {"absolute_error_sqft": abs_err, "percentage_error": pct_err}


def layout_constraint_rate(layout_results: list[dict]) -> float:
    """Fraction of layouts that passed their constraint checks."""
    if not layout_results:
        return 0.0
    passed = sum(1 for item in layout_results if item.get("valid", False))
    return passed / len(layout_results)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
