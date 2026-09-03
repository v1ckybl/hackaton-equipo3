"""Carga segura e inferencia nominal para el modelo v1."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from .contract import FEATURE_COLUMNS_V1, FEATURE_DEFINITIONS, FEATURE_SCHEMA_VERSION, risk_level


class PredictionInputError(ValueError):
    """Raised when an inference input violates the feature contract."""


class RiskPredictor:
    def __init__(self, model: XGBClassifier, schema: dict[str, Any]) -> None:
        self._model = model
        self._schema = schema

    @classmethod
    def load(cls, model_path: Path | str, schema_path: Path | str) -> "RiskPredictor":
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        names = tuple(item["name"] for item in schema.get("features", []))
        if schema.get("version") != FEATURE_SCHEMA_VERSION or names != FEATURE_COLUMNS_V1:
            raise PredictionInputError("model schema is not compatible with feature contract v1")
        model = XGBClassifier()
        model.load_model(str(model_path))
        return cls(model, schema)

    @staticmethod
    def _validate_feature_frame(frame: pd.DataFrame) -> np.ndarray:
        missing = [name for name in FEATURE_COLUMNS_V1 if name not in frame.columns]
        if missing:
            raise PredictionInputError(f"missing features: {', '.join(missing)}")
        try:
            values = frame.loc[:, list(FEATURE_COLUMNS_V1)].apply(pd.to_numeric, errors="raise").to_numpy(dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise PredictionInputError("all features must be numeric") from error
        if not np.isfinite(values).all():
            raise PredictionInputError("all features must be finite")
        for position, definition in enumerate(FEATURE_DEFINITIONS):
            column = values[:, position]
            if np.any(column < definition["min"]) or np.any(column > definition["max"]):
                raise PredictionInputError(f"{definition['name']} is outside the v1 range")
        if np.any(values[:, 1] < values[:, 0]):
            raise PredictionInputError("rain_72h_mm must be greater than or equal to rain_24h_mm")
        if np.any(values[:, 3] < values[:, 2]):
            raise PredictionInputError("forecast_rain_12h_mm must be greater than or equal to forecast_rain_6h_mm")
        return values

    def predict(self, features: Mapping[str, float]) -> float:
        supplied = set(features)
        expected = set(FEATURE_COLUMNS_V1)
        missing, unexpected = sorted(expected - supplied), sorted(supplied - expected)
        if missing or unexpected:
            parts = []
            if missing:
                parts.append(f"missing features: {', '.join(missing)}")
            if unexpected:
                parts.append(f"unexpected features: {', '.join(unexpected)}")
            raise PredictionInputError("; ".join(parts))
        values = self._validate_feature_frame(pd.DataFrame([features]))
        return float(self._model.predict_proba(values)[0, 1])

    def predict_many(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            raise PredictionInputError("batch cannot be empty")
        values = self._validate_feature_frame(frame)
        output = frame.copy()
        output["risk_score"] = self._model.predict_proba(values)[:, 1].astype(float)
        output["risk_level"] = output["risk_score"].map(risk_level)
        return output

    @property
    def feature_importances(self) -> np.ndarray:
        return self._model.feature_importances_.copy()
