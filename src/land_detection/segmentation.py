"""
Land2Home — Plot Boundary & Sketch Segmentation Pipeline
=========================================================

Detects plot boundaries from:
  1. Satellite map screenshots / real land site photos
  2. Hand-drawn sketches / cadastral blueprint drawings

Includes:
  - Adaptive thresholding & multi-scale edge filtering
  - Polygon approximation (approxPolyDP)
  - 4-point ordering & perspective transform (homography rectification)
  - Annotated overlay visualization with corner markers & side labels
"""

from __future__ import annotations
import math
import cv2
import numpy as np


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order coordinates consistently in order:
      [top-left, top-right, bottom-right, bottom-left].
    """
    rect = np.zeros((4, 2), dtype="float32")
    pts = pts.reshape(4, 2)

    # Top-left has smallest sum (x+y); bottom-right has largest sum (x+y)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Top-right has smallest difference (y-x); bottom-left has largest difference (y-x)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> tuple[np.ndarray, float, float]:
    """
    Apply a 4-point perspective transform (homography warp) to obtain an
    overhead / top-down bird's-eye view of the plot.

    Returns:
        (warped_image, target_width, target_height)
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Compute width of new image: maximum distance between bottom and top horizontal points
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = max(int(width_a), int(width_b), 10)

    # Compute height of new image: maximum distance between right and left vertical points
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = max(int(height_a), int(height_b), 10)

    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_w, max_h))
    return warped, float(max_w), float(max_h)


