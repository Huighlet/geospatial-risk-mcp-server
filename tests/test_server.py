"""
Unit tests for deterministic risk engine and GeoJSON schema validation.
"""

import pytest
from models import FloodVulnerabilityInput, DroughtAssessmentInput, BoundingBox
from services.risk_engine import RiskEngine


def test_flood_index_deterministic_behavior():
    """Verify that identical inputs yield identical deterministic risk scores."""
    input_data = FloodVulnerabilityInput(
        latitude=13.7563,
        longitude=100.5018,
        elevation_meters=2.5,
        precipitation_mm=120.0,
        soil_absorption_rate=0.4,
    )
    result_1 = RiskEngine.calculate_flood_index(input_data)
    result_2 = RiskEngine.calculate_flood_index(input_data)

    assert result_1["flood_vulnerability_index"] == result_2["flood_vulnerability_index"]
    assert result_1["severity_level"] in ["MODERATE", "HIGH", "CRITICAL"]
    assert "deterministic_factors" in result_1


def test_drought_index_severity_scaling():
    """Verify that severe moisture deficit triggers elevated drought classifications."""
    severe_drought = DroughtAssessmentInput(
        soil_moisture_pct=10.0,
        surface_temp_celsius=42.0,
        baseline_ndvi=0.15,
    )
    result = RiskEngine.calculate_drought_index(severe_drought)
    assert result["composite_drought_index"] >= 60.0
    assert result["classification"] in ["SEVERE_DROUGHT", "EXTREME_DROUGHT"]


def test_geojson_bounding_box_generation():
    """Verify that generated GeoJSON complies with RFC 7946 specifications."""
    bbox = BoundingBox(
        min_lat=10.0,
        min_lon=98.0,
        max_lat=15.0,
        max_lon=103.0,
    )
    geojson_result = RiskEngine.generate_bounding_box_risk_geojson(bbox, "flood")
    dumped = geojson_result.model_dump()

    assert dumped["type"] == "FeatureCollection"
    assert len(dumped["features"]) == 4
    for feature in dumped["features"]:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        assert "risk_score" in feature["properties"]
        assert "severity" in feature["properties"]


def test_invalid_coordinates_validation():
    """Verify that Pydantic enforces valid geographic constraints."""
    with pytest.raises(ValueError):
        BoundingBox(min_lat=50.0, min_lon=10.0, max_lat=40.0, max_lon=10.0)  # max_lat < min_lat
