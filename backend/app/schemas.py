"""Contratos HTTP de la demo."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeatureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rain_24h_mm: float = Field(ge=0, le=200)
    rain_72h_mm: float = Field(ge=0, le=400)
    forecast_rain_6h_mm: float = Field(ge=0, le=150)
    forecast_rain_12h_mm: float = Field(ge=0, le=250)
    elevation_mean_m: float = Field(ge=20, le=120)
    slope_mean_pct: float = Field(ge=0, le=10)
    water_coverage_100m_ratio: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_accumulations(self) -> "FeatureInput":
        if self.rain_72h_mm < self.rain_24h_mm:
            raise ValueError("rain_72h_mm must be greater than or equal to rain_24h_mm")
        if self.forecast_rain_12h_mm < self.forecast_rain_6h_mm:
            raise ValueError("forecast_rain_12h_mm must be greater than or equal to forecast_rain_6h_mm")
        return self


class ForecastInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rain_24h_mm: float = Field(ge=0, le=200)
    rain_72h_mm: float = Field(ge=0, le=400)
    forecast_rain_6h_mm: float = Field(ge=0, le=150)
    forecast_rain_12h_mm: float = Field(ge=0, le=250)

    @model_validator(mode="after")
    def validate_accumulations(self) -> "ForecastInput":
        if self.rain_72h_mm < self.rain_24h_mm:
            raise ValueError("La lluvia de 72 h debe ser mayor o igual a la de 24 h")
        if self.forecast_rain_12h_mm < self.forecast_rain_6h_mm:
            raise ValueError("El pronóstico de 12 h debe ser mayor o igual al de 6 h")
        return self


class LocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class DemoAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: LocationInput
    forecast: ForecastInput
    safety_margin_minutes: int = Field(default=40, ge=0, le=180)


class PredictionResponse(BaseModel):
    risk_score: float
    risk_level: str
    model_version: str
    disclaimer: str


class TimelinePoint(BaseModel):
    prediction_time: datetime
    risk_score: float
    risk_level: str


class SegmentRisk(BaseModel):
    segment_id: str
    name: str
    peak_risk_score: float
    risk_level: str
    critical_time: datetime | None


class RouteRisk(BaseModel):
    route_id: str
    name: str
    travel_time_minutes: int
    geometry: dict[str, Any]
    peak_risk_score: float
    risk_level: str
    critical_time: datetime | None
    critical_segment_id: str | None
    last_safe_departure: datetime | None
    segments: list[SegmentRisk]
    timeline: list[TimelinePoint]


class Alert(BaseModel):
    severity: str
    route_id: str
    title: str
    message: str


class DemoAnalysisResponse(BaseModel):
    mode: str
    generated_at: datetime
    trigger_threshold_mm: float
    triggered: bool
    location: LocationInput
    forecast: ForecastInput
    routes: list[RouteRisk]
    alerts: list[Alert]
    disclaimer: str
