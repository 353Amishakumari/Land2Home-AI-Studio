# 🏠 Land2Home AI Architecture Studio
### Intelligent Residential Concept Planning, Computer Vision Land Detection, Vastu Compliance & Construction BOQ Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://land2home-ai-studio-jtvtkxuc9xzjvxy7qevkb8.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenCV Headless](https://img.shields.io/badge/OpenCV-Headless-red.svg)](https://opencv.org/)
[![AutoCAD DXF](https://img.shields.io/badge/AutoCAD-DXF%20R2010-orange.svg)](https://ezdxf.readthedocs.io/)

> 🚀 **Live Web App:** Experience the full interactive PropTech platform live:  
> 👉 **[Launch Land2Home Live App](https://land2home-ai-studio-jtvtkxuc9xzjvxy7qevkb8.streamlit.app/)**

**Land2Home** is a commercial PropTech architectural feasibility and generative space-planning platform. It bridges the gap between raw land parcels and build-ready residential concepts by combining **OpenCV computer vision**, **computational geometry (Shapely)**, **traditional Vedic Vastu Shastra rules**, and **milestone-based construction cost estimation (BOQ)** into a single unified workflow.

---

## 🌟 Key Features

### 1. 📸 Automated Land Boundary & Sketch Detection
- Upload real site aerial photos, satellite map screenshots, or hand-drawn rough sketches (JPG/PNG).
- OpenCV computer vision pipeline with adaptive Gaussian thresholding, Canny edge detection, contour approximation, and 4-point homography perspective warp.
- **Interactive Scale Calibration Tool**: Calibrate real-world feet dimensions using either a known side length (e.g. front road width) or total deed area (sq.ft / cents).

### 2. 🏗️ Parametric Residential Floor Planner
- Supports **1BHK, 2BHK, 3BHK, and 4BHK** residential configurations on any rectangular, square, or custom polygonal plot.
- Generates 3 distinct architectural design typologies:
  - **Design A — Central Hall**: Traditional Indian family layout with segregated private zones.
  - **Design B — Corridor Plan**: Efficient circulation with central spine dividing living from private rooms.
  - **Design C — Open Living + Dining**: Modern open-concept floor plan maximizing perceived volume.
- **Strict Geometric Invariants**: Rigorous non-overlapping room validation and realistic space proportions (bathrooms capped to realistic residential dimensions with excess space allocated to utility/store areas).

### 3. ☸️ Vastu Shastra Architectural Compliance Audit
- Compass orientation calibration supporting **North**, **East**, **South**, and **West** road-facing plots.
- Evaluates 8 compass directions + Brahmasthan (*Center*) across all rooms (e.g. Kitchen in *Agneya/SE*, Master Bedroom in *Nairutya/SW*, Pooja in *Ishanya/NE*).
- Outputs a numerical compliance score (0–100), rating grade (*A+*, *A*, *B*), and room-by-room architectural remedies.

### 4. 💰 Construction Cost & Material Quantity Estimator (BOQ)
- Interactive budget forecast with 3 customizable specification tiers:
  - **Basic**: Rs. 1,600 / sq.ft (Standard red bricks, vitrified tiles, basic fittings)
  - **Standard**: Rs. 2,100 / sq.ft (High-grade cement/steel, granite counters, branded CP fittings)
  - **Premium**: Rs. 2,800 / sq.ft (Italian marble, teak frames, smart electricals)
- **8-Phase Milestone Cashflow Forecast**: Foundation, RCC Superstructure, Masonry, Plastering, Flooring, Joinery, Plumbing/Electrical, Painting.
- **Primary Material Takeoff**: Estimates Cement (50kg bags), Structural Steel (TMT Fe 500D in kg & MT), Bricks/Blocks, M-Sand (cu.ft), Coarse Aggregates (cu.ft), Tiles, and Paint.

### 5. 📐 Multi-Format Export (AutoCAD DXF + Publication PDF)
- **AutoCAD DXF Export**: Generates layered CAD files (`PLOT_BOUNDARY`, `WALLS`, `ROOM_NAMES`, `ROOM_DIMENSIONS`, `DOORS`, `WINDOWS`, `AMENITIES`) compatible with AutoCAD, FreeCAD, and LibreCAD.
- **Executive PDF Dossier**: Publication-grade 8-page feasibility report featuring side-by-side computer vision verification images, room schedule, Vastu audit table, BOQ cashflow, 2D floor plans, 3D renders, and customizable B2B white-label branding (*Prepared For* & *Prepared By*).

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/353Amishakumari/Land2Home-AI-Studio.git
cd Land2Home-AI-Studio

# 2. Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate
# Activate on Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Streamlit application
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## ☁️ Streamlit Community Cloud Deployment

To deploy on [Streamlit Community Cloud](https://share.streamlit.io/):
1. Push this repository to GitHub.
2. Link your GitHub account on Streamlit Cloud.
3. Select this repository and set the main file path to `app.py`.
4. Ensure `packages.txt` (containing `libgl1` and `libglib2.0-0`) and `requirements.txt` are at the repository root.
5. Click **Deploy**.

---

## 📁 Repository Structure

```
Land2Home/
├── app.py                             # Streamlit multi-page web application
├── requirements.txt                   # Python dependencies (headless OpenCV, Shapely, ReportLab, ezdxf)
├── packages.txt                       # Linux OS dependencies for OpenCV on Streamlit Cloud
├── README.md                          # Project documentation and guide
└── src/
    ├── measurement/                   # Plot geometry and area calculation
    │   ├── geometry.py                # Coordinate calculation for rectangular/square/polygon plots
    │   ├── area_calculation.py       # Area & perimeter calculation with setbacks
    │   └── calibration.py             # Scale calibration (pixels to feet)
    ├── land_detection/                # Computer vision boundary detection
    │   ├── preprocessing.py           # Image loading, grayscale conversion, Gaussian blur
    │   └── segmentation.py            # Contour analysis, corner detection, perspective warp
    ├── requirement_parser/            # Space program and feasibility rules
    │   └── parser.py                  # Room requirements parser and plot buildability check
    ├── house_planner/                 # Architectural floor plan layout engine
    │   ├── floorplan_generator.py     # Procedural room partitioning for Designs A, B, and C
    │   ├── constraints.py             # Shapely geometry validation and collision detection
    │   └── room_graph.py              # Adjacency graph and topological scoring
    ├── evaluation/                    # Design metrics and Vastu audit
    │   ├── metrics.py                 # 7-factor scoring (efficiency, light, privacy, circulation)
    │   └── vastu.py                   # 8-direction + Brahmasthan Vastu Shastra analyzer
    ├── cost_estimation/               # Construction budgeting & BOQ
    │   └── estimator.py               # Tiered cost calculator, milestone cashflow, material takeoff
    ├── visualization/                 # 2D & 3D rendering
    │   ├── render_2d.py               # Matplotlib architectural drawings with styled legend
    │   └── render_3d.py               # Plotly 3D WebGL isometric models with Matplotlib fallback
    ├── export/                        # CAD export tools
    │   └── dxf_exporter.py            # Layered AutoCAD DXF R2010 generator with ezdxf
    └── reporting/                     # Client PDF dossier generation
        └── pdf_generator.py           # Multi-page ReportLab commercial report with visual proof
```

---

## ⚖️ License & Disclaimer

- **License**: MIT License.
- **Disclaimer**: Conceptual drawings, Vastu ratings, and preliminary BOQ estimates produced by Land2Home are for feasibility and conceptual planning purposes. All designs and engineering specifications must be reviewed and stamped by a licensed architect and registered structural engineer prior to on-site construction.
