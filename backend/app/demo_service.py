"""Orquestación del escenario geográfico y meteorológico simulado."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ultima_ventana_ml import calculate_last_safe_departure, risk_level

from .model_service import DISCLAIMER, ModelService
from .schemas import DemoAnalysisRequest

RAIN_TRIGGER_THRESHOLD_MM = 20.0
FORECAST_PRESETS = {
    "dry": {"label": "Seco", "rain_24h_mm": 12, "rain_72h_mm": 29, "forecast_rain_6h_mm": 8, "forecast_rain_12h_mm": 16},
    "moderate": {"label": "Moderado", "rain_24h_mm": 45, "rain_72h_mm": 105, "forecast_rain_6h_mm": 28, "forecast_rain_12h_mm": 52},
    "storm": {"label": "Tormenta", "rain_24h_mm": 122, "rain_72h_mm": 245, "forecast_rain_6h_mm": 68, "forecast_rain_12h_mm": 110},
}
DEFAULT_LOCATION = {"latitude": -27.4692, "longitude": -58.8306}


def _load_route_templates() -> list[dict[str, Any]]:
    path = Path(__file__).with_name("data") / "demo_routes.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _offset_coordinate(latitude: float, longitude: float, east_m: float, north_m: float) -> list[float]:
    latitude_delta = north_m / 111_320.0
    longitude_scale = max(111_320.0 * math.cos(math.radians(latitude)), 1.0)
    longitude_delta = east_m / longitude_scale
    return [longitude + longitude_delta, latitude + latitude_delta]


def _geometry(route: dict[str, Any], latitude: float, longitude: float) -> dict[str, Any]:
    coordinates = [_offset_coordinate(latitude, longitude, east, north) for east, north in route["points_m"]]
    return {"type": "LineString", "coordinates": coordinates}


def _snapshot(forecast: dict[str, float], segment: dict[str, Any], progress: float) -> dict[str, float]:
    future_rain = forecast["forecast_rain_12h_mm"] * progress
    rain_24h = min(forecast["rain_24h_mm"] + 0.55 * future_rain, 200.0)
    rain_72h = min(forecast["rain_72h_mm"] + 0.80 * future_rain, 400.0)
    forecast_6h = min(forecast["forecast_rain_6h_mm"] * (0.75 + 0.25 * progress), 150.0)
    forecast_12h = min(forecast["forecast_rain_12h_mm"] * (0.85 + 0.15 * progress), 250.0)
    water_increase = 0.25 * (forecast["forecast_rain_12h_mm"] / 250.0) * progress
    return {
        "rain_24h_mm": rain_24h,
        "rain_72h_mm": max(rain_24h, rain_72h),
        "forecast_rain_6h_mm": forecast_6h,
        "forecast_rain_12h_mm": max(forecast_6h, forecast_12h),
        "elevation_mean_m": segment["elevation_mean_m"],
        "slope_mean_pct": segment["slope_mean_pct"],
        "water_coverage_100m_ratio": min(segment["water_coverage_100m_ratio"] + water_increase, 1.0),
    }


def analyze_demo(model: ModelService, request: DemoAnalysisRequest) -> dict[str, Any]:
    forecast = request.forecast.model_dump()
    start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    route_results: list[dict[str, Any]] = []
    alerts: list[dict[str, str]] = []

    for route in _load_route_templates():
        records = []
        for hour in range(1, 13):
            prediction_time = start_time + timedelta(hours=hour)
            for segment in route["segments"]:
                records.append({
                    "segment_id": segment["segment_id"], "segment_name": segment["name"],
                    "prediction_time": prediction_time,
                    **_snapshot(forecast, segment, hour / 12.0),
                })
        scored = model.predictor.predict_many(pd.DataFrame(records))
        route_timeline = []
        for prediction_time, group in scored.groupby("prediction_time", sort=True):
            worst = group.loc[group["risk_score"].idxmax()]
            route_timeline.append({
                "prediction_time": prediction_time,
                "risk_score": float(worst["risk_score"]),
                "risk_level": worst["risk_level"],
                "critical_segment_id": worst["segment_id"],
            })
        first_critical = next((point for point in route_timeline if point["risk_score"] >= 0.70), None)
        peak = max(route_timeline, key=lambda point: point["risk_score"])
        segments = []
        for segment_id, group in scored.groupby("segment_id", sort=False):
            segment_peak = group.loc[group["risk_score"].idxmax()]
            critical_rows = group.loc[group["risk_score"] >= 0.70].sort_values("prediction_time")
            segments.append({
                "segment_id": segment_id,
                "name": segment_peak["segment_name"],
                "peak_risk_score": float(segment_peak["risk_score"]),
                "risk_level": segment_peak["risk_level"],
                "critical_time": None if critical_rows.empty else critical_rows.iloc[0]["prediction_time"],
            })
        critical_time = None if first_critical is None else first_critical["prediction_time"]
        last_departure = None if critical_time is None else calculate_last_safe_departure(
            critical_time, route["travel_time_minutes"], request.safety_margin_minutes,
        )
        route_result = {
            "route_id": route["route_id"], "name": route["name"],
            "travel_time_minutes": route["travel_time_minutes"],
            "geometry": _geometry(route, request.location.latitude, request.location.longitude),
            "peak_risk_score": float(peak["risk_score"]), "risk_level": risk_level(float(peak["risk_score"])),
            "critical_time": critical_time,
            "critical_segment_id": None if first_critical is None else first_critical["critical_segment_id"],
            "last_safe_departure": last_departure, "segments": segments,
            "timeline": [{key: point[key] for key in ("prediction_time", "risk_score", "risk_level")} for point in route_timeline],
        }
        route_results.append(route_result)
        if critical_time is not None:
            alerts.append({
                "severity": "CRITICAL", "route_id": route["route_id"],
                "title": f"{route['name']} podría alcanzar riesgo crítico",
                "message": f"Tramo {route_result['critical_segment_id']} · hora crítica estimada {critical_time:%H:%M} UTC.",
            })

    return {
        "mode": "SYNTHETIC_DEMO", "generated_at": datetime.now(timezone.utc),
        "trigger_threshold_mm": RAIN_TRIGGER_THRESHOLD_MM,
        "triggered": forecast["forecast_rain_12h_mm"] >= RAIN_TRIGGER_THRESHOLD_MM,
        "location": request.location.model_dump(), "forecast": forecast,
        "routes": route_results, "alerts": alerts, "disclaimer": DISCLAIMER,
    }
