"""
Land2Home — room-adjacency graph and connectivity validation.
"""

from __future__ import annotations
import networkx as nx


# ---------------------------------------------------------------------------
# Preferred adjacency rules (used for scoring)
# ---------------------------------------------------------------------------

_PREFERRED_EDGES = [
    ("Living Room",  "Kitchen"),
    ("Living Room",  "Dining Room"),
    ("Living Room",  "Passage"),
    ("Living Room",  "Corridor"),
    ("Dining Room",  "Kitchen"),
    ("Passage",      "Bathroom 1"),
    ("Passage",      "Bathroom 2"),
    ("Corridor",     "Bedroom 1"),
    ("Corridor",     "Bedroom 2"),
    ("Corridor",     "Bedroom 3"),
    ("Corridor",     "Bedroom 4"),
    ("Corridor",     "Bathroom 1"),
    ("Corridor",     "Bathroom 2"),
    ("Passage",      "Bedroom 1"),
    ("Passage",      "Bedroom 2"),
]

_DISCOURAGED_EDGES = [
    # Bathroom directly off kitchen is undesirable
    ("Kitchen", "Bathroom 1"),
    ("Kitchen", "Bathroom 2"),
]


def build_room_graph(requirements: dict) -> nx.Graph:
    """
    Build a *preferred* room-adjacency graph from the requirements dict.

    This graph captures the architect-ideal connectivity. It is compared
    against the actual geometric adjacency to produce a score.
    """
    graph = nx.Graph()
    n_bed  = requirements.get("bedrooms", 1)
    n_bath = requirements.get("bathrooms", 1)

    # Core nodes
    graph.add_node("Living Room",  room_type="common")
    graph.add_node("Kitchen",      room_type="service")
    graph.add_edge("Living Room", "Kitchen", preferred=True)

    if requirements.get("dining_room"):
        graph.add_node("Dining Room", room_type="semi-public")
        graph.add_edge("Living Room", "Dining Room", preferred=True)
        graph.add_edge("Dining Room", "Kitchen",     preferred=True)

    # Passage / Corridor node (generic circulation)
    graph.add_node("Passage", room_type="circulation")
    graph.add_edge("Living Room", "Passage", preferred=True)

    # Bedrooms
    for idx in range(1, n_bed + 1):
        bname = f"Bedroom {idx}"
        graph.add_node(bname, room_type="private")
        graph.add_edge("Passage", bname, preferred=True)

    # Bathrooms — connected from passage (not bedrooms)
    for idx in range(1, n_bath + 1):
        bname = f"Bathroom {idx}"
        graph.add_node(bname, room_type="service")
        graph.add_edge("Passage", bname, preferred=True)

    # Optional amenities
    if requirements.get("parking"):
        graph.add_node("Parking", room_type="external")
        graph.add_edge("Parking", "Living Room", preferred=False)

    if requirements.get("staircase"):
        graph.add_node("Staircase", room_type="circulation")
        graph.add_edge("Living Room", "Staircase", preferred=True)
        graph.add_edge("Passage",    "Staircase", preferred=True)

    if requirements.get("balcony"):
        graph.add_node("Balcony", room_type="external")
        graph.add_edge("Living Room", "Balcony", preferred=True)

    if requirements.get("store_room"):
        graph.add_node("Store Room", room_type="service")
        graph.add_edge("Passage", "Store Room", preferred=True)

    if requirements.get("pooja_room"):
        graph.add_node("Pooja Room", room_type="semi-public")
        graph.add_edge("Living Room", "Pooja Room", preferred=True)

    if requirements.get("utility"):
        graph.add_node("Utility", room_type="service")
        graph.add_edge("Kitchen", "Utility", preferred=True)

    return graph


def score_adjacency(ideal_graph: nx.Graph,
                    actual_rooms: list[dict]) -> dict:
    """
    Compare the ideal adjacency graph against the actual geometric layout.

    Counts how many preferred edges from the ideal graph are satisfied in
    the actual layout (rooms that share a wall or open circulation).

    Returns:
        {"satisfied": int, "total": int, "pct": float, "unsatisfied": list[str]}
    """
    from .constraints import build_adjacency_graph
    actual_graph = build_adjacency_graph(actual_rooms)

    def _find_actual_nodes(ideal_node: str) -> list[str]:
        matches = []
        for n in actual_graph.nodes:
            if n == ideal_node:
                matches.append(n)
            elif ideal_node in ("Living Room", "Dining Room") and ("Living" in n and "Dining" in n):
                matches.append(n)
            elif ideal_node in ("Passage", "Corridor") and n in ("Passage", "Corridor", "Circulation"):
                matches.append(n)
        return matches

    satisfied   = 0
    unsatisfied = []
    preferred_edges = [(u, v) for u, v, d in ideal_graph.edges(data=True) if d.get("preferred")]

    for u, v in preferred_edges:
        nodes_u = _find_actual_nodes(u)
        nodes_v = _find_actual_nodes(v)

        if not nodes_u or not nodes_v:
            # If one of the rooms is not in this design, skip
            continue

        # If u and v mapped to the same merged room (e.g. Open Living + Dining)
        if any(nu == nv for nu in nodes_u for nv in nodes_v):
            satisfied += 1
            continue

        edge_found = False
        for nu in nodes_u:
            for nv in nodes_v:
                if actual_graph.has_edge(nu, nv):
                    edge_found = True
                    break
            if edge_found:
                break

        if edge_found:
            satisfied += 1
        else:
            unsatisfied.append(f"{u} ↔ {v}")

    total = max(len(preferred_edges), 1)
    return {
        "satisfied":   satisfied,
        "total":       total,
        "pct":         round(satisfied / total * 100, 1),
        "unsatisfied": unsatisfied,
    }


def validate_connectivity(rooms: list[dict],
                           requirements: dict) -> dict:
    """
    Full connectivity validation: geometric adjacency + ideal-graph comparison.
    """
    from .constraints import connectivity_check
    geo_result = connectivity_check(rooms)
    ideal_g    = build_room_graph(requirements)
    adj_score  = score_adjacency(ideal_g, rooms)
    return {**geo_result, "adjacency_score": adj_score}