def detect_plot_boundary(
    image_rgb: np.ndarray,
    mode: str = "auto",
    blur_kernel: int = 5
) -> dict:
    """
    Detect the prominent plot boundary polygon from an image.

    Args:
        image_rgb:   RGB numpy array of the plot image or sketch.
        mode:        "auto" | "sketch" | "satellite" | "photo"
        blur_kernel: Gaussian blur kernel size (odd integer >= 3).

    Returns:
        dict containing:
            "success": bool
            "corners": list of (x, y) tuples in pixel coordinates
            "ordered_corners": list of 4 (x, y) tuples if quad, else None
            "is_quadrilateral": bool
            "perimeter_px": float
            "area_px": float
            "warped_image": RGB numpy array (perspective-rectified) or None
            "annotated_image": RGB numpy array with corner pins and boundary
            "side_lengths_px": list of float distances between consecutive corners
            "aspect_ratio": float (width / height in pixels)
            "message": str
    """
    h_img, w_img = image_rgb.shape[:2]
    img_area = h_img * w_img

    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    k = max(3, blur_kernel | 1)
    blurred = cv2.GaussianBlur(gray, (k, k), 0)

    candidates = []

    # Strategy A: Adaptive Thresholding (especially effective for hand-drawn sketches)
    if mode in ("auto", "sketch"):
        thresh_adapt = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )
        # Dilate slightly to connect disconnected sketch strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(thresh_adapt, kernel, iterations=1)
        cnts, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates.extend(cnts)

    # Strategy B: Canny Edge Detection + Morphological Close (great for photos/satellite maps)
    if mode in ("auto", "satellite", "photo"):
        edges = cv2.Canny(blurred, 40, 140)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates.extend(cnts)

    # Strategy C: Otsu's Global Thresholding (general contrast fallback)
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cnts_otsu, _ = cv2.findContours(otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates.extend(cnts_otsu)

    if not candidates:
        return _fallback_result(image_rgb, "No boundary contours could be extracted from image.")

    # Filter contours: must occupy between 2% and 98% of total image area
    valid_cnts = []
    for c in candidates:
        a = cv2.contourArea(c)
        if 0.02 * img_area < a < 0.98 * img_area:
            valid_cnts.append((a, c))

    if not valid_cnts:
        # If no internal contour matched, consider the largest available contour
        c_max = max(candidates, key=cv2.contourArea)
        if cv2.contourArea(c_max) > 0.005 * img_area:
            valid_cnts.append((cv2.contourArea(c_max), c_max))
        else:
            return _fallback_result(image_rgb, "No prominent plot boundary found. Please try adjusting the mode or lighting.")

    # Sort candidates by area descending
    valid_cnts.sort(key=lambda x: x[0], reverse=True)

    # Attempt to find the best 4-corner polygon first, else best convex polygon
    best_poly = None
    best_cnt = None
    best_area = 0.0

    for area, cnt in valid_cnts:
        peri = cv2.arcLength(cnt, True)
        # Try different epsilon values from 0.015 to 0.05
        for eps_factor in [0.02, 0.03, 0.04, 0.015, 0.05]:
            approx = cv2.approxPolyDP(cnt, eps_factor * peri, True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                best_poly = approx.reshape(-1, 2)
                best_cnt = cnt
                best_area = area
                break
        if best_poly is not None:
            break

    # If no 4-corner polygon found, accept the largest polygon with 3 to 8 vertices
    if best_poly is None:
        area, cnt = valid_cnts[0]
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
        if len(approx) >= 3:
            best_poly = approx.reshape(-1, 2)
            best_cnt = cnt
            best_area = area
        else:
            # Fall back to minimum area bounding box
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            best_poly = np.int32(box)
            best_cnt = cnt
            best_area = area

    corners = [(float(pt[0]), float(pt[1])) for pt in best_poly]
    n_pts = len(corners)
    is_quad = (n_pts == 4)

    # Side lengths in pixels
    side_lengths_px = []
    for i in range(n_pts):
        p1 = corners[i]
        p2 = corners[(i + 1) % n_pts]
        side_lengths_px.append(round(math.hypot(p2[0] - p1[0], p2[1] - p1[1]), 2))

    perimeter_px = float(sum(side_lengths_px))

    # Perspective rectification if quad
    warped_img = None
    ordered_corners = None
    aspect_ratio = 1.0

    if is_quad:
        ordered = order_points(np.array(corners, dtype="float32"))
        ordered_corners = [(float(p[0]), float(p[1])) for p in ordered]
        try:
            warped_img, warp_w, warp_h = four_point_transform(image_rgb, ordered)
            aspect_ratio = round(warp_w / max(warp_h, 1.0), 3)
        except Exception:
            warped_img = None

    # Draw annotated overlay image
    annotated = image_rgb.copy()
    pts_int = np.array(corners, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(annotated, [pts_int], isClosed=True, color=(0, 220, 255), thickness=3)

    # Draw corner pins and side length indicators
    for i, (x, y) in enumerate(corners):
        ix, iy = int(round(x)), int(round(y))
        cv2.circle(annotated, (ix, iy), 8, (255, 60, 0), -1)
        cv2.circle(annotated, (ix, iy), 10, (255, 255, 255), 2)
        cv2.putText(
            annotated, f"C{i+1}", (ix + 12, iy - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA
        )
        cv2.putText(
            annotated, f"C{i+1}", (ix + 12, iy - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA
        )

        # Label side length on midpoints
        p_next = corners[(i + 1) % n_pts]
        mx = int((x + p_next[0]) / 2)
        my = int((y + p_next[1]) / 2)
        dist_s = f"{side_lengths_px[i]:.0f}px"
        cv2.putText(annotated, dist_s, (mx - 20, my - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 2, cv2.LINE_AA)

    return {
        "success": True,
        "corners": corners,
        "ordered_corners": ordered_corners,
        "is_quadrilateral": is_quad,
        "perimeter_px": round(perimeter_px, 1),
        "area_px": round(best_area, 1),
        "warped_image": warped_img,
        "annotated_image": annotated,
        "side_lengths_px": side_lengths_px,
        "aspect_ratio": aspect_ratio,
        "message": f"Successfully detected {n_pts}-corner plot boundary."
    }


def _fallback_result(image_rgb: np.ndarray, message: str) -> dict:
    """Default fallback when contour extraction cannot isolate a boundary."""
    h, w = image_rgb.shape[:2]
    # Default to 80% inset bounding box
    margin_x = w * 0.1
    margin_y = h * 0.1
    corners = [
        (margin_x, margin_y),
        (w - margin_x, margin_y),
        (w - margin_x, h - margin_y),
        (margin_x, h - margin_y)
    ]
    return {
        "success": False,
        "corners": corners,
        "ordered_corners": corners,
        "is_quadrilateral": True,
        "perimeter_px": float(2 * ((w - 2 * margin_x) + (h - 2 * margin_y))),
        "area_px": float((w - 2 * margin_x) * (h - 2 * margin_y)),
        "warped_image": None,
        "annotated_image": image_rgb.copy(),
        "side_lengths_px": [float(w - 2 * margin_x), float(h - 2 * margin_y), float(w - 2 * margin_x), float(h - 2 * margin_y)],
        "aspect_ratio": round((w - 2 * margin_x) / max((h - 2 * margin_y), 1), 3),
        "message": message
    }
