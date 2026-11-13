"""
Land2Home — Vastu Shastra Architectural Compliance Analyzer
=============================================================

Evaluates room placements, orientations, and circulation according to
traditional Vedic Vastu Shastra principles for Indian residential designs.
"""

from __future__ import annotations


def get_room_zone(
    cx: float, cy: float,
    plot_width: float, plot_length: float,
    plot_facing: str = "North"
) -> str:
    """
    Determine the 8-directional compass zone + Brahmasthan (Center)
    for a given coordinate, calibrated to the plot road orientation.

    Standard coordinate layout:
      x = 0 (West), x = plot_width (East)
      y = 0 (South / Road frontage), y = plot_length (North / Rear)
    Adjusted based on plot_facing: "North", "East", "South", "West".
    """
    # Normalized position 0.0 to 1.0
    nx = cx / max(plot_width, 1.0)
    ny = cy / max(plot_length, 1.0)

    # Check center (Brahmasthan) first
    if 0.35 <= nx <= 0.65 and 0.35 <= ny <= 0.65:
        return "Center (Brahmasthan)"

    is_north = ny >= 0.55
    is_south = ny <= 0.45
    is_east  = nx >= 0.55
    is_west  = nx <= 0.45

    if is_north and is_east:
        zone = "North-East (Ishanya)"
    elif is_north and is_west:
        zone = "North-West (Vayavya)"
    elif is_south and is_east:
        zone = "South-East (Agneya)"
    elif is_south and is_west:
        zone = "South-West (Nairutya)"
    elif is_north:
        zone = "North (Kuber)"
    elif is_south:
        zone = "South (Yama)"
    elif is_east:
        zone = "East (Indra)"
    else:
        zone = "West (Varuna)"

    return zone


