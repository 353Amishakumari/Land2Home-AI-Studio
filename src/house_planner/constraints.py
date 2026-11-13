"""
Land2Home — layout constraint checkers.

Uses Shapely for geometric validation and NetworkX for connectivity checks.
"""

from __future__ import annotations
import networkx as nx
from shapely.geometry import box


# ---------------------------------------------------------------------------
# Geometric constraints
# ---------------------------------------------------------------------------

def check_rectangular_layout(rooms: list[dict],
                              plot_width: float,
                              plot_length: float) -> dict:
    """
    Verify that all room rectangles:
      • lie inside the plot boundary,
      • have positive dimensions,
      • do not overlap each other.

    Returns:
        {"valid": bool, "issues": list[str], "warnings": list[str]}
    """
    issues: list[str]   = []
    warnings: list[str] = []
    shapes: list        = []

    for room in rooms:
        w = room.get("width", 0)
        h = room.get("length", 0)
        x = room.get("x", 0)
        y = room.get("y", 0)
        name = room.get("name", "?")

        if w <= 0 or h <= 0:
            issues.append(f"'{name}' has non-positive dimensions ({w:.1f}×{h:.1f} ft).")
            continue

        if x < -0.01 or y < -0.01:
            issues.append(f"'{name}' origin ({x:.1f}, {y:.1f}) is outside the plot.")
        if x + w > plot_width + 0.01:
            issues.append(f"'{name}' exceeds the east plot boundary (x+w={x+w:.1f} > {plot_width:.1f}).")
        if y + h > plot_length + 0.01:
            issues.append(f"'{name}' exceeds the north plot boundary (y+h={y+h:.1f} > {plot_length:.1f}).")

        shapes.append((name, box(x, y, x + w, y + h)))

    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            overlap = shapes[i][1].intersection(shapes[j][1]).area
            if overlap > 0.25:        # Significant physical room overlap (> 3 inches of room collision)
                issues.append(f"'{shapes[i][0]}' overlaps '{shapes[j][0]}' by {overlap:.1f} sqft.")
            elif overlap > 0.05:     # Tiny numerical boundary precision noise
                warnings.append(f"Tiny overlap between '{shapes[i][0]}' and '{shapes[j][0]}'.")

    return {"valid": len(issues) == 0, "issues": issues, "warnings": warnings}


# ---------------------------------------------------------------------------
# Dimension sanity
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


def dimension_sanity_check(rooms: list[dict]) -> list[str]:
    """
    Return a list of warning strings for rooms that are smaller than the
    recommended minimum dimensions, evaluated orientation-independently.
    Does not block layout generation.
    """
    warnings: list[str] = []
    for room in rooms:
        name = room.get("name", "").lower()
        w    = room.get("width", 0)
        h    = room.get("length", 0)
        dim_min = min(w, h)
        dim_max = max(w, h)
        for key, (mw, mh) in _MIN_DIM.items():
            if key in name:
                req_min = min(mw, mh)
                req_max = max(mw, mh)
                # Check orientation-independently with tolerance
                if dim_min < (req_min - 0.25) or dim_max < (req_max - 0.25):
                    warnings.append(
                        f"'{room['name']}' ({w:.1f}×{h:.1f} ft) is below the "
                        f"recommended {req_min:.0f}×{req_max:.0f} ft minimum."
                    )
                break
    return warnings


# ---------------------------------------------------------------------------
# Graph-based connectivity
# ---------------------------------------------------------------------------

def build_adjacency_graph(rooms: list[dict], tolerance: float = 0.3) -> nx.Graph:
    """
    Build a room-adjacency graph based on shared wall segments.

    Two rooms are adjacent if their bounding boxes share an edge of length
    ≥ tolerance feet. The graph is used for connectivity validation.
    """
    graph = nx.Graph()
    for room in rooms:
        graph.add_node(room["name"], **room)

    for i in range(len(rooms)):
        for j in range(i + 1, len(rooms)):
            a, b = rooms[i], rooms[j]
            # Compute shared boundary length
            shared = _shared_edge_length(a, b)
            if shared >= tolerance:
                graph.add_edge(a["name"], b["name"], shared_ft=round(shared, 2))
    return graph


def _shared_edge_length(a: dict, b: dict) -> float:
    """Return the length of the shared boundary between two rectangles (0 if none)."""
    # Horizontal shared edge (a and b touch vertically)
    if abs((a["y"] + a["length"]) - b["y"]) < 0.05 or abs((b["y"] + b["length"]) - a["y"]) < 0.05:
        overlap_x = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
        return max(0.0, overlap_x)
    # Vertical shared edge (a and b touch horizontally)
    if abs((a["x"] + a["width"]) - b["x"]) < 0.05 or abs((b["x"] + b["width"]) - a["x"]) < 0.05:
        overlap_y = min(a["y"] + a["length"], b["y"] + b["length"]) - max(a["y"], b["y"])
        return max(0.0, overlap_y)
    return 0.0


def connectivity_check(rooms: list[dict],
                        entrance_room: str = "Living Room") -> dict:
    """
    Verify that all rooms are reachable from the entrance room via shared
    walls (adjacency graph). Private rooms (bedrooms) should not be the
    only path to service rooms (bathrooms, kitchen).

    Returns:
        {"connected": bool, "issues": list[str], "warnings": list[str]}
    """
    graph   = build_adjacency_graph(rooms)
    issues: list[str]   = []
    warnings: list[str] = []

    if entrance_room not in graph:
        # Fall back: use first room as entrance
        entrance_room = rooms[0]["name"] if rooms else ""

    if not entrance_room:
        issues.append("No rooms to validate connectivity for.")
        return {"connected": False, "issues": issues, "warnings": warnings}

    # Check all rooms are reachable from entrance
    unreachable = []
    for node in graph.nodes:
        if not nx.has_path(graph, entrance_room, node):
            unreachable.append(node)
    if unreachable:
        issues.append(f"Rooms not reachable from {entrance_room}: {', '.join(unreachable)}")

    # Warn if bathroom is only accessible through a bedroom
    bathroom_nodes = [n for n in graph.nodes if "bathroom" in n.lower() or "bath" in n.lower()]
    bedroom_nodes  = {n for n in graph.nodes if "bedroom" in n.lower()}
    for bath in bathroom_nodes:
        all_paths = list(nx.all_simple_paths(graph, entrance_room, bath, cutoff=6))
        if all_paths and all(any(n in bedroom_nodes for n in path) for path in all_paths):
            warnings.append(
                f"'{bath}' may only be accessible through a bedroom. "
                "Consider adding a passage connection."
            )

    return {
        "connected": len(issues) == 0,
        "issues":    issues,
        "warnings":  warnings,
    }


def buildable_dimensions(width: float, length: float, setback_ft: float = 0.0):
    """Simple equal setback inset (kept for backward compatibility)."""
    usable_width  = width  - 2 * setback_ft
    usable_length = length - 2 * setback_ft
    if usable_width <= 0 or usable_length <= 0:
        raise ValueError("Setback leaves no usable plot area.")
    return usable_width, usable_length
