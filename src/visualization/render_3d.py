"""
Land2Home — Interactive 3D Visualization (Plotly)
==================================================

Creates an open-top 3D residential model using Plotly go.Mesh3d.
Each room is rendered as a coloured box (floor + 4 walls, no ceiling).
Features (parking, garden) are rendered as flat coloured slabs.

Returns a plotly.graph_objects.Figure for use with st.plotly_chart().
"""

from __future__ import annotations
import plotly.graph_objects as go
from src.visualization.colors import get_room_color, wall_color

# Wall height in feet (default for a standard room)
_WALL_H = 9.0
_GARDEN_H = 0.3
_PARKING_H = 0.2


def create_3d_view(rooms: list[dict],
                   plot_width: float,
                   plot_length: float,
                   features: list[dict] | None = None,
                   design_name: str = "",
                   wall_height: float = _WALL_H) -> go.Figure:
    """
    Build an interactive Plotly 3D model for the given layout.

    Args:
        rooms:        list of room dicts from generate_all_designs().
        plot_width:   total plot width in feet.
        plot_length:  total plot length in feet.
        features:     parking / garden amenity dicts.
        design_name:  shown in the figure title.
        wall_height:  room wall height in feet (default 9 ft).

    Returns:
        plotly Figure with interactive 3D scene.
    """
    features = features or []
    traces   = []

    # ---- Draw features (flat slabs) ----
    for feat in features:
        h = _GARDEN_H if "garden" in feat["name"].lower() else _PARKING_H
        col = get_room_color(feat["name"])
        traces.extend(_room_mesh(feat["x"], feat["y"],
                                 feat["width"], feat["length"],
                                 h, col, opacity=0.75))
        traces.append(_label(feat["name"], feat["x"] + feat["width"] / 2,
                             feat["y"] + feat["length"] / 2, h + 0.5, fontsize=10))

    # ---- Draw rooms ----
    for room in rooms:
        h = wall_height * 0.5 if room.get("kind") == "staircase" else wall_height
        col = room.get("color", get_room_color(room["name"]))
        traces.extend(_room_mesh(room["x"], room["y"],
                                 room["width"], room["length"],
                                 h, col, opacity=0.55))
        # Room label at ceiling level
        area = room["width"] * room["length"]
        label_text = (f"<b>{room['name']}</b><br>"
                      f"{room['width']:.1f}×{room['length']:.1f} ft  "
                      f"({area:.0f} sqft)")
        traces.append(_label(label_text,
                             room["x"] + room["width"] / 2,
                             room["y"] + room["length"] / 2,
                             h + 0.4, fontsize=9))

    # ---- Plot boundary box (wireframe) ----
    traces.append(_plot_boundary(plot_width, plot_length, wall_height))

    # ---- Assemble figure ----
    title = f"Land2Home — 3D Concept View  |  {plot_width:.0f} × {plot_length:.0f} ft"
    if design_name:
        title += f"  |  {design_name}"

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#1A1A1A"), x=0.02),
        scene=dict(
            xaxis=dict(title="Width (ft)", showgrid=True, gridcolor="#DDD",
                       backgroundcolor="#F5F5F0", range=[0, plot_width]),
            yaxis=dict(title="Length (ft)", showgrid=True, gridcolor="#DDD",
                       backgroundcolor="#F5F5F0", range=[0, plot_length]),
            zaxis=dict(title="Height (ft)", showgrid=True, gridcolor="#DDD",
                       backgroundcolor="#EEF0F5", range=[0, wall_height + 2]),
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=1.2),
                up=dict(x=0, y=0, z=1),
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=plot_width / max(plot_width, plot_length),
                y=1.0,
                z=0.5,
            ),
            bgcolor="#F8F8F4",
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#F8F8F4",
        height=680,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Mesh helpers
# ---------------------------------------------------------------------------

def _room_mesh(x0: float, y0: float, w: float, l: float, h: float,
               color: str, opacity: float = 0.55) -> list[go.Mesh3d]:
    """
    Return a list of go.Mesh3d traces for one room (floor + 4 walls).

    Vertices:
      0: (x0,   y0,   0)  bottom-south-west
      1: (x0+w, y0,   0)  bottom-south-east
      2: (x0+w, y0+l, 0)  bottom-north-east
      3: (x0,   y0+l, 0)  bottom-north-west
      4: (x0,   y0,   h)  top-south-west
      5: (x0+w, y0,   h)  top-south-east
      6: (x0+w, y0+l, h)  top-north-east
      7: (x0,   y0+l, h)  top-north-west
    """
    xs = [x0,   x0+w, x0+w, x0,   x0,   x0+w, x0+w, x0  ]
    ys = [y0,   y0,   y0+l, y0+l, y0,   y0,   y0+l, y0+l]
    zs = [0,    0,    0,    0,    h,    h,    h,    h   ]

    # Triangles for floor + 4 walls (open top)
    # Floor
    fi = [0, 0];  fj = [1, 2];  fk = [2, 3]
    # South wall  (y=y0):   0,1,5,4
    si = [0, 0];  sj = [1, 5];  sk = [5, 4]
    # North wall  (y=y0+l): 3,2,6,7
    ni = [3, 3];  nj = [2, 6];  nk = [6, 7]
    # West wall   (x=x0):   0,3,7,4
    wi = [0, 0];  wj = [3, 7];  wk = [7, 4]
    # East wall   (x=x0+w): 1,2,6,5
    ei = [1, 1];  ej = [2, 6];  ek = [6, 5]

    all_i = fi + si + ni + wi + ei
    all_j = fj + sj + nj + wj + ej
    all_k = fk + sk + nk + wk + ek

    wc = wall_color(color, darken=0.80)

    mesh = go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=all_i, j=all_j, k=all_k,
        color=color,
        opacity=opacity,
        flatshading=True,
        lighting=dict(ambient=0.7, diffuse=0.6, specular=0.1),
        hoverinfo="skip",
    )
    return [mesh]


