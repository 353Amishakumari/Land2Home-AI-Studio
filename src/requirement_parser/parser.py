"""
Land2Home — house requirement parser and feasibility checker.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Minimum buildable areas per BHK type (sq.ft.) — conservative estimates
# for a compact but livable Indian residential layout.
# ---------------------------------------------------------------------------
_MIN_AREA: dict[int, float] = {
    1: 400.0,
    2: 700.0,
    3: 1050.0,
    4: 1450.0,
}

_MIN_PLOT_DIMS: dict[int, tuple[float, float]] = {
    # (min_width_ft, min_length_ft)
    1: (20.0, 25.0),
    2: (25.0, 32.0),
    3: (28.0, 38.0),
    4: (32.0, 44.0),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_requirements(
    house_type:  str  = "2BHK",
    floors:      str  = "Ground Floor",
    parking:     bool = False,
    staircase:   bool = False,
    garden:      bool = False,
    dining_room: bool = True,
    balcony:     bool = False,
    store_room:  bool = False,
    pooja_room:  bool = False,
    utility:     bool = False,
    bathrooms:   int  = 0,
) -> dict:
    """
    Convert UI form selections into a structured requirement dict.

    Args:
        house_type:  "1BHK" | "2BHK" | "3BHK" | "4BHK"
        floors:      "Ground Floor" | "G+1" | "G+2"
        parking / staircase / garden / dining_room / balcony /
        store_room / pooja_room / utility:  boolean feature flags.
        bathrooms:   explicit bathroom count (0 = auto-derive from BHK).

    Returns:
        Structured dict consumed by floorplan_generator and the UI.
    """
    bedroom_count = int(house_type.replace("BHK", ""))
    auto_baths    = max(1, bedroom_count - 1) if bathrooms <= 0 else bathrooms

    return {
        "house_type":   house_type,
        "bedrooms":     bedroom_count,
        "bathrooms":    auto_baths,
        "kitchen":      1,
        "living_room":  1,
        "dining_room":  bool(dining_room),
        "balcony":      bool(balcony),
        "store_room":   bool(store_room),
        "pooja_room":   bool(pooja_room),
        "utility":      bool(utility),
        "floors":       floors,
        "parking":      bool(parking),
        "staircase":    bool(staircase or floors != "Ground Floor"),
        "garden":       bool(garden),
        "design_count": 3,
    }


def validate_feasibility(requirements: dict,
                          plot_width: float,
                          plot_length: float,
                          setback: float = 0.0) -> dict:
    """
    Check whether the selected BHK configuration can physically fit on
    the given plot.

    Returns:
        {
            "feasible": bool,
            "reason": str,          # human-readable explanation
            "suggestion": str,      # actionable alternative (empty if feasible)
            "buildable_area_sqft": float,
        }
    """
    n_bed = requirements.get("bedrooms", 2)
    n_bed = max(1, min(n_bed, 4))

    # Usable area after front setback (parking/garden strip uses ~20–25% of depth)
    front_strip = min(10.0, plot_length * 0.22)
    buildable_area = (plot_width - 2 * setback) * (plot_length - front_strip - setback)

    min_area      = _MIN_AREA.get(n_bed, 1000.0)
    min_w, min_l  = _MIN_PLOT_DIMS.get(n_bed, (30.0, 40.0))

    effective_w = plot_width - 2 * setback
    effective_l = plot_length - front_strip - setback

    issues = []
    if buildable_area < min_area:
        issues.append(
            f"Buildable area {buildable_area:.0f} sq.ft is less than the minimum "
            f"{min_area:.0f} sq.ft needed for a {n_bed}BHK."
        )
    if effective_w < min_w:
        issues.append(
            f"Plot width ({plot_width:.1f} ft, effective {effective_w:.1f} ft) is below "
            f"the {min_w:.0f} ft minimum for {n_bed}BHK."
        )
    if effective_l < min_l:
        issues.append(
            f"Plot length ({plot_length:.1f} ft, effective {effective_l:.1f} ft) is below "
            f"the {min_l:.0f} ft minimum for {n_bed}BHK."
        )

    if not issues:
        return {
            "feasible":            True,
            "reason":              f"{n_bed}BHK fits comfortably on this {plot_width:.0f}×{plot_length:.0f} ft plot.",
            "suggestion":          "",
            "buildable_area_sqft": round(buildable_area, 1),
        }

    # Build a helpful suggestion
    suggestion = ""
    if n_bed > 1 and buildable_area >= _MIN_AREA.get(n_bed - 1, 0):
        suggestion = (
            f"Consider a {n_bed - 1}BHK layout which needs only "
            f"{_MIN_AREA[n_bed-1]:.0f} sq.ft of buildable area."
        )
    elif buildable_area < _MIN_AREA.get(1, 400):
        suggestion = "The plot is very small. Consider a studio layout or verify the dimensions."

    return {
        "feasible":            False,
        "reason":              " | ".join(issues),
        "suggestion":          suggestion,
        "buildable_area_sqft": round(buildable_area, 1),
    }
