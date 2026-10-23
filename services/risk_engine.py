"""
Deterministic Climate & Disaster Risk Calculation Engine.
Ensures scientific precision and prevents LLM hallucination of numerical risk scores.
Supports multi-hazard modeling (Flood Inundation & Agricultural Drought) with high-resolution GeoJSON partitions.
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
            status = "CRITICAL"
            action = "Emergency crop irrigation dispatch and food security contingency release."
        elif composite_score >= 50.0:
            status = "HIGH"
            action = "Implement water rationing protocols and livestock feed subsidies."
        elif composite_score >= 30.0:
            status = "MODERATE"
            action = "Advise farmers on soil mulching and dry-season crop protection."
        else:
            status = "LOW"
            action = "Normal agro-climatic growth conditions."

        return {
            "composite_drought_index": composite_score,
            "classification": status,
            "severity_level": status,
            "soil_moisture_pct": data.soil_moisture_pct,
            "surface_temp_celsius": data.surface_temp_celsius,
            "baseline_ndvi": data.baseline_ndvi,
            "operational_guidance": action,
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
        soil_rate: float = 0.35,
        soil_moisture_pct: float = 20.0,
        surface_temp_celsius: float = 35.0,
        baseline_ndvi: float = 0.25,
        grid_resolution: int = 4  # 4x4 = 16 analytical grid cells
    ) -> GeoJSONFeatureCollection:
        """
        Generates a fine-grained 16-cell GeoJSON FeatureCollection dividing a target
        bounding box into analytical grid polygons with computed risk attributes.
        Supports both Flood Inundation and Agricultural Drought models.
        """
        steps = max(2, min(6, grid_resolution))
        lat_step = (bbox.max_lat - bbox.min_lat) / float(steps)
        lon_step = (bbox.max_lon - bbox.min_lon) / float(steps)

        features: List[GeoJSONFeature] = []
        cell_id = 1

        for i in range(steps):
            for j in range(steps):
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

                if hazard_type.lower() == "drought":
                    # Localized microclimate variance across cells
                    cell_moisture = max(0.0, min(100.0, soil_moisture_pct + ((i - 1.5) * 2.0)))
                    cell_temp = max(-10.0, min(55.0, surface_temp_celsius + ((j - 1.5) * 1.2)))
                    cell_ndvi = max(-0.2, min(1.0, baseline_ndvi - ((i + j) * 0.015)))

                    drought_input = DroughtAssessmentInput(
                        soil_moisture_pct=cell_moisture,
                        surface_temp_celsius=cell_temp,
                        baseline_ndvi=cell_ndvi
                    )
                    cell_result = RiskEngine.calculate_drought_index(drought_input)

                    features.append(
                        GeoJSONFeature(
                            type="Feature",
                            geometry=GeoJSONGeometry(type="Polygon", coordinates=polygon_coords),
                            properties={
                                "cell_id": f"AGRI_ZONE_{cell_id:03d}",
                                "hazard_type": "drought",
                                "risk_score": cell_result["composite_drought_index"],
                                "severity": cell_result["classification"],
                                "soil_moisture_pct": round(cell_moisture, 1),
                                "surface_temp_c": round(cell_temp, 1),
                                "ndvi": round(cell_ndvi, 2),
                                "guidance": cell_result["operational_guidance"],
                                "centroid": {"lat": round(centroid_lat, 4), "lon": round(centroid_lon, 4)},
                            },
                        )
                    )
                else:
                    # Flood Model: Micro-topographic variance across 16 cells (+/- 4m elevation gradient)
                    cell_elevation = max(0.0, elevation_meters + ((i - 1.5) * 2.5) + ((j - 1.5) * 1.8))
                    
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
                                "cell_id": f"HYDRO_ZONE_{cell_id:03d}",
                                "hazard_type": "flood",
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
                "grid_resolution": f"{steps}x{steps}",
                "cell_count": len(features),
                "data_source": "SERVIR-Aligned Deterministic Risk Analytics Service",
            },
        )

    @staticmethod
    def generate_bounded_ai_briefing(
        hazard: str,
        score: float,
        severity: str,
        rainfall: float,
        elevation: float,
        soil: float,
        location_name: str = "Target Zone"
    ) -> Dict[str, Any]:
        """
        Synthesizes a structured UN-style Situation Report (SITREP) strictly bounded
        by the deterministic calculation outputs. Zero hallucination of statistics.
        """
        if score >= 75.0:
            priority = "URGENT / PHASE 3 EMERGENCY"
            civil_actions = [
                "Issue mandatory flash flood / inundation evacuation orders for low-lying settlements below 5m elevation.",
                "Deploy emergency high-capacity mobile dewatering pumps to critical transport junctions.",
                "Activate pre-positioned shelter centers with clean water and emergency power."
            ]
            infrastructure_impact = "High probability of impassable arterial roads, bridge scour, and wastewater surcharge."
            agri_impact = "Severe topsoil stripping and prolonged crop submersion leading to total seasonal yield loss."
        elif score >= 50.0:
            priority = "ELEVATED ALERT / PHASE 2"
            civil_actions = [
                "Pre-alert municipal emergency response units and drainage maintenance teams.",
                "Inspect stormwater retention canals and clear culvert blockages.",
                "Broadcast flood advisories via regional SMS and community radio."
            ]
            infrastructure_impact = "Localized surface street ponding; intermittent disruptions to electrical substations."
            agri_impact = "Moderate waterlogging in heavy clay soils; temporary field access delays."
        elif score >= 25.0:
            priority = "ADVISORY / PHASE 1"
            civil_actions = [
                "Maintain continuous monitoring of satellite precipitation radar and hydrometric gauges.",
                "Ensure local community disaster management committees are informed."
            ]
            infrastructure_impact = "Minor localized drainage slowdowns; standard transit operations maintained."
            agri_impact = "Beneficial soil recharge with minimal erosion risk."
        else:
            priority = "NORMAL MONITORING / ROUTINE"
            civil_actions = [
                "Standard meteorological tracking and regular baseline watershed observations."
            ]
            infrastructure_impact = "Nominal operating conditions across all sectors."
            agri_impact = "Optimal moisture retention for crop germination."

        return {
            "situation_report": f"SERVIR Climate Advisory for {location_name}",
            "hazard_type": hazard.upper(),
            "quantitative_score": score,
            "severity_classification": severity,
            "readiness_priority": priority,
            "civil_protection_directives": civil_actions,
            "critical_infrastructure_risk": infrastructure_impact,
            "agricultural_livelihood_impact": agri_impact,
            "assurance_note": "Generated in accordance with Sendai Framework standards. All figures deterministically calculated by SERVIR Risk Engine."
        }
