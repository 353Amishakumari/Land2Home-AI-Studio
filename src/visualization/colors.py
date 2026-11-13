"""
Land2Home — shared room colour constants.

All visualisation modules import from here so colours stay consistent
across the 2D plan, 3D view and PDF report.
"""

# ---------------------------------------------------------------------------
# Room fill colours (hex strings)
# ---------------------------------------------------------------------------
ROOM_COLORS: dict[str, str] = {
    "Living Room":  "#FFFACD",   # LemonChiffon  — warm yellow
    "Hall":         "#FFFACD",
    "Bedroom 1":    "#ADD8E6",   # LightBlue
    "Bedroom 2":    "#AED6F1",   # slightly deeper blue
    "Bedroom 3":    "#85C1E9",
    "Bedroom 4":    "#7FB3D3",
    "Kitchen":      "#FFDAB9",   # Peach / PapayaWhip
    "Bathroom 1":   "#E0FFFF",   # Cyan / LightCyan
    "Bathroom 2":   "#B2EBF2",
    "Passage":      "#FFF8DC",   # Cornsilk / Cream
    "Corridor":     "#FFF8DC",
    "Staircase":    "#C0C0C0",   # Silver
    "Parking":      "#D3D3D3",   # LightGrey
    "Garden":       "#90EE90",   # LightGreen
    "Dining Room":  "#E6E6FA",   # Lavender
    "Balcony":      "#98FB98",   # PaleGreen
    "Store Room":   "#DEB887",   # BurlyWood / Light Brown
    "Pooja Room":   "#FFE4B5",   # Moccasin
    "Utility":      "#F5DEB3",   # Wheat
    "Open Living":  "#FFFACD",
}

# Edge / border colours
ROOM_EDGE_COLOR = "#2C3E50"
PLOT_EDGE_COLOR = "#1A1A1A"
GARDEN_EDGE    = "#27AE60"
PARKING_EDGE   = "#626567"

# Wall colour for 3D (a slightly desaturated version of the fill)
def wall_color(hex_fill: str, darken: float = 0.75) -> str:
    """Return a slightly darkened hex colour for 3D walls."""
    hex_fill = hex_fill.lstrip("#")
    r, g, b = int(hex_fill[0:2], 16), int(hex_fill[2:4], 16), int(hex_fill[4:6], 16)
    r = int(r * darken); g = int(g * darken); b = int(b * darken)
    return f"#{r:02x}{g:02x}{b:02x}"


def get_room_color(name: str) -> str:
    """Return fill colour for a room by name, falling back gracefully."""
    # Exact match
    if name in ROOM_COLORS:
        return ROOM_COLORS[name]
    # Partial keyword match
    keywords = {
        "Living":   "#FFFACD",
        "Bedroom":  "#ADD8E6",
        "Kitchen":  "#FFDAB9",
        "Bathroom": "#E0FFFF",
        "Bath":     "#E0FFFF",
        "WC":       "#E0FFFF",
        "Passage":  "#FFF8DC",
        "Corridor": "#FFF8DC",
        "Stair":    "#C0C0C0",
        "Parking":  "#D3D3D3",
        "Garden":   "#90EE90",
        "Dining":   "#E6E6FA",
        "Balcony":  "#98FB98",
        "Store":    "#DEB887",
        "Pooja":    "#FFE4B5",
        "Utility":  "#F5DEB3",
        "Hall":     "#FFFACD",
    }
    for key, color in keywords.items():
        if key.lower() in name.lower():
            return color
    return "#F0F0F0"   # neutral default


# Legend entries: (label, hex_colour) — only the main room types
LEGEND_ENTRIES = [
    ("Living Room / Hall", "#FFFACD"),
    ("Bedroom",            "#ADD8E6"),
    ("Kitchen",            "#FFDAB9"),
    ("Bathroom",           "#E0FFFF"),
    ("Dining Room",        "#E6E6FA"),
    ("Passage / Corridor", "#FFF8DC"),
    ("Staircase",          "#C0C0C0"),
    ("Parking",            "#D3D3D3"),
    ("Garden",             "#90EE90"),
    ("Balcony",            "#98FB98"),
    ("Store Room",         "#DEB887"),
    ("Pooja Room",         "#FFE4B5"),
    ("Utility",            "#F5DEB3"),
]
