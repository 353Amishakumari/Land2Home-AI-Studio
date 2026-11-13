"""
Land2Home — layout optimization and design scoring.
"""

from __future__ import annotations
from src.evaluation.metrics import score_layout


def generate_alternatives(plot_width: float, plot_length: float,
                           requirements: dict) -> list[dict]:
    """
    Generate and rank all three design alternatives.

    Each design is scored on 7 criteria (see evaluation/metrics.py).
    Returns a list sorted by total score (highest first).
    """
    from .floorplan_generator import generate_all_designs
    designs = generate_all_designs(plot_width, plot_length, requirements)

    alternatives = []
    for design in designs:
        alternatives.append({
            "design_id":          design["design_id"],
            "design_name":        design["design_name"],
            "design_description": design["design_description"],
            "layout":             design,                  # full design dict
            "score":              design["score"]["total"],
            "grade":              design["score"]["grade"],
            "breakdown":          design["score"]["breakdown"],
            "validation":         design["validation"],
        })

    return sorted(alternatives, key=lambda x: x["score"], reverse=True)


def rank_designs(designs: list[dict]) -> list[dict]:
    """
    Re-rank an already-generated list of designs by their score.
    Returns the same list sorted highest-score first.
    """
    return sorted(designs, key=lambda d: d.get("score", {}).get("total", 0), reverse=True)


def best_design(designs: list[dict]) -> dict:
    """Return the single highest-scoring design from the list."""
    ranked = rank_designs(designs)
    return ranked[0] if ranked else {}
