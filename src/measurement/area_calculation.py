"""
Land2Home — land area and perimeter calculation.
"""

from .geometry import polygon_measurements, setback_dimensions


def calculate_land_area(points: list) -> dict:
    """
    Return comprehensive area and perimeter information for a plot polygon.

    Args:
        points: list of (x, y) coordinate tuples in feet.

    Returns:
        dict with area_sqft, area_sqm, perimeter_ft, boundary_lengths_ft,
        and a human-readable area_str / perimeter_str.
    """
    result = polygon_measurements(points)
    area_sqft = result["area_sqft"]
    return {
        "area_sqft":           area_sqft,
        "area_sqm":            result["area_sqm"],
        "perimeter_ft":        result["perimeter_ft"],
        "boundary_lengths_ft": result["boundary_lengths_ft"],
        "area_cents":          round(area_sqft / 435.6, 3),   # 1 cent = 435.6 sqft (South Indian)
        "area_str":            f"{area_sqft:,.1f} sq.ft  ({result['area_sqm']:,.2f} sq.m)",
        "perimeter_str":       f"{result['perimeter_ft']:,.1f} ft",
    }


def calculate_with_setback(points: list, width_ft: float, length_ft: float,
                            front_ft: float = 0.0, rear_ft: float = 0.0,
                            left_ft: float = 0.0, right_ft: float = 0.0) -> dict:
    """
    Return both gross and net (after setback) land measurements.

    Args:
        points:     polygon corner points (gross plot boundary).
        width_ft:   gross plot width.
        length_ft:  gross plot length.
        front/rear/left/right_ft: setback distances.

    Returns:
        dict combining gross measurements and usable (net) dimensions.
    """
    gross = calculate_land_area(points)
    net   = setback_dimensions(width_ft, length_ft, front_ft, rear_ft, left_ft, right_ft)
    return {
        **gross,
        "setbacks": {
            "front_ft": front_ft, "rear_ft": rear_ft,
            "left_ft":  left_ft,  "right_ft": right_ft,
        },
        "usable_width_ft":  net["usable_width_ft"],
        "usable_length_ft": net["usable_length_ft"],
        "usable_area_sqft": net["usable_area_sqft"],
        "usable_area_sqm":  net["usable_area_sqm"],
        "setback_loss_pct": round(
            (1 - net["usable_area_sqft"] / gross["area_sqft"]) * 100, 1
        ),
    }
