"""
Land2Home — Calibration and Scale Tool for Image-Based Land Measurement
========================================================================

Converts pixel coordinates and measurements into real-world feet and sq.ft
using:
  1. A known reference side length (e.g. Front Road Side = 30 ft)
  2. A known total land area (e.g. 1200 sq.ft)
"""

from __future__ import annotations
import math
from typing import Sequence


def pixels_per_foot(pixel_distance: float, real_distance_feet: float) -> float:
    """Calculate scale factor in pixels per foot from a known line segment."""
    if pixel_distance <= 0 or real_distance_feet <= 0:
        raise ValueError("Pixel and real distances must be strictly positive.")
    return float(pixel_distance / real_distance_feet)


def pixels_per_foot_from_area(pixel_area: float, real_area_sqft: float) -> float:
    """Calculate scale factor in pixels per foot from known total polygon area."""
    if pixel_area <= 0 or real_area_sqft <= 0:
        raise ValueError("Pixel and real area values must be strictly positive.")
    return float(math.sqrt(pixel_area / real_area_sqft))


def pixel_polygon_to_feet(
    points: Sequence[tuple[float, float]],
    scale_pixels_per_foot: float,
    origin: tuple[float, float] | None = None
) -> list[tuple[float, float]]:
    """
    Convert a list of (x, y) pixel coordinates into feet.
    Aligns coordinate origin to the minimum x and minimum y (so all coordinates >= 0).
    """
    if scale_pixels_per_foot <= 0:
        raise ValueError("Scale must be positive.")
    if not points:
        return []

    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)

    if origin is None:
        origin_x, origin_y = min_x, min_y
    else:
        origin_x, origin_y = origin

    return [
        (
            round((p[0] - origin_x) / scale_pixels_per_foot, 2),
            round((p[1] - origin_y) / scale_pixels_per_foot, 2)
        )
        for p in points
    ]


def compute_calibrated_plot(
    detected_result: dict,
    calibration_method: str = "side",
    known_side_index: int = 0,
    known_side_ft: float = 30.0,
    known_area_sqft: float = 1200.0
) -> dict:
    """
    Compute full real-world metrics from a detection result using either
    a known side length or a known area.

    Returns:
        {
            "scale_px_per_ft": float,
            "width_ft": float,
            "length_ft": float,
            "area_sqft": float,
            "area_sqm": float,
            "perimeter_ft": float,
            "side_lengths_ft": list[float],
            "polygon_feet": list[tuple[float, float]],
            "calibration_summary": str
        }
    """
    if not detected_result.get("success", False):
        raise ValueError("Cannot calibrate an unsuccessful boundary detection.")

    corners = detected_result.get("ordered_corners") or detected_result.get("corners", [])
    side_lengths_px = detected_result.get("side_lengths_px", [])
    area_px = detected_result.get("area_px", 1.0)

    if calibration_method == "area":
        scale = pixels_per_foot_from_area(area_px, known_area_sqft)
        summary = f"Calibrated from total area: {known_area_sqft:.1f} sq.ft ({scale:.2f} px/ft)"
    else:
        # Calibrate from side
        if not side_lengths_px:
            raise ValueError("No detected sides available for calibration.")
        idx = max(0, min(known_side_index, len(side_lengths_px) - 1))
        chosen_side_px = side_lengths_px[idx]
        scale = pixels_per_foot(chosen_side_px, known_side_ft)
        summary = f"Calibrated from Side {idx+1}: {known_side_ft:.1f} ft ({scale:.2f} px/ft)"

    # Convert polygon coordinates to feet
    poly_ft = pixel_polygon_to_feet(corners, scale)

    # Compute bounding box in feet
    xs = [p[0] for p in poly_ft]
    ys = [p[1] for p in poly_ft]
    bbox_w = max(xs) - min(xs)
    bbox_l = max(ys) - min(ys)

    # Side lengths in feet
    side_lengths_ft = [round(px / scale, 2) for px in side_lengths_px]
    perimeter_ft = round(sum(side_lengths_ft), 2)
    area_sqft = round(area_px / (scale ** 2), 2)
    area_sqm = round(area_sqft * 0.09290304, 4)

    return {
        "scale_px_per_ft": round(scale, 3),
        "width_ft": round(max(bbox_w, bbox_l if bbox_w < 10 else bbox_w), 1),
        "length_ft": round(max(bbox_l, bbox_w if bbox_l < 10 else bbox_l), 1),
        "plot_width": round(min(bbox_w, bbox_l), 1),
        "plot_length": round(max(bbox_w, bbox_l), 1),
        "area_sqft": area_sqft,
        "area_sqm": area_sqm,
        "perimeter_ft": perimeter_ft,
        "side_lengths_ft": side_lengths_ft,
        "polygon_feet": poly_ft,
        "calibration_summary": summary
    }
