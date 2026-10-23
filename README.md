# GeoRisk Platform: Geospatial Climate Risk MCP Server & DSS

[![CI & Docker Verification](https://github.com/Huighlet/geospatial-risk-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/Huighlet/geospatial-risk-mcp-server/actions/workflows/ci.yml)
[![FastMCP](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol-emerald.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

A production-grade Python **Model Context Protocol (MCP)** server and interactive decision-support platform providing deterministic geospatial analytics, flood vulnerability indexing, and RFC 7946 GeoJSON bounding-box hazard partitions for LLM agents, GIS analysts, and disaster response teams.

Engineered to support scientific, Earth-observation-grounded risk analytics adhering to the **Sendai Framework for Disaster Risk Reduction** and open geospatial decision-support standards.

---

## Interactive Web Map Decision Platform

![GeoRisk Platform Interactive Decision Support System](assets/dashboard_preview.png)
*Live interactive hazard simulation over Keta Lagoon (Volta Region, Ghana) showing real-time 81.3 Critical Flood Inundation and dynamic RFC 7946 GeoJSON polygon styling.*

---

## Key Architecture & Capabilities

### 1. Strict Deterministic Scientific Engine
- **Decoupled Analytics:** Quantitative hydrologic and topographic calculations run inside approved deterministic services. The LLM explains and guides, but never hallucinates mathematical risk indices.
- **Physical Grounding:** Correlates surface elevation (meters above sea level), precipitation intensity (mm), and soil percolation coefficients.

### 2. RFC 7946 GeoJSON Standard & Spatial Partitioning
- **Dynamic Bounding-Box Partitions:** Divides any target geographic area into analytical grid polygons with cell-specific elevation variance, computed risk scores, and centroid telemetry.
- **One-Click GIS Export:** Export generated hazard layers directly to `.geojson` for seamless ingestion into **QGIS**, **ArcGIS**, or **Google Earth Engine**.

### 3. Model Context Protocol (MCP) Native
- **FastMCP Protocol Integration:** Exposes standardized tool definitions, input schemas, and resource capabilities for Claude Desktop, Cursor, Antigravity, and autonomous agent loops.

### 4. Containerized & CI/CD Automated
- **GitHub Actions Pipeline:** Automated test suite execution and Docker container build verification on every commit.

---

## Registered MCP Tools

| Tool Name | Input Parameters | Output |
| :--- | :--- | :--- |
| **`calculate_flood_vulnerability`** | `latitude`, `longitude`, `elevation_meters`, `precipitation_mm`, `soil_absorption_rate` | Deterministic index (0–100), severity (`LOW` to `CRITICAL`), operational guidance |
| **`evaluate_drought_index`** | `soil_moisture_pct`, `surface_temp_celsius`, `baseline_ndvi` | Composite drought score, classification (`EXTREME_DROUGHT` to `NORMAL`) |
| **`query_bounding_box_risk`** | `min_lat`, `min_lon`, `max_lat`, `max_lon`, `hazard_type` | RFC 7946 GeoJSON FeatureCollection with analytical polygon coordinates |

---

## Project Structure

```text
geospatial-risk-mcp-server/
├── server.py              # FastMCP server entrypoint & tool declarations
├── web_app.py             # Interactive Leaflet Web Decision Support Dashboard
├── models.py              # Pydantic data schemas & geographic validation
├── services/
│   └── risk_engine.py     # Deterministic mathematical & geospatial calculation engine
├── tests/
│   └── test_server.py     # Pytest suite verifying deterministic models & schemas
├── assets/
│   └── dashboard_preview.png  # Live simulation screenshot
├── .github/
│   └── workflows/ci.yml   # GitHub Actions CI & Docker test automation
├── Dockerfile             # Multi-stage container with automated test verification
├── requirements.txt       # Dependency specifications
└── README.md
```

---

## Quickstart

### 1. Launch the Interactive Web Dashboard
```bash
# Clone the repository
git clone https://github.com/Huighlet/geospatial-risk-mcp-server.git
cd geospatial-risk-mcp-server

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# Run the live map dashboard
python web_app.py
```
Access the live map interface at **`http://localhost:8000`** in your browser.

---

### 2. Connect to an MCP Client (Claude Desktop / Cursor)
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "geospatial-risk": {
      "command": "python",
      "args": ["/path/to/geospatial-risk-mcp-server/server.py"]
    }
  }
}
```

---

### 3. Run Automated Tests
```bash
pytest tests/ -v
```

---

## License
MIT License