def _label(text: str, x: float, y: float, z: float, fontsize: int = 9) -> go.Scatter3d:
    """Return a Scatter3d text annotation at (x, y, z)."""
    return go.Scatter3d(
        x=[x], y=[y], z=[z],
        mode="text",
        text=[text],
        textfont=dict(size=fontsize, color="#1A1A1A",
                      family="Arial, sans-serif"),
        hoverinfo="skip",
    )


def _plot_boundary(W: float, L: float, H: float) -> go.Scatter3d:
    """Draw the outer plot boundary as a wireframe rectangle at z=0."""
    xs = [0, W, W, 0, 0, W, W, 0, 0, 0, W, W, 0, 0]
    ys = [0, 0, L, L, 0, 0, L, L, 0, 0, 0, L, L, 0]
    zs = [0, 0, 0, 0, 0, 0, 0, 0, 0, H, H, H, H, 0]
    # Simplified: just bottom rectangle outline
    return go.Scatter3d(
        x=[0, W, W, 0, 0],
        y=[0, 0, L, L, 0],
        z=[0, 0, 0, 0, 0],
        mode="lines",
        line=dict(color="#1A1A1A", width=4),
        hoverinfo="skip",
    )


# ---------------------------------------------------------------------------
# Matplotlib 3D view (for PDF generation & offline rendering)
# ---------------------------------------------------------------------------

def create_matplotlib_3d_figure(rooms: list[dict],
                                plot_width: float,
                                plot_length: float,
                                features: list[dict] | None = None,
                                design_name: str = "",
                                wall_height: float = _WALL_H):
    """
    Generate a matplotlib 3D Figure representing the open-top residential model.
    Used by pdf_generator to guarantee crisp 3D visualization without kaleido.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    features = features or []
    all_items = features + rooms

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    fig.patch.set_facecolor("#F8F8F4")
    ax.set_facecolor("#F8F8F4")

    for item in all_items:
        x, y, w, l = item["x"], item["y"], item["width"], item["length"]
        is_feature = item.get("kind") == "amenity"
        h = 0.4 if is_feature else (wall_height * 0.5 if item.get("kind") == "staircase" else wall_height)
        col = item.get("color", get_room_color(item["name"]))

        # 5 faces: bottom floor + 4 walls (open top)
        faces = [
            [(x, y, 0), (x + w, y, 0), (x + w, y + l, 0), (x, y + l, 0)],           # floor
            [(x, y, 0), (x + w, y, 0), (x + w, y, h), (x, y, h)],                   # south
            [(x, y + l, 0), (x + w, y + l, 0), (x + w, y + l, h), (x, y + l, h)],   # north
            [(x, y, 0), (x, y + l, 0), (x, y + l, h), (x, y, h)],                   # west
            [(x + w, y, 0), (x + w, y + l, 0), (x + w, y + l, h), (x + w, y, h)],   # east
        ]
        poly = Poly3DCollection(
            faces,
            facecolor=col,
            alpha=0.85 if is_feature else 0.55,
            edgecolor="#2C3E50",
            linewidth=0.8
        )
        ax.add_collection3d(poly)

        # Label on top roof plane with solid white pill so front walls never obscure room names
        ax.text(
            x + w / 2, y + l / 2, h + 0.2,
            f"{item['name']}\n{w:.0f}×{l:.0f} ft",
            fontsize=7.0, ha="center", va="center", color="#0F172A",
            fontweight="bold", zorder=10,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='#CBD5E1', pad=1.5)
        )

    # Plot boundary lines
    ax.plot([0, plot_width, plot_width, 0, 0],
            [0, 0, plot_length, plot_length, 0],
            [0, 0, 0, 0, 0],
            color="#1A1A1A", linewidth=2.5)

    ax.set_xlim(0, plot_width)
    ax.set_ylim(0, plot_length)
    ax.set_zlim(0, wall_height + 2)
    ax.set_xlabel("Width (ft)", fontsize=8, labelpad=5)
    ax.set_ylabel("Length (ft)", fontsize=8, labelpad=5)
    ax.set_zlabel("Height (ft)", fontsize=8, labelpad=5)

    title = f"Land2Home — 3D Schematic View  |  {plot_width:.0f} × {plot_length:.0f} ft"
    if design_name:
        title += f"\n{design_name}"
    ax.set_title(title, fontsize=10, fontweight="bold", pad=12)

    ax.view_init(elev=32, azim=-55)
    fig.tight_layout(pad=1.0)
    return fig


# ---------------------------------------------------------------------------
# Backward-compatible shim (for old app.py imports)
# ---------------------------------------------------------------------------

def create_basic_3d_view(rooms: list[dict],
                          plot_width: float,
                          plot_length: float,
                          wall_height: float = _WALL_H,
                          features: list[dict] | None = None) -> go.Figure:
    """Alias kept for backward compatibility."""
    return create_3d_view(rooms, plot_width, plot_length, features, wall_height=wall_height)
