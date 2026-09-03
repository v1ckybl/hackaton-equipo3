"""Carga verificada del artefacto XGBoost exportado por Colab."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ultima_ventana_ml import RiskPredictor, risk_level

DISCLAIMER = (
    "Demo experimental con rutas, features y pronóstico simulados. "
    "No representa transitabilidad real ni una recomendación operativa."
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class ModelService:
    predictor: RiskPredictor
    metadata: dict[str, Any]
    artifact_dir: Path

    @classmethod
    def load(cls) -> "ModelService":
        repository_root = Path(__file__).resolve().parents[2]
        default_dir = repository_root / "artifacts" / "models" / "synthetic-v1"
        artifact_dir = Path(os.environ.get("MODEL_ARTIFACT_DIR", default_dir)).resolve()
        model_path = artifact_dir / "model.json"
        schema_path = artifact_dir / "feature_schema.json"
        metadata_path = artifact_dir / "metadata.json"
        for required in (model_path, schema_path, metadata_path):
            if not required.is_file():
                raise RuntimeError(f"Falta el artefacto requerido: {required}")

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected_hashes = {
            model_path: metadata.get("model_sha256"),
            schema_path: metadata.get("feature_schema_sha256"),
        }
        for path, expected in expected_hashes.items():
            if not expected or _sha256(path) != expected:
                raise RuntimeError(f"Checksum inválido para {path.name}")
        return cls(RiskPredictor.load(model_path, schema_path), metadata, artifact_dir)

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        score = self.predictor.predict(features)
        return {
            "risk_score": score,
            "risk_level": risk_level(score),
            "model_version": self.metadata["model_version"],
            "disclaimer": DISCLAIMER,
        }
