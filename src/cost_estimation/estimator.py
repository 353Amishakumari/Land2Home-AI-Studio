"""
Land2Home — Construction Cost & Material Quantity Estimator (BOQ)
==================================================================

Computes detailed residential construction budget forecasts, phase-wise
milestone cashflows, and primary material takeoff quantities for Indian
residential construction.
"""

from __future__ import annotations

# Construction rates per square foot of built-up area (Indian standard rates in INR)
TIER_RATES: dict[str, float] = {
    "Basic": 1600.0,      # Standard red bricks, vitrified tiles, basic fittings
    "Standard": 2100.0,   # High-grade cement/steel, granite counters, branded CP fittings, modular electricals
    "Premium": 2800.0,    # Italian marble/hardwood, teakwood frames, smart switches, designer sanitaryware
}

# Milestone breakdown percentages across standard residential project lifecycle
PHASE_PERCENTAGES: list[tuple[str, float, str]] = [
    ("Foundation & Substructure", 0.20, "Excavation, PCC, RCC Footings, Plinth Beam, Anti-termite treatment"),
    ("RCC Superstructure Frame", 0.18, "Columns, Beams, Roof Slab casting, Staircase RCC work"),
    ("Brickwork & Masonry", 0.14, "External 9-inch and internal 4.5-inch brick/AAC block walls"),
    ("Plastering & Waterproofing", 0.10, "Internal ceiling/wall plaster, external waterproof plaster, sunken slab treatment"),
    ("Flooring & Wall Tiling", 0.12, "Vitrified tiles, skirting, bathroom anti-skid tiles & wall dado"),
    ("Doors, Windows & Joinery", 0.10, "Main door teak frame, internal flush doors, UPVC/aluminum sliding windows"),
    ("Plumbing & Electrical Lines", 0.09, "Concealed conduit wiring, switchboards, CPVC/UPVC water supply & drainage pipes"),
    ("Painting & Final Finishing", 0.07, "Wall putty, primer coats, interior premium emulsion, exterior weathercoat paint"),
]


def estimate_construction_cost(
    built_up_area_sqft: float,
    tier: str = "Standard"
) -> dict:
    """
    Compute comprehensive construction cost estimation, milestone cashflows,
    and bill of quantities (BOQ) material takeoffs.

    Args:
        built_up_area_sqft: Total covered built-up area in square feet.
        tier: "Basic" | "Standard" | "Premium"

    Returns:
        Structured dict with total cost (INR and Lakhs), phase breakdown,
        and material quantity takeoffs.
    """
    area = max(float(built_up_area_sqft), 1.0)
    rate = TIER_RATES.get(tier, TIER_RATES["Standard"])
    total_cost = area * rate
    total_lakhs = total_cost / 100000.0

    # Phase-wise cost breakdown
    phase_breakdown = []
    for name, pct, desc in PHASE_PERCENTAGES:
        phase_cost = total_cost * pct
        phase_breakdown.append({
            "phase": name,
            "pct": round(pct * 100, 1),
            "cost_inr": round(phase_cost, 0),
            "cost_lakhs": round(phase_cost / 100000.0, 2),
            "description": desc,
        })

    # Material quantity takeoffs (empirical Indian construction estimation rules of thumb)
    # 1. Cement: ~0.40 to 0.45 bags per sq.ft built-up area
    cement_bags = round(area * 0.42)
    # 2. Steel (TMT 500D bars): ~3.5 to 4.0 kg per sq.ft
    steel_kg = round(area * 3.65)
    steel_tonnes = round(steel_kg / 1000.0, 2)
    # 3. Bricks (Red modular / fly-ash / AAC): ~18 to 20 bricks per sq.ft
    bricks_count = round(area * 18.5)
    # 4. Sand (M-Sand / River sand): ~1.8 to 2.0 cu.ft per sq.ft
    sand_cft = round(area * 1.85)
    # 5. Coarse Aggregate (10mm / 20mm blue metal): ~1.3 to 1.4 cu.ft per sq.ft
    aggregate_cft = round(area * 1.35)
    # 6. Flooring tiles (including 10% wastage): ~1.15 sq.ft per sq.ft built area
    tiles_sqft = round(area * 1.12)
    # 7. Paint (Primer + 2 coats interior/exterior): ~0.18 liters per sq.ft
    paint_litres = round(area * 0.18)

    materials = {
        "Cement (50 kg bags)": {"quantity": cement_bags, "unit": "bags", "note": "OPC 53 for RCC, PPC for masonry/plaster"},
        "Structural Steel (TMT Fe 500D)": {"quantity": steel_kg, "unit": "kg", "note": f"Approx {steel_tonnes} Metric Tonnes"},
        "Masonry Bricks / AAC Blocks": {"quantity": bricks_count, "unit": "pcs", "note": "Standard modular bricks or equivalent AAC blocks"},
        "Sand / Fine Aggregate (M-Sand)": {"quantity": sand_cft, "unit": "cu.ft", "note": "Zone-II manufactured sand for concrete & plaster"},
        "Coarse Aggregate (10/20 mm)": {"quantity": aggregate_cft, "unit": "cu.ft", "note": "Clean, angular hard blue metal granite"},
        "Flooring & Wall Tiles": {"quantity": tiles_sqft, "unit": "sq.ft", "note": "Includes 10% cutting wastage allowance"},
        "Interior & Exterior Paint": {"quantity": paint_litres, "unit": "litres", "note": "Putty base + 1 coat primer + 2 coats premium finish"},
    }

    return {
        "tier": tier,
        "rate_per_sqft": rate,
        "built_up_area_sqft": round(area, 1),
        "total_cost_inr": round(total_cost, 0),
        "total_cost_lakhs": round(total_lakhs, 2),
        "formatted_cost": f"₹ {total_lakhs:.2f} Lakhs",
        "phase_breakdown": phase_breakdown,
        "materials": materials,
    }
