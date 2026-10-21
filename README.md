# Geospatial Climate Risk MCP Server

A production-grade Python **Model Context Protocol (MCP)** server providing deterministic geospatial analytics, flood vulnerability indexing, and GeoJSON bounding-box hazard partitions for LLM agents and decision-support systems.

Engineered to support scientific, Earth-observation-grounded risk analytics adhering to the **Sendai Framework for Disaster Risk Reduction** and **SERVIR Global Risk Platform (GRP)** design standards.

---

##  Key Features

- **Strict Deterministic Analytics:** Decouples quantitative calculations from language models. The LLM explains and summarizes, but never hallucinates mathematical risk indices.
- **RFC 7946 GeoJSON Standard:** Outputs valid `FeatureCollection` geometries with analytical polygon coordinates, hazard classifications, and centroid telemetry.
- **Model Context Protocol (MCP) Native:** Built using FastMCP with standard input schemas, tool descriptions, and resource capabilities.
- **Containerized & CI/CD Ready:** Fully dockerized with automated test execution during image build.

---

##  MCP Tool Definitions

### 1. `calculate_flood_vulnerability`
Calculates a composite flood vulnerability index (0 to 100) based on elevation, precipitation, and soil percolation.
* **Input Parameters:**
  * `latitude` (*float*): Target latitude (-90 to 90).
  * `longitude` (*float*): Target longitude (-180 to 180).
  * `elevation_meters` (*float*): Surface altitude above sea level.
  * `precipitation_mm` (*float*): 24-hour rainfall forecast.
  * `soil_absorption_rate` (*float*, optional): Soil infiltration coefficient (0.0 to 1.0).
* **Output:** Deterministic risk score, severity level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`), and operational guidance.

### 2. `evaluate_drought_index`
Computes agricultural drought severity by correlating soil moisture deficit, land surface temperature anomalies, and NDVI vegetation health.
* **Input Parameters:**
  * `soil_moisture_pct` (*float*): Topsoil moisture percentage (0 to 100).
  * `surface_temp_celsius` (*float*): Land surface temperature (-50 to 60°C).
  * `baseline_ndvi` (*float*): Normalized Difference Vegetation Index (-1.0 to 1.0).
* **Output:** Composite drought classification (`NORMAL`, `MODERATE_DROUGHT`, `SEVERE_DROUGHT`, `EXTREME_DROUGHT`).

### 3. `query_bounding_box_risk`
Partitions a target geographic bounding box into spatial cells and generates a compliant GeoJSON `FeatureCollection` with risk scores for web map visualization (Leaflet, MapLibre, OpenLayers).
* **Input Parameters:** `min_lat`, `min_lon`, `max_lat`, `max_lon`, `hazard_type`.
* **Output:** GeoJSON FeatureCollection with polygon coordinates and zone metadata.

---

##  Project Architecture

```text
geospatial-risk-mcp-server/
├── server.py              # FastMCP server entrypoint & tool declarations
├── models.py              # Pydantic data schemas & geographic validation
├── services/
│   └── risk_engine.py     # Deterministic mathematical & geospatial engine
├── tests/
│   └── test_server.py     # Unit tests verifying deterministic behavior & schemas
├── Dockerfile             # Multi-stage production container
├── requirements.txt       # Dependency specifications
└── README.md
```

---

##  Client Integration

### 1. Claude Desktop / Cursor MCP Configuration
Add this server to your `claude_desktop_config.json` or cursor MCP settings:

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

### 2. Docker Execution
```bash
# Build the container
docker build -t geospatial-risk-mcp .

# Run via standard I/O
docker run -i --rm geospatial-risk-mcp
```

---

##  Automated Testing

Run the test suite to verify schema validation and deterministic calculations:

```bash
pytest tests/ -v
```

---

##  License
MIT License
