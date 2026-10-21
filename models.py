"""
Data models and schemas for Geospatial Climate Risk Assessment.
Enforces strict input validation and deterministic GeoJSON output formatting.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")


class BoundingBox(BaseModel):
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)

    @field_validator("max_lat")
    @classmethod
    def validate_latitude_order(cls, v: float, values: Any) -> float:
        if "min_lat" in values.data and v < values.data["min_lat"]:
            raise ValueError("max_lat must be greater than or equal to min_lat")
        return v

    @field_validator("max_lon")
    @classmethod
    def validate_longitude_order(cls, v: float, values: Any) -> float:
        if "min_lon" in values.data and v < values.data["min_lon"]:
            raise ValueError("max_lon must be greater than or equal to min_lon")
        return v


class FloodVulnerabilityInput(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    elevation_meters: float = Field(..., description="Surface elevation in meters above sea level")
    precipitation_mm: float = Field(..., ge=0.0, description="24-hour rainfall forecast in millimeters")
    soil_absorption_rate: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Soil percolation coefficient (0.0 to 1.0)")


class DroughtAssessmentInput(BaseModel):
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Topsoil moisture content percentage")
    surface_temp_celsius: float = Field(..., ge=-50.0, le=60.0, description="Land surface temperature in Celsius")
    baseline_ndvi: float = Field(..., ge=-1.0, le=1.0, description="Normalized Difference Vegetation Index baseline")


class GeoJSONGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
    metadata: Dict[str, Any]
