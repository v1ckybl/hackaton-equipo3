"""Contrato de features, target y niveles de riesgo del modelo v1."""

from __future__ import annotations

from typing import Any

FEATURE_COLUMNS_V1 = (
    "rain_24h_mm",
    "rain_72h_mm",
    "forecast_rain_6h_mm",
    "forecast_rain_12h_mm",
    "elevation_mean_m",
    "slope_mean_pct",
    "water_coverage_100m_ratio",
)
TARGET_NAME = "intransitable_within_6h"
TARGET_HORIZON_HOURS = 6
FEATURE_SCHEMA_VERSION = "v1"
SYNTHETIC_GENERATOR_VERSION = "synthetic-v1"
LABEL_RULE_VERSION = "synthetic-v1"
MODEL_VERSION = "synthetic-v1"
CRITICAL_RISK_THRESHOLD = 0.70

FEATURE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"name": "rain_24h_mm", "type": "float64", "unit": "mm", "min": 0.0, "max": 200.0},
    {"name": "rain_72h_mm", "type": "float64", "unit": "mm", "min": 0.0, "max": 400.0},
    {"name": "forecast_rain_6h_mm", "type": "float64", "unit": "mm", "min": 0.0, "max": 150.0},
    {"name": "forecast_rain_12h_mm", "type": "float64", "unit": "mm", "min": 0.0, "max": 250.0},
    {"name": "elevation_mean_m", "type": "float64", "unit": "m", "min": 20.0, "max": 120.0},
    {"name": "slope_mean_pct", "type": "float64", "unit": "percent", "min": 0.0, "max": 10.0},
    {"name": "water_coverage_100m_ratio", "type": "float64", "unit": "ratio", "min": 0.0, "max": 1.0},
)


def risk_level(score: float) -> str:
    """Convert a probability into the four MVP risk bands."""
    value = float(score)
    if not 0.0 <= value <= 1.0:
        raise ValueError("risk score must be between 0 and 1")
    if value < 0.30:
        return "LOW"
    if value < 0.50:
        return "MODERATE"
    if value < CRITICAL_RISK_THRESHOLD:
        return "HIGH"
    return "CRITICAL"
