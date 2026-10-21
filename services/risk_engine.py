"""
Deterministic Climate & Disaster Risk Calculation Engine.
Ensures scientific precision and prevents LLM hallucination of numerical risk scores.
"""

import math
from typing import Dict, Any, List
from models import (
    FloodVulnerabilityInput,
    DroughtAssessmentInput,
    BoundingBox,
    GeoJSONFeatureCollection,
    GeoJSONFeature,
    GeoJSONGeometry,
)


class RiskEngine:
    """Core calculation engine for geospatial risk analytics."""

    @staticmethod
    def calculate_flood_index(data: FloodVulnerabilityInput) -> Dict[str, Any]:
        """
        Calculates a deterministic flood vulnerability index (0.0 to 100.0)
        based on topographic elevation, anticipated precipitation, and soil percolation.
        """
        # Topographic vulnerability decreases logarithmically with elevation
        if data.elevation_meters <= 0:
            elevation_factor = 1.0
        elif data.elevation_meters < 50:
            elevation_factor = max(0.1, 1.0 - (data.elevation_meters / 50.0))
        else:
            elevation_factor = max(0.02, 1.0 / (1.0 + math.log10(data.elevation_meters / 10.0)))

        # Precipitation intensity factor (capped at 250mm standard extreme benchmark)
        precip_factor = min(1.0, data.precipitation_mm / 250.0)

        # Runoff coefficient inverse of soil absorption
        runoff_factor = 1.0 - (data.soil_absorption_rate or 0.5)

        # Composite Flood Risk Score: 0 - 100
        raw_score = (elevation_factor * 0.45 + precip_factor * 0.40 + runoff_factor * 0.15) * 100.0
        risk_score = round(min(100.0, max(0.0, raw_score)), 2)

        if risk_score >= 75.0:
            severity = "CRITICAL"
            recommended_action = "Immediate evacuation readiness and deployment of flood barriers."
        elif risk_score >= 50.0:
            severity = "HIGH"
            recommended_action = "Activate municipal drainage systems and issue public hazard alerts."
        elif risk_score >= 25.0:
            severity = "MODERATE"
            recommended_action = "Monitor localized hydrologic telemetry and river gauging stations."
        else:
            severity = "LOW"
            recommended_action = "Routine hydrometric observation."

        return {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "elevation_meters": data.elevation_meters,
            "precipitation_mm": data.precipitation_mm,
            "flood_vulnerability_index": risk_score,
            "severity_level": severity,
            "deterministic_factors": {
                "topographic_factor": round(elevation_factor, 3),
                "precipitation_factor": round(precip_factor, 3),
                "runoff_coefficient": round(runoff_factor, 3),
            },
            "operational_guidance": recommended_action,
        }

    @staticmethod
    def calculate_drought_index(data: DroughtAssessmentInput) -> Dict[str, Any]:
        """
        Evaluates agricultural and hydrologic drought severity based on topsoil moisture,
        land surface temperature, and NDVI vegetation health.
        """
        # Low soil moisture increases drought severity
        moisture_deficit = max(0.0, (100.0 - data.soil_moisture_pct) / 100.0)

        # Thermal stress factor (30C standard baseline threshold)
        if data.surface_temp_celsius > 30.0:
            thermal_stress = min(1.0, (data.surface_temp_celsius - 30.0) / 20.0)
        else:
            thermal_stress = 0.0

        # Vegetation anomaly (NDVI below 0.3 indicates severe vegetation stress)
        vegetation_stress = max(0.0, min(1.0, (0.5 - data.baseline_ndvi) / 0.5))

        composite_score = round((moisture_deficit * 0.50 + thermal_stress * 0.30 + vegetation_stress * 0.20) * 100.0, 2)

        if composite_score >= 70.0:
            status = "EXTREME_DROUGHT"
        elif composite_score >= 50.0:
            status = "SEVERE_DROUGHT"
        elif composite_score >= 30.0:
            status = "MODERATE_DROUGHT"
        else:
            status = "NORMAL_CONDITIONS"

        return {
            "composite_drought_index": composite_score,
            "classification": status,
            "soil_moisture_pct": data.soil_moisture_pct,
            "surface_temp_celsius": data.surface_temp_celsius,
            "baseline_ndvi": data.baseline_ndvi,
            "stress_breakdown": {
                "moisture_deficit_weight": round(moisture_deficit, 3),
                "thermal_stress_weight": round(thermal_stress, 3),
                "vegetation_stress_weight": round(vegetation_stress, 3),
            },
        }

    @staticmethod
    def generate_bounding_box_risk_geojson(
        bbox: BoundingBox, 
        hazard_type: str = "flood",
        precipitation_mm: float = 135.0,
        elevation_meters: float = 2.5,
        soil_rate: float = 0.35
    ) -> GeoJSONFeatureCollection:
        """
        Generates a valid GeoJSON FeatureCollection dividing a target geographic
        bounding box into analytical grid polygons with computed risk attributes
        directly driven by the simulation slider values.
        """
        lat_step = (bbox.max_lat - bbox.min_lat) / 2.0
        lon_step = (bbox.max_lon - bbox.min_lon) / 2.0

        features: List[GeoJSONFeature] = []
        cell_id = 1

        for i in range(2):
            for j in range(2):
                c_min_lat = bbox.min_lat + i * lat_step
                c_max_lat = c_min_lat + lat_step
                c_min_lon = bbox.min_lon + j * lon_step
                c_max_lon = c_min_lon + lon_step

                polygon_coords = [
                    [
                        [round(c_min_lon, 5), round(c_min_lat, 5)],
                        [round(c_max_lon, 5), round(c_min_lat, 5)],
                        [round(c_max_lon, 5), round(c_max_lat, 5)],
                        [round(c_min_lon, 5), round(c_max_lat, 5)],
                        [round(c_min_lon, 5), round(c_min_lat, 5)],
                    ]
                ]

                centroid_lat = (c_min_lat + c_max_lat) / 2.0
                centroid_lon = (c_min_lon + c_max_lon) / 2.0

                # Slight localized topographic variance across grid cells (+/- 3m)
                cell_elevation = max(0.0, elevation_meters + ((i - 0.5) * 2.5) + ((j - 0.5) * 1.5))
                
                # Calculate deterministic flood index for this specific cell
                cell_input = FloodVulnerabilityInput(
                    latitude=centroid_lat,
                    longitude=centroid_lon,
                    elevation_meters=cell_elevation,
                    precipitation_mm=precipitation_mm,
                    soil_absorption_rate=soil_rate
                )
                cell_result = RiskEngine.calculate_flood_index(cell_input)

                features.append(
                    GeoJSONFeature(
                        type="Feature",
                        geometry=GeoJSONGeometry(type="Polygon", coordinates=polygon_coords),
                        properties={
                            "cell_id": f"ZONE_{cell_id:03d}",
                            "hazard_type": hazard_type.lower(),
                            "risk_score": cell_result["flood_vulnerability_index"],
                            "severity": cell_result["severity_level"],
                            "elevation_m": round(cell_elevation, 1),
                            "precipitation_mm": precipitation_mm,
                            "guidance": cell_result["operational_guidance"],
                            "centroid": {"lat": round(centroid_lat, 4), "lon": round(centroid_lon, 4)},
                        },
                    )
                )
                cell_id += 1

        return GeoJSONFeatureCollection(
            type="FeatureCollection",
            features=features,
            metadata={
                "crs": "EPSG:4326",
                "hazard_evaluated": hazard_type,
                "cell_count": len(features),
                "data_source": "SERVIR-Aligned Deterministic Risk Analytics Service",
            },
        )
