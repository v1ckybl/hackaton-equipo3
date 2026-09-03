"""Escenario temporal sintético y lógica demostrativa de Última Ventana."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from .contract import CRITICAL_RISK_THRESHOLD


def generate_demo_timeline(start_time: datetime | None = None, hours: int = 12, step_hours: int = 1) -> pd.DataFrame:
    if hours < 1 or step_hours < 1:
        raise ValueError("hours and step_hours must be positive")
    start = start_time or datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    steps = np.arange(step_hours, hours + 1, step_hours, dtype=float)
    progress = steps / float(hours)
    return pd.DataFrame({
        "segment_id": 152,
        "prediction_time": [start + timedelta(hours=float(step)) for step in steps],
        "rain_24h_mm": 12.0 + 110.0 * progress,
        "rain_72h_mm": 29.0 + 216.0 * progress,
        "forecast_rain_6h_mm": 8.0 + 60.0 * progress,
        "forecast_rain_12h_mm": 16.0 + 94.0 * progress,
        "elevation_mean_m": 48.0,
        "slope_mean_pct": 0.3,
        "water_coverage_100m_ratio": 0.04 + 0.38 * progress,
    })


def find_critical_time(predictions: pd.DataFrame, threshold: float = CRITICAL_RISK_THRESHOLD) -> datetime | None:
    required = {"prediction_time", "risk_score"}
    if not required.issubset(predictions.columns):
        raise ValueError("predictions require prediction_time and risk_score")
    critical = predictions.loc[predictions["risk_score"] >= threshold].sort_values("prediction_time")
    return None if critical.empty else critical.iloc[0]["prediction_time"]


def calculate_last_safe_departure(critical_time: datetime, travel_time_minutes: int, safety_margin_minutes: int) -> datetime:
    if travel_time_minutes < 0 or safety_margin_minutes < 0:
        raise ValueError("travel time and safety margin cannot be negative")
    return critical_time - timedelta(minutes=travel_time_minutes + safety_margin_minutes)
