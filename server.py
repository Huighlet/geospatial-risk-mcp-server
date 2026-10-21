"""
Geospatial Climate Risk Assessment Server
Implements Model Context Protocol (MCP) to provide deterministic spatial analytics
and hazard risk indicators to LLM agents and external decision-support platforms.
"""

import sys
import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from models import FloodVulnerabilityInput, DroughtAssessmentInput, BoundingBox
from services.risk_engine import RiskEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GeospatialRiskMCPServer")

# Initialize FastMCP Server with domain specifications
mcp = FastMCP(
    name="Geospatial-Climate-Risk-Engine",
    instructions=(
        "You are connected to a high-precision, deterministic geospatial climate risk engine. "
        "Use these tools to calculate flood indices, evaluate agricultural drought, "
        "and retrieve bounding-box GeoJSON polygons for spatial analysis and map visualization. "
        "Always ground your qualitative recommendations in the quantitative metrics provided by these tools."
    ),
)


@mcp.tool()
def calculate_flood_vulnerability(
    latitude: float,
    longitude: float,
    elevation_meters: float,
    precipitation_mm: float,
    soil_absorption_rate: float = 0.5,
) -> Dict[str, Any]:
    """
    Computes a deterministic flood vulnerability index (0 to 100) based on elevation,
    24-hour precipitation forecast, and soil absorption.

    Args:
        latitude: Target location latitude in decimal degrees (-90 to 90).
        longitude: Target location longitude in decimal degrees (-180 to 180).
        elevation_meters: Surface altitude above sea level in meters.
        precipitation_mm: Forecasted or observed rainfall in millimeters.
        soil_absorption_rate: Soil percolation coefficient between 0.0 (impermeable) and 1.0 (highly porous).
    """
    try:
        validated_input = FloodVulnerabilityInput(
            latitude=latitude,
            longitude=longitude,
            elevation_meters=elevation_meters,
            precipitation_mm=precipitation_mm,
            soil_absorption_rate=soil_absorption_rate,
        )
        return RiskEngine.calculate_flood_index(validated_input)
    except Exception as exc:
        logger.error(f"Error executing flood vulnerability calculation: {exc}")
        return {"error": "Validation or calculation error", "details": str(exc)}


@mcp.tool()
def evaluate_drought_index(
    soil_moisture_pct: float,
    surface_temp_celsius: float,
    baseline_ndvi: float,
) -> Dict[str, Any]:
    """
    Assesses agricultural and vegetative drought severity using topsoil moisture,
    land surface temperature, and NDVI vegetation index.

    Args:
        soil_moisture_pct: Topsoil volumetric water content percentage (0 to 100).
        surface_temp_celsius: Observed land surface temperature in Celsius (-50 to 60).
        baseline_ndvi: Normalized Difference Vegetation Index value (-1.0 to 1.0).
    """
    try:
        validated_input = DroughtAssessmentInput(
            soil_moisture_pct=soil_moisture_pct,
            surface_temp_celsius=surface_temp_celsius,
            baseline_ndvi=baseline_ndvi,
        )
        return RiskEngine.calculate_drought_index(validated_input)
    except Exception as exc:
        logger.error(f"Error executing drought assessment: {exc}")
        return {"error": "Validation or calculation error", "details": str(exc)}


@mcp.tool()
def query_bounding_box_risk(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    hazard_type: str = "flood",
) -> Dict[str, Any]:
    """
    Divides a geographic bounding box into spatial hazard zones and returns
    a fully compliant GeoJSON FeatureCollection with computed risk scores for mapping.

    Args:
        min_lat: Minimum latitude (south boundary).
        min_lon: Minimum longitude (west boundary).
        max_lat: Maximum latitude (north boundary).
        max_lon: Maximum longitude (east boundary).
        hazard_type: Type of hazard to evaluate ('flood', 'drought', 'coastal_surge').
    """
    try:
        validated_bbox = BoundingBox(
            min_lat=min_lat,
            min_lon=min_lon,
            max_lat=max_lat,
            max_lon=max_lon,
        )
        geojson_collection = RiskEngine.generate_bounding_box_risk_geojson(validated_bbox, hazard_type)
        return geojson_collection.model_dump()
    except Exception as exc:
        logger.error(f"Error querying bounding box risk: {exc}")
        return {"error": "Bounding box validation error", "details": str(exc)}


@mcp.resource("system://capabilities")
def get_system_capabilities() -> str:
    """Provides platform specification and compliance documentation."""
    return (
        "SERVIR-Aligned Geospatial Risk Analytics Engine v1.0.0\n"
        "Supported Hazards: Flood, Drought, Hydrologic Inundation\n"
        "Data Standards: EPSG:4326 GeoJSON FeatureCollection\n"
        "Execution Mode: Strictly Deterministic (Zero Hallucination)"
    )


if __name__ == "__main__":
    # Runs the server using standard standard I/O transport for MCP clients
    mcp.run()
