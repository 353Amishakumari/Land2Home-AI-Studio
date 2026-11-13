"""
Land2Home — geometry utilities for plot measurement.

All coordinates and dimensions are in feet unless noted.
"""

from shapely.geometry import Polygon


# ---------------------------------------------------------------------------
# Polygon helpers
# ---------------------------------------------------------------------------

def make_polygon(points: list) -> Polygon:
    """Create and validate a Shapely Polygon from (x, y) coordinate pairs."""
    if len(points) < 3:
        raise ValueError("A plot boundary needs at least three corner points.")
    polygon = Polygon(points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)   # attempt self-intersection repair
    if polygon.is_empty or polygon.area <= 0:
        raise ValueError("The supplied plot boundary produces no usable area.")
    return polygon


def polygon_measurements(points: list) -> dict:
    """Return area and perimeter measurements for an arbitrary polygon."""
    polygon = make_polygon(points)
    coords = list(polygon.exterior.coords)
    boundary_lengths = []
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        boundary_lengths.append(round(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 2))
    return {
        "area_sqft":      round(float(polygon.area), 2),
        "area_sqm":       round(float(polygon.area * 0.09290304), 4),
        "perimeter_ft":   round(float(polygon.length), 2),
        "boundary_lengths_ft": boundary_lengths,
        "polygon":        polygon,
    }


# ---------------------------------------------------------------------------
# Named plot shapes
# ---------------------------------------------------------------------------

def rectangular_plot(length_ft: float, width_ft: float) -> list:
    """Return corner points for a rectangular plot (front-left origin)."""
    if length_ft <= 0 or width_ft <= 0:
        raise ValueError("Length and width must be positive.")
    return [
        (0.0,          0.0),
        (float(width_ft),  0.0),
        (float(width_ft),  float(length_ft)),
        (0.0,          float(length_ft)),
    ]


def square_plot(side_ft: float) -> list:
    """Return corner points for a square plot."""
    if side_ft <= 0:
        raise ValueError("Side length must be positive.")
    return rectangular_plot(side_ft, side_ft)


# ---------------------------------------------------------------------------
# Setback / buildable area
# ---------------------------------------------------------------------------

def setback_dimensions(width_ft: float, length_ft: float,
                        front_ft: float = 0.0, rear_ft: float = 0.0,
                        left_ft: float = 0.0, right_ft: float = 0.0) -> dict:
    """
    Compute usable (buildable) dimensions after applying configurable setbacks.

    Setbacks are measured inward from each boundary edge.
    Returns usable width, length, area and the inset origin.
    """
    usable_w = width_ft  - left_ft  - right_ft
    usable_l = length_ft - front_ft - rear_ft
    if usable_w <= 0 or usable_l <= 0:
        raise ValueError(
            f"Setbacks ({front_ft}/{rear_ft}/{left_ft}/{right_ft} ft) leave no "
            "usable plot area. Reduce setback values."
        )
    return {
        "usable_width_ft":  round(usable_w, 2),
        "usable_length_ft": round(usable_l, 2),
        "usable_area_sqft": round(usable_w * usable_l, 2),
        "usable_area_sqm":  round(usable_w * usable_l * 0.09290304, 4),
        "origin_x":         left_ft,
        "origin_y":         front_ft,
    }