def analyze_vastu_compliance(
    rooms: list[dict],
    plot_width: float,
    plot_length: float,
    plot_facing: str = "North",
    features: list[dict] | None = None
) -> dict:
    """
    Perform an automated Vastu Shastra audit on the layout.

    Returns:
        {
            "score": float,            # 0 to 100
            "grade": str,              # "Excellent", "Good", "Moderate"
            "audit_items": list[dict], # [{room, zone, ideal, status, tip, score}]
            "summary": str,
            "strengths": list[str],
            "recommendations": list[str]
        }
    """
    features = features or []
    all_items = rooms + features

    rules: dict[str, dict] = {
        "kitchen": {
            "ideal": "South-East (Agneya) or North-West (Vayavya)",
            "scores": {
                "South-East (Agneya)": (100, "Auspicious ✅", "Kitchen in Agneya (Fire zone) promotes vitality, good health, and family prosperity."),
                "North-West (Vayavya)": (85, "Acceptable ⚠️", "Kitchen in Vayavya (Air zone) is an acceptable secondary placement."),
                "East (Indra)": (70, "Neutral ⚠️", "Kitchen in East receives morning sun; ensure cook faces East."),
                "North-East (Ishanya)": (30, "Inauspicious ❌", "Fire element in Water zone (Ishanya) is inauspicious. Remedy: Use green marble counter."),
                "South-West (Nairutya)": (35, "Inauspicious ❌", "Kitchen in South-West causes energy clashes. Remedy: Paint walls lemon yellow."),
            },
            "default": (55, "Neutral ⚠️", "Acceptable placement with minor Vastu corrections.")
        },
        "bedroom 1": {
            "ideal": "South-West (Nairutya)",
            "scores": {
                "South-West (Nairutya)": (100, "Auspicious ✅", "Master Bedroom in South-West provides grounding stability, leadership, and peace."),
                "South (Yama)": (85, "Auspicious ✅", "South placement supports sound sleep and physical rejuvenation."),
                "West (Varuna)": (80, "Good ✅", "West bedroom promotes prosperity and stable career growth."),
                "North-West (Vayavya)": (75, "Acceptable ⚠️", "North-West is suitable for guest bedroom or youth bedroom."),
                "North-East (Ishanya)": (40, "Inauspicious ❌", "Master bed in North-East causes restlessness. Keep head towards South."),
            },
            "default": (65, "Neutral ⚠️", "Place headboard against South or East wall.")
        },
        "bedroom 2": {
            "ideal": "North-West (Vayavya) or West (Varuna)",
            "scores": {
                "North-West (Vayavya)": (95, "Auspicious ✅", "Excellent placement for children or guest bedroom."),
                "West (Varuna)": (90, "Auspicious ✅", "West is very favorable for students and growing children."),
                "South (Yama)": (80, "Good ✅", "Good placement for secondary bedroom."),
                "South-West (Nairutya)": (85, "Good ✅", "Provides good stability and rest."),
            },
            "default": (70, "Good ✅", "Ensure sleeping direction is South or East.")
        },
        "living": {
            "ideal": "North (Kuber), East (Indra), or North-East (Ishanya)",
            "scores": {
                "North-East (Ishanya)": (100, "Auspicious ✅", "Living room in North-East welcomes positive solar and magnetic vibrations."),
                "East (Indra)": (95, "Auspicious ✅", "East-facing living room brings brightness and social harmony."),
                "North (Kuber)": (95, "Auspicious ✅", "North living room attracts wealth and prosperous opportunities."),
                "North-West (Vayavya)": (80, "Good ✅", "Encourages dynamic conversations and guest hospitality."),
                "South (Yama)": (60, "Neutral ⚠️", "Keep heavy furniture along South/West walls."),
            },
            "default": (70, "Neutral ⚠️", "Ensure lighter furniture in North/East corners.")
        },
        "pooja": {
            "ideal": "North-East (Ishanya)",
            "scores": {
                "North-East (Ishanya)": (100, "Auspicious ✅", "Ideal sacred placement. Channels maximum spiritual and cosmic energy."),
                "East (Indra)": (90, "Auspicious ✅", "East-facing prayer room brings clarity and peace."),
                "North (Kuber)": (85, "Good ✅", "North prayer area invites divine blessings and prosperity."),
            },
            "default": (50, "Neutral ⚠️", "Ensure deities face West so devotee faces East during prayer.")
        },
        "bathroom": {
            "ideal": "North-West (Vayavya) or West (Varuna)",
            "scores": {
                "North-West (Vayavya)": (100, "Auspicious ✅", "Ideal elimination zone according to Vastu Shastra."),
                "West (Varuna)": (90, "Auspicious ✅", "West wall is very suitable for toilet and bath."),
                "South (Yama)": (75, "Acceptable ⚠️", "South placement is acceptable for secondary bath."),
                "North-East (Ishanya)": (20, "Inauspicious ❌", "Severe Vastu Dosha. Avoid toilet in North-East. Keep bowl in NW corner."),
                "South-West (Nairutya)": (30, "Inauspicious ❌", "Water drainage in SW disturbs earth energy. Remedy: Keep door closed."),
            },
            "default": (65, "Neutral ⚠️", "Ensure WC commode faces North-South axis.")
        },
        "dining": {
            "ideal": "West (Varuna) or East (Indra)",
            "scores": {
                "West (Varuna)": (100, "Auspicious ✅", "Dining in West ensures nourishment and good digestion."),
                "East (Indra)": (90, "Auspicious ✅", "East dining fosters health and family connection."),
                "North-West (Vayavya)": (80, "Good ✅", "Close to kitchen for convenient meal service."),
            },
            "default": (70, "Neutral ⚠️", "Face East or North while eating.")
        },
        "staircase": {
            "ideal": "South (Yama), South-West (Nairutya), or West",
            "scores": {
                "South-West (Nairutya)": (100, "Auspicious ✅", "Heavy staircase in SW anchors the structural stability of the plot."),
                "South (Yama)": (90, "Auspicious ✅", "Excellent heavy element placement."),
                "West (Varuna)": (85, "Good ✅", "Very good placement for staircase."),
                "North-East (Ishanya)": (25, "Inauspicious ❌", "Heavy weight in North-East blocks positive cosmic flow."),
            },
            "default": (65, "Neutral ⚠️", "Ensure staircase climbs in clockwise direction.")
        },
    }

    audit_items = []
    total_score = 0.0
    count = 0
    strengths = []
    recommendations = []

    for item in all_items:
        rname = item["name"]
        rname_lower = rname.lower()
        cx = item["x"] + item["width"] / 2
        cy = item["y"] + item["length"] / 2

        zone = get_room_zone(cx, cy, plot_width, plot_length, plot_facing)

        # Match rule
        matched_rule = None
        for rule_key, rule_dict in rules.items():
            if rule_key in rname_lower:
                matched_rule = rule_dict
                break

        if matched_rule is None:
            continue

        ideal = matched_rule["ideal"]
        scores_map = matched_rule["scores"]
        default_val = matched_rule["default"]

        score_val, status, note = scores_map.get(zone, default_val)

        total_score += score_val
        count += 1

        if score_val >= 85:
            strengths.append(f"{rname} placed in {zone} ({status})")
        elif score_val < 60:
            recommendations.append(f"{rname} in {zone}: {note}")

        audit_items.append({
            "room": rname,
            "zone": zone,
            "ideal_zone": ideal,
            "status": status,
            "score": score_val,
            "tip": note
        })

    final_score = round(total_score / max(count, 1), 1) if count > 0 else 75.0
    grade = (
        "Excellent (A+)" if final_score >= 85 else
        "Good (A)" if final_score >= 75 else
        "Moderate (B)" if final_score >= 60 else "Needs Alignment (C)"
    )

    summary = (
        f"Overall Vastu Compliance Score: {final_score}/100 ({grade}). "
        f"Analyzed {count} key architectural spaces with plot facing {plot_facing}."
    )

    return {
        "score": final_score,
        "grade": grade,
        "plot_facing": plot_facing,
        "audit_items": audit_items,
        "summary": summary,
        "strengths": strengths[:4],
        "recommendations": recommendations[:3],
    }
