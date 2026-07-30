# Enterprise Municipal AutoDCR Engine

Production-ready Municipal Building Plan Approval AutoDCR Engine built with Python and FastAPI, comparable to Telangana AutoDCR, Andhra Pradesh AutoDCR, Maharashtra AutoDCR, and GDCR systems.

---

## 🏗 System Architecture

```
                                    +-----------------------------------+
                                    |        FastAPI REST API Layer      |
                                    |    (/api/autodcr/* Endpoints)    |
                                    +-----------------+-----------------+
                                                      |
                    +---------------------------------+---------------------------------+
                    |                                 |                                 |
                    v                                 v                                 v
        +-----------------------+         +-----------------------+         +-----------------------+
        |   Multi-Format Parser |         |  Automatic Detection  |         |   Area/Height/Parking |
        |  (DXF / DWG / IFC/PDF)|         |         Engine        |         |        Engines        |
        +-----------+-----------+         +-----------+-----------+         +-----------+-----------+
                    |                                 |                                 |
                    +---------------------------------+---------------------------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        |  Configurable Rule Engine |
                                        |  (JSON/YAML Building DCRs)|
                                        +-------------+-------------+
                                                      |
                                                      v
                                        +---------------------------+
                                        | Compliance & Report Engine|
                                        | (JSON/PDF/HTML/SVG Overlays|
                                        +---------------------------+
```

---

## ⚡ Key Features

1. **Multi-Format Parsing**: Production CAD/BIM parsers for DXF, DWG (via ODA), IFC, and vector PDF drawings normalized into a single common schema.
2. **Automatic Detection Engine**: Automatic layer and spatial relationship-based detection of:
   - Plot Boundary, Building Footprint, Compound Wall, Road, Footpath, Driveways, Corner Plots.
   - Parking Slots (Car, Bike, Accessible Handicapped Slots).
   - Circulation (Lifts, Lift Shafts, Fire Escape Staircases, Normal Staircases, Vehicle & Pedestrian Ramps).
   - Floor Projections (Balconies, Basements, Terraces, Open Spaces, Landscape Areas).
   - Amenities (Rooftop Solar PV Arrays, Rain Water Harvesting Pits, Water Tanks, STP, Generator & Utility Rooms).
3. **Production Calculation Engines**:
   - **Area Engine**: Plot Area, Building Area, Built-up Area, Floor-wise Area, Ground Coverage %, Parking Area, Open Area, Landscape Area, Basement Area, Terrace Area, Carpet Area, Super Built-up Area, FSI Area, FAR.
   - **Height Engine**: Building Height, Floor Height, Plinth, Parapet, Terrace Height, Basement Depth, Floor Count.
   - **Parking Engine**: Required vs Available Parking for Car/Bike/Accessible slots, Slot Dimensions, Parking Violations.
4. **Configurable Rule Engine**: Non-hardcoded JSON rule configurations for Residential, Commercial, Industrial, Mixed Use, and High Rise zones with min/max, formula, conditions, and priority support.
5. **Municipal Compliance Engine**: Calculates overall PASS/FAIL/WARNING/INFO status, Compliance Score %, Pass/Fail count, Risk Level (Low/Medium/High), and actionable recommendations.
6. **Multi-Format Reporting & Visualization**: Generates PDF, HTML, JSON, and Excel compliance reports along with color-coded SVG/PNG drawing overlays (Green = PASS, Red = FAIL).
7. **Enterprise Security & Performance**: Upload validation (MIME, size, path traversal protection), rate limiting, audit logging, Docker containerization, and automated GitHub Actions CI pipeline.

---

## 🚀 Quick Start & Deployment Guide

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-org/autodcr-engine.git
cd autodcr-engine

# 2. Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run server
uvicorn app.main:app --reload --port 8000
```

### Docker Deployment

```bash
docker-compose up -d --build
```

---

## 🧪 Running Test Suite

```bash
python -m pytest tests/ -v --cov=app
```

---

## 📖 API Documentation

Access interactive OpenAPI documentation at: `http://localhost:8000/docs`

Key endpoints:
- `POST /api/autodcr/upload`: Upload CAD/BIM drawing file
- `POST /api/autodcr/parse`: Parse entities into common schema
- `POST /api/autodcr/detect`: Run automatic spatial feature detection
- `POST /api/autodcr/calculate`: Calculate Area, Height, and Parking metrics
- `POST /api/autodcr/validate`: Evaluate rules against building code standards
- `POST /api/autodcr/report`: Generate compliance report (JSON, PDF, HTML, Excel)
- `GET /api/autodcr/rules`: Retrieve active configurable rule set
