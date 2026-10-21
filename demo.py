"""
Interactive demonstration script for Geospatial Climate Risk Engine.
Run this script to see the deterministic calculations and GeoJSON outputs in action.
"""

import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from services.risk_engine import RiskEngine
from models import FloodVulnerabilityInput, DroughtAssessmentInput, BoundingBox


def run_demo():
    print("=" * 70)
    print("[*] GEOSPATIAL CLIMATE RISK ENGINE -- DEMONSTRATION")
    print("=" * 70)

    # 1. Flood Vulnerability Test
    print("\n[1] CALCULATING DETERMINISTIC FLOOD RISK (e.g., Bangkok Lowland Area)")
    flood_input = FloodVulnerabilityInput(
        latitude=13.7563,
        longitude=100.5018,
        elevation_meters=2.5,        # Low coastal elevation
        precipitation_mm=135.0,      # Heavy tropical storm rainfall
        soil_absorption_rate=0.35,   # Urban clay / low absorption
    )
    flood_result = RiskEngine.calculate_flood_index(flood_input)
    print(f"  * Target: Lat {flood_input.latitude}, Lon {flood_input.longitude}")
    print(f"  * Elevation: {flood_input.elevation_meters}m | 24h Rain: {flood_input.precipitation_mm}mm")
    print(f"  * Computed Flood Vulnerability Index: {flood_result['flood_vulnerability_index']} / 100")
    print(f"  * Severity Classification: {flood_result['severity_level']}")
    print(f"  * Operational Action: {flood_result['operational_guidance']}")

    # 2. Agricultural Drought Test
    print("\n[2] ASSESSING AGRICULTURAL DROUGHT SEVERITY")
    drought_input = DroughtAssessmentInput(
        soil_moisture_pct=14.0,       # Very dry topsoil
        surface_temp_celsius=39.5,    # High surface heat
        baseline_ndvi=0.22,           # Stressed vegetation
    )
    drought_result = RiskEngine.calculate_drought_index(drought_input)
    print(f"  * Soil Moisture: {drought_input.soil_moisture_pct}% | Surface Temp: {drought_input.surface_temp_celsius}C")
    print(f"  * Vegetation Index (NDVI): {drought_input.baseline_ndvi}")
    print(f"  * Composite Drought Score: {drought_result['composite_drought_index']} / 100")
    print(f"  * Classification: {drought_result['classification']}")

    # 3. GeoJSON Spatial Risk Map Layer
    print("\n[3] GENERATING RFC 7946 GeoJSON MAP POLYGONS (Bounding Box Partition)")
    bbox = BoundingBox(
        min_lat=13.0,
        min_lon=100.0,
        max_lat=14.5,
        max_lon=101.5,
    )
    geojson_result = RiskEngine.generate_bounding_box_risk_geojson(bbox, hazard_type="flood")
    geojson_dict = geojson_result.model_dump()
    print(f"  * Generated FeatureCollection with {len(geojson_dict['features'])} analytical grid zones")
    print(f"  * Sample Zone 1 Properties: {geojson_dict['features'][0]['properties']}")
    print(f"  * Sample Polygon Coordinates: {geojson_dict['features'][0]['geometry']['coordinates'][0][:3]}...")

    print("\n" + "=" * 70)
    print("[SUCCESS] All calculations completed deterministically with ZERO LLM hallucination.")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
